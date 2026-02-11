<template>
  <div class="app-container">
    <!-- 顶部标题栏 -->
    <el-header class="header">
      <h1>🌸 牵牛花订单数据下钻分析系统</h1>
      <div class="header-actions">
        <el-button type="success" @click="exportData" :disabled="!dataLoaded">
          <el-icon><Download /></el-icon> 导出数据
        </el-button>
      </div>
    </el-header>

    <el-main>
      <!-- 上传区域 -->
      <el-card v-if="!dataLoaded" class="upload-card">
        <template #header>
          <span>📁 上传数据文件</span>
        </template>
        <el-form label-width="100px">
          <el-form-item label="上周期数据">
            <el-upload
              ref="lastUpload"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls,.csv"
              :on-change="(file) => handleFileChange(file, 'last')"
            >
              <el-button type="primary">选择文件</el-button>
              <template #tip>
                <div class="el-upload__tip">支持 Excel (.xlsx, .xls) 或 CSV 文件</div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="本周期数据">
            <el-upload
              ref="currentUpload"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls,.csv"
              :on-change="(file) => handleFileChange(file, 'current')"
            >
              <el-button type="primary">选择文件</el-button>
            </el-upload>
          </el-form-item>
          <el-form-item>
            <el-button type="success" @click="uploadFiles" :loading="uploading" size="large">
              <el-icon><Upload /></el-icon> 开始分析
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 数据分析区域 -->
      <template v-else>
        <!-- 筛选器 -->
        <el-card class="filter-card">
          <el-row :gutter="20" align="middle">
            <el-col :span="6">
              <span class="filter-label">门店筛选：</span>
              <el-select v-model="selectedStore" @change="loadCategories" style="width: 200px">
                <el-option v-for="store in stores" :key="store" :label="store" :value="store" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <span class="filter-label">当前分类：</span>
              <el-tag v-if="selectedCategory" type="primary" size="large">{{ selectedCategory }}</el-tag>
              <el-tag v-else type="info" size="large">全部分类</el-tag>
            </el-col>
            <el-col :span="6">
              <el-button v-if="selectedCategory" @click="backToCategories" type="warning">
                <el-icon><Back /></el-icon> 返回分类列表
              </el-button>
            </el-col>
            <el-col :span="6" style="text-align: right">
              <el-button @click="resetData" type="danger">
                <el-icon><RefreshRight /></el-icon> 重新上传
              </el-button>
            </el-col>
          </el-row>
        </el-card>

        <el-row :gutter="20">
          <!-- 左侧：数据表格 -->
          <el-col :span="14">
            <!-- 分类汇总视图 -->
            <el-card v-if="!selectedCategory" class="data-card">
              <template #header>
                <span>📊 分类销售汇总 (点击分类查看商品明细)</span>
              </template>
              <el-table 
                :data="categories" 
                stripe 
                @row-click="drillDown"
                style="cursor: pointer"
                max-height="600"
              >
                <el-table-column prop="category" label="分类" min-width="200" />
                <el-table-column prop="current_qty" label="本周期销量" width="120" align="right">
                  <template #default="{ row }">{{ formatNumber(row.current_qty) }}</template>
                </el-table-column>
                <el-table-column prop="last_qty" label="上周期销量" width="120" align="right">
                  <template #default="{ row }">{{ formatNumber(row.last_qty) }}</template>
                </el-table-column>
                <el-table-column label="销量变化" width="150" align="right">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.qty_change)">
                      {{ formatChange(row.qty_change) }} ({{ formatPercent(row.qty_change_pct) }})
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="current_amount" label="本周期金额" width="120" align="right">
                  <template #default="{ row }">¥{{ formatNumber(row.current_amount) }}</template>
                </el-table-column>
                <el-table-column label="金额变化" width="150" align="right">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.amount_change)">
                      {{ formatChange(row.amount_change) }} ({{ formatPercent(row.amount_change_pct) }})
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>

            <!-- 商品明细视图 -->
            <el-card v-else class="data-card">
              <template #header>
                <span>📦 商品明细 - {{ selectedCategory }}</span>
              </template>
              <el-table :data="products" stripe max-height="600">
                <el-table-column prop="product_name" label="商品名称" min-width="200" show-overflow-tooltip />
                <el-table-column prop="spec" label="规格" width="100" />
                <el-table-column prop="sku" label="SKU" width="180" show-overflow-tooltip />
                <el-table-column prop="last_qty" label="上周期销量" width="100" align="right">
                  <template #default="{ row }">{{ formatNumber(row.last_qty) }}</template>
                </el-table-column>
                <el-table-column prop="current_qty" label="本周期销量" width="100" align="right">
                  <template #default="{ row }">{{ formatNumber(row.current_qty) }}</template>
                </el-table-column>
                <el-table-column label="销量变化" width="100" align="right">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.qty_change)">{{ formatChange(row.qty_change) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="变化率" width="100" align="right">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.qty_change_pct)">{{ formatPercent(row.qty_change_pct) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>

          <!-- 右侧：图表 -->
          <el-col :span="10">
            <el-card class="chart-card">
              <template #header>
                <span>📉 销量下跌 TOP 200 商品</span>
              </template>
              <div ref="chartRef" style="height: 600px"></div>
            </el-card>
          </el-col>
        </el-row>
      </template>
    </el-main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

// API 基础路径：生产环境由 nginx 代理，开发环境由 vite proxy 处理
axios.defaults.baseURL = import.meta.env.BASE_URL || '/qnh-drill/'

// 状态
const dataLoaded = ref(false)
const uploading = ref(false)
const stores = ref([])
const selectedStore = ref('全部')
const categories = ref([])
const products = ref([])
const selectedCategory = ref(null)
const topDecline = ref([])

// 文件
const lastFile = ref(null)
const currentFile = ref(null)

// 图表
const chartRef = ref(null)
let chartInstance = null

// 文件选择
const handleFileChange = (file, type) => {
  if (type === 'last') {
    lastFile.value = file.raw
  } else {
    currentFile.value = file.raw
  }
}

// 上传文件
const uploadFiles = async () => {
  if (!lastFile.value || !currentFile.value) {
    ElMessage.warning('请选择两个周期的数据文件')
    return
  }

  uploading.value = true
  const formData = new FormData()
  formData.append('last_file', lastFile.value)
  formData.append('current_file', currentFile.value)

  try {
    const res = await axios.post('/api/upload', formData)
    if (res.data.success) {
      ElMessage.success('数据上传成功！')
      stores.value = ['全部', ...res.data.stats.stores]
      dataLoaded.value = true
      await loadCategories()
      await loadTopDecline()
    }
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

// 加载分类数据
const loadCategories = async () => {
  try {
    const res = await axios.get('/api/categories', {
      params: { store: selectedStore.value }
    })
    categories.value = res.data.categories
    selectedCategory.value = null
    await loadTopDecline()
  } catch (error) {
    ElMessage.error('加载分类数据失败')
  }
}

// 下钻到商品
const drillDown = async (row) => {
  selectedCategory.value = row.category
  try {
    const res = await axios.get('/api/products', {
      params: { 
        category: row.category,
        store: selectedStore.value 
      }
    })
    products.value = res.data.products
    await loadTopDecline()
  } catch (error) {
    ElMessage.error('加载商品数据失败')
  }
}

// 返回分类列表
const backToCategories = () => {
  selectedCategory.value = null
  products.value = []
  loadTopDecline()
}

// 加载下跌 TOP 200
const loadTopDecline = async () => {
  try {
    const res = await axios.get('/api/top-decline', {
      params: {
        store: selectedStore.value,
        category: selectedCategory.value,
        limit: 200
      }
    })
    topDecline.value = res.data.products
    await nextTick()
    renderChart()
  } catch (error) {
    console.error('加载下跌数据失败', error)
  }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, 'dark')
  }

  const data = topDecline.value.slice(0, 50)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(20, 20, 35, 0.95)',
      borderColor: 'rgba(100, 100, 255, 0.2)',
      textStyle: { color: '#e0e0f0' },
      formatter: (params) => {
        const item = params[0]
        const product = data[item.dataIndex]
        return `
          <strong style="color:#fff">${product.product_name}</strong><br/>
          <span style="color:#a0a0b0">规格: ${product.spec}</span><br/>
          上周期: ${product.last_qty}<br/>
          本周期: ${product.current_qty}<br/>
          变化: <span style="color: #4ade80">${product.qty_change}</span>
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map((_, i) => i + 1),
      axisLabel: { interval: 4, rotate: 0, color: '#a0a0b0' },
      axisLine: { lineStyle: { color: 'rgba(100,100,255,0.2)' } },
      name: '排名',
      nameTextStyle: { color: '#a0a0b0' }
    },
    yAxis: {
      type: 'value',
      name: '销量变化',
      nameTextStyle: { color: '#a0a0b0' },
      axisLabel: { formatter: (val) => val, color: '#a0a0b0' },
      axisLine: { lineStyle: { color: 'rgba(100,100,255,0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(100,100,255,0.08)' } }
    },
    series: [{
      name: '销量变化',
      type: 'bar',
      data: data.map(item => ({
        value: item.qty_change,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(74, 222, 128, 0.8)' },
            { offset: 1, color: 'rgba(74, 222, 128, 0.3)' }
          ]),
          borderRadius: [4, 4, 0, 0]
        }
      })),
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(100, 100, 255, 0.9)' },
            { offset: 1, color: 'rgba(100, 100, 255, 0.4)' }
          ])
        }
      }
    }],
    dataZoom: [{
      type: 'slider',
      show: true,
      start: 0,
      end: 100,
      bottom: 0,
      backgroundColor: 'rgba(100,100,255,0.05)',
      borderColor: 'rgba(100,100,255,0.1)',
      fillerColor: 'rgba(100,100,255,0.15)',
      handleStyle: { color: '#6464ff' },
      textStyle: { color: '#a0a0b0' }
    }]
  }

  chartInstance.setOption(option)
}

// 导出数据
const exportData = async () => {
  try {
    const res = await axios.get('/api/export', {
      params: { store: selectedStore.value },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '订单数据对比分析.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    ElMessage.success('导出成功！')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 重置数据
const resetData = () => {
  dataLoaded.value = false
  stores.value = []
  categories.value = []
  products.value = []
  selectedCategory.value = null
  selectedStore.value = '全部'
  lastFile.value = null
  currentFile.value = null
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

// 格式化函数
const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return Number(num).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

const formatChange = (num) => {
  if (num === null || num === undefined) return '0'
  const prefix = num > 0 ? '↑' : num < 0 ? '↓' : ''
  return prefix + Math.abs(num).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

const formatPercent = (num) => {
  if (num === null || num === undefined) return '0%'
  const prefix = num > 0 ? '↑' : num < 0 ? '↓' : ''
  return prefix + Math.abs(num).toFixed(1) + '%'
}

const getChangeClass = (num) => {
  if (num > 0) return 'change-up'
  if (num < 0) return 'change-down'
  return ''
}

// 监听窗口大小变化
onMounted(() => {
  window.addEventListener('resize', () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
})
</script>

<style>
/* ===== 布局 ===== */
.app-container {
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
  min-height: 100vh;
}

.header {
  background: rgba(20, 20, 35, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(100, 100, 255, 0.15);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  height: 70px;
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(135deg, #fff 0%, #a0a0c0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.el-main { padding: 20px; }

.upload-card { max-width: 600px; margin: 100px auto; }
.filter-card { margin-bottom: 20px; }
.filter-label { font-weight: 500; margin-right: 10px; color: #a0a0b0; }
.data-card, .chart-card { height: calc(100vh - 220px); }

/* ===== Element Plus 深色覆盖 ===== */
.el-card {
  background: rgba(26, 26, 45, 0.85) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(100, 100, 255, 0.15) !important;
  border-radius: 16px !important;
}

.el-card__header {
  background: rgba(100, 100, 255, 0.1) !important;
  border-bottom: 1px solid rgba(100, 100, 255, 0.15) !important;
  color: #e0e0f0 !important;
}

.el-card__body { color: #c0c0d0; }

.el-button--primary {
  background: linear-gradient(135deg, #6464ff, #8b5cf6) !important;
  border: none !important;
}

.el-button--success {
  background: linear-gradient(135deg, #22c55e, #16a34a) !important;
  border: none !important;
}

.el-button--warning {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  border: none !important;
  color: #fff !important;
}

.el-button--danger {
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
  border: none !important;
}

/* 表格 */
.el-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(100, 100, 255, 0.1);
  --el-table-row-hover-bg-color: rgba(100, 100, 255, 0.1);
  --el-table-border-color: rgba(100, 100, 255, 0.1);
  --el-table-text-color: #c0c0d0;
  --el-table-header-text-color: #e0e0f0;
  font-size: 13px;
}

.el-table th.el-table__cell {
  background: rgba(100, 100, 255, 0.1) !important;
}

.el-table .el-table__row { cursor: pointer; }
.el-table .el-table__row:hover { background-color: rgba(100, 100, 255, 0.15) !important; }

/* 条纹行深色 */
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: rgba(100, 100, 255, 0.04) !important;
}

/* 选择器 */
.el-select .el-input__wrapper {
  background: rgba(30, 30, 50, 0.8) !important;
  border: 1px solid rgba(100, 100, 255, 0.2) !important;
  box-shadow: none !important;
}
.el-select .el-input__inner { color: #e0e0f0 !important; }

/* 下拉菜单 */
.el-select-dropdown {
  background: rgba(26, 26, 45, 0.95) !important;
  border: 1px solid rgba(100, 100, 255, 0.2) !important;
}
.el-select-dropdown__item { color: #c0c0d0 !important; }
.el-select-dropdown__item.hover, .el-select-dropdown__item:hover {
  background: rgba(100, 100, 255, 0.15) !important;
}
.el-select-dropdown__item.selected { color: #8b8bff !important; }

/* 标签 */
.el-tag {
  background: rgba(100, 100, 255, 0.15) !important;
  border: 1px solid rgba(100, 100, 255, 0.3) !important;
  color: #a0a0ff !important;
}
.el-tag--info {
  background: rgba(160, 160, 176, 0.15) !important;
  border-color: rgba(160, 160, 176, 0.3) !important;
  color: #a0a0b0 !important;
}

/* 表单 */
.el-form-item__label { color: #a0a0b0 !important; }

/* 上传提示 */
.el-upload__tip { color: #6a6a7a !important; }

/* ===== 数据变化色 ===== */
.change-up { color: #ff6b6b !important; font-weight: 600; }
.change-down { color: #4ade80 !important; font-weight: 600; }

/* ===== 滚动条 ===== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: rgba(100, 100, 255, 0.05); }
::-webkit-scrollbar-thumb { background: rgba(100, 100, 255, 0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(100, 100, 255, 0.3); }
</style>
