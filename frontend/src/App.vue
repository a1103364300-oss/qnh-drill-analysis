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

// 设置 API 基础路径
const API_BASE = import.meta.env.BASE_URL || '/qnh-drill/'
axios.defaults.baseURL = API_BASE

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
    chartInstance = echarts.init(chartRef.value)
  }

  const data = topDecline.value.slice(0, 50) // 显示前50个

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = params[0]
        const product = data[item.dataIndex]
        return `
          <strong>${product.product_name}</strong><br/>
          规格: ${product.spec}<br/>
          上周期: ${product.last_qty}<br/>
          本周期: ${product.current_qty}<br/>
          变化: <span style="color: #67C23A">${product.qty_change}</span>
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
      axisLabel: {
        interval: 4,
        rotate: 0
      },
      name: '排名'
    },
    yAxis: {
      type: 'value',
      name: '销量变化',
      axisLabel: {
        formatter: (val) => val
      }
    },
    series: [{
      name: '销量变化',
      type: 'bar',
      data: data.map(item => ({
        value: item.qty_change,
        itemStyle: {
          color: '#67C23A' // 绿色表示下跌
        }
      })),
      emphasis: {
        itemStyle: {
          color: '#409EFF'
        }
      }
    }],
    dataZoom: [{
      type: 'slider',
      show: true,
      start: 0,
      end: 100,
      bottom: 0
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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
}

.el-main {
  padding: 20px;
}

.upload-card {
  max-width: 600px;
  margin: 100px auto;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-label {
  font-weight: 500;
  margin-right: 10px;
}

.data-card, .chart-card {
  height: calc(100vh - 220px);
}

.change-up {
  color: #F56C6C;
  font-weight: 600;
}

.change-down {
  color: #67C23A;
  font-weight: 600;
}

.el-table {
  font-size: 13px;
}

.el-table .el-table__row {
  cursor: pointer;
}

.el-table .el-table__row:hover {
  background-color: #ecf5ff !important;
}
</style>
