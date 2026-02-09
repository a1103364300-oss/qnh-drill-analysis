# 🌸 牵牛花订单数据下钻分析系统

对比分析同一门店两个周期的商品订单数据，通过交互式界面直观展示销售变化。

## 功能特性

- 📁 **数据上传**: 支持 Excel (.xlsx, .xls) 和 CSV 文件
- 📊 **分类汇总**: 按分类展示销售总额对比
- 📦 **商品下钻**: 点击分类查看商品明细
- 📉 **下跌分析**: 销量下跌 TOP 200 商品图表
- 📤 **数据导出**: 导出带对比数据的 Excel 文件
- 🏪 **门店筛选**: 支持多门店数据筛选

## 技术栈

- **前端**: Vue 3 + Element Plus + ECharts
- **后端**: Python FastAPI + Pandas
- **部署**: Docker Compose

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 构建并启动
docker compose up -d --build

# 访问
http://localhost:8080
```

### 方式二：本地开发

#### 后端

```bash
cd backend
pip install -r requirements.txt
python main.py
# 后端运行在 http://localhost:8000
```

#### 前端

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:3000
```

## 数据格式要求

上传的 Excel 文件需包含以下列：

| 列名 | 说明 |
|------|------|
| 门店编码 | 门店唯一标识 |
| 门店名称 | 门店名称 |
| 店内分类 | 商品分类 |
| 商品名称 | 商品名称 |
| 商品SKU | 商品唯一标识 |
| 规格 | 商品规格 |
| 数量 | 销售数量 |
| 商品售价 | 单价 |
| 商品金额 | 销售金额 |

## 使用说明

1. **上传数据**: 分别选择"上周期"和"本周期"的数据文件，点击"开始分析"
2. **查看分类**: 系统自动按分类汇总，显示销量和金额变化
3. **下钻商品**: 点击任一分类行，查看该分类下的商品明细
4. **筛选门店**: 使用顶部下拉框筛选特定门店
5. **查看图表**: 右侧图表显示销量下跌最多的商品
6. **导出数据**: 点击"导出数据"下载带对比分析的 Excel 文件

## 颜色说明

- 🔴 **红色**: 数值上涨
- 🟢 **绿色**: 数值下跌

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传数据文件 |
| `/api/stores` | GET | 获取门店列表 |
| `/api/categories` | GET | 获取分类汇总 |
| `/api/products` | GET | 获取商品明细 |
| `/api/top-decline` | GET | 获取下跌 TOP N |
| `/api/export` | GET | 导出 Excel |
| `/api/health` | GET | 健康检查 |

## 目录结构

```
qnh-drill-down/
├── backend/
│   ├── main.py           # FastAPI 应用
│   ├── requirements.txt  # Python 依赖
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.vue       # 主组件
│   │   └── main.js       # 入口文件
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 许可证

MIT License
