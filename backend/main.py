"""
牵牛花订单数据下钻分析系统 - 后端 API
FastAPI + Pandas
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import json
from typing import Optional

app = FastAPI(title="牵牛花订单数据下钻分析系统", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局数据存储
data_store = {
    "current_period": None,  # 本周期
    "last_period": None,     # 上周期
    "merged": None,          # 合并后的数据
}


def read_excel_file(file: UploadFile) -> pd.DataFrame:
    """读取上传的 Excel/CSV 文件"""
    content = file.file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_excel(io.BytesIO(content))
    return df


def process_data():
    """处理并合并两个周期的数据"""
    df_current = data_store["current_period"]
    df_last = data_store["last_period"]
    
    if df_current is None or df_last is None:
        return None
    
    # 标准化列名
    col_mapping = {
        '商品SKU': 'sku',
        '商品名称': 'product_name',
        '规格': 'spec',
        '店内分类': 'category',
        '门店名称': 'store',
        '门店编码': 'store_code',
        '数量': 'quantity',
        '商品金额': 'amount',
        '商品售价': 'price',
        '商家整单优惠': 'merchant_discount',
        '平台整单优惠': 'platform_discount',
    }
    
    df_current = df_current.rename(columns=col_mapping)
    df_last = df_last.rename(columns=col_mapping)
    
    # 按 SKU + 门店 + 分类 聚合
    group_cols = ['sku', 'product_name', 'spec', 'category', 'store']
    
    current_agg = df_current.groupby(group_cols, as_index=False).agg({
        'quantity': 'sum',
        'amount': 'sum'
    }).rename(columns={'quantity': 'current_qty', 'amount': 'current_amount'})
    
    last_agg = df_last.groupby(group_cols, as_index=False).agg({
        'quantity': 'sum',
        'amount': 'sum'
    }).rename(columns={'quantity': 'last_qty', 'amount': 'last_amount'})
    
    # 合并数据
    merged = pd.merge(current_agg, last_agg, on=group_cols, how='outer')
    merged = merged.fillna(0)
    
    # 计算变化
    merged['qty_change'] = merged['current_qty'] - merged['last_qty']
    merged['qty_change_pct'] = merged.apply(
        lambda x: (x['qty_change'] / x['last_qty'] * 100) if x['last_qty'] != 0 else (100 if x['current_qty'] > 0 else 0),
        axis=1
    )
    merged['amount_change'] = merged['current_amount'] - merged['last_amount']
    merged['amount_change_pct'] = merged.apply(
        lambda x: (x['amount_change'] / x['last_amount'] * 100) if x['last_amount'] != 0 else (100 if x['current_amount'] > 0 else 0),
        axis=1
    )
    
    data_store["merged"] = merged
    return merged


@app.post("/api/upload")
async def upload_files(
    current_file: UploadFile = File(..., description="本周期数据"),
    last_file: UploadFile = File(..., description="上周期数据")
):
    """上传两个周期的数据文件"""
    try:
        data_store["current_period"] = read_excel_file(current_file)
        current_file.file.seek(0)
        
        data_store["last_period"] = read_excel_file(last_file)
        last_file.file.seek(0)
        
        merged = process_data()
        
        if merged is None:
            raise HTTPException(status_code=400, detail="数据处理失败")
        
        # 获取门店列表
        stores = merged['store'].unique().tolist()
        
        return {
            "success": True,
            "message": "数据上传成功",
            "stats": {
                "current_records": len(data_store["current_period"]),
                "last_records": len(data_store["last_period"]),
                "merged_records": len(merged),
                "stores": stores,
                "categories": merged['category'].nunique(),
                "skus": merged['sku'].nunique()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stores")
async def get_stores():
    """获取门店列表"""
    if data_store["merged"] is None:
        return {"stores": []}
    stores = data_store["merged"]['store'].unique().tolist()
    return {"stores": ["全部"] + stores}


@app.get("/api/categories")
async def get_categories(store: Optional[str] = None):
    """获取分类汇总数据"""
    if data_store["merged"] is None:
        raise HTTPException(status_code=400, detail="请先上传数据")
    
    df = data_store["merged"].copy()
    
    # 按门店筛选
    if store and store != "全部":
        df = df[df['store'] == store]
    
    # 按分类聚合
    cat_summary = df.groupby('category', as_index=False).agg({
        'current_qty': 'sum',
        'last_qty': 'sum',
        'current_amount': 'sum',
        'last_amount': 'sum'
    })
    
    # 计算变化
    cat_summary['qty_change'] = cat_summary['current_qty'] - cat_summary['last_qty']
    cat_summary['qty_change_pct'] = cat_summary.apply(
        lambda x: (x['qty_change'] / x['last_qty'] * 100) if x['last_qty'] != 0 else 0,
        axis=1
    )
    cat_summary['amount_change'] = cat_summary['current_amount'] - cat_summary['last_amount']
    cat_summary['amount_change_pct'] = cat_summary.apply(
        lambda x: (x['amount_change'] / x['last_amount'] * 100) if x['last_amount'] != 0 else 0,
        axis=1
    )
    
    # 排序：按销量变化从小到大（下跌最多的在前）
    cat_summary = cat_summary.sort_values('qty_change', ascending=True)
    
    return {
        "categories": cat_summary.to_dict(orient='records'),
        "total": {
            "current_qty": df['current_qty'].sum(),
            "last_qty": df['last_qty'].sum(),
            "current_amount": df['current_amount'].sum(),
            "last_amount": df['last_amount'].sum()
        }
    }


@app.get("/api/products")
async def get_products(category: str, store: Optional[str] = None):
    """获取分类下的商品明细"""
    if data_store["merged"] is None:
        raise HTTPException(status_code=400, detail="请先上传数据")
    
    df = data_store["merged"].copy()
    
    # 筛选
    if store and store != "全部":
        df = df[df['store'] == store]
    df = df[df['category'] == category]
    
    # 排序：按销量变化从小到大
    df = df.sort_values('qty_change', ascending=True)
    
    return {
        "products": df.to_dict(orient='records'),
        "count": len(df)
    }


@app.get("/api/top-decline")
async def get_top_decline(
    store: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 200
):
    """获取销量下跌 TOP N 商品"""
    if data_store["merged"] is None:
        raise HTTPException(status_code=400, detail="请先上传数据")
    
    df = data_store["merged"].copy()
    
    # 筛选
    if store and store != "全部":
        df = df[df['store'] == store]
    if category and category != "全部":
        df = df[df['category'] == category]
    
    # 只取下跌的商品
    df = df[df['qty_change'] < 0]
    
    # 排序并取 TOP N
    df = df.sort_values('qty_change', ascending=True).head(limit)
    
    return {
        "products": df.to_dict(orient='records'),
        "count": len(df)
    }


@app.get("/api/export")
async def export_data(store: Optional[str] = None):
    """导出数据为 Excel"""
    if data_store["merged"] is None:
        raise HTTPException(status_code=400, detail="请先上传数据")
    
    df = data_store["merged"].copy()
    
    if store and store != "全部":
        df = df[df['store'] == store]
    
    # 重命名列为中文
    export_df = df.rename(columns={
        'sku': '商品SKU',
        'product_name': '商品名称',
        'spec': '规格',
        'category': '分类',
        'store': '门店',
        'current_qty': '本周期销量',
        'last_qty': '上周期销量',
        'qty_change': '销量变化值',
        'qty_change_pct': '销量变化百分比',
        'current_amount': '本周期金额',
        'last_amount': '上周期金额',
        'amount_change': '金额变化值',
        'amount_change_pct': '金额变化百分比'
    })
    
    # 导出到 Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='数据对比')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=order_analysis_export.xlsx"}
    )


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "data_loaded": data_store["merged"] is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
