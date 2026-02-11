<template>
  <div class="app-container">
    <el-header class="header">
      <h1>🌸 牵牛花订单数据下钻分析系统</h1>
      <div class="header-actions">
        <el-button type="success" @click="exportData" :disabled="!dataLoaded">
          <el-icon><Download /></el-icon> 导出数据
        </el-button>
      </div>
    </el-header>

    <el-main>
      <el-card v-if="!dataLoaded" class="upload-card">
        <template #header><span>📁 上传数据文件</span></template>
        <el-form label-width="100px">
          <el-form-item label="上周期数据">
            <el-upload ref="lastUpload" :auto-upload="false" :limit="1" accept=".xlsx,.xls,.csv"
              :on-change="(file) => handleFileChange(file, 'last')">
              <el-button type="primary">选择文件</el-button>
              <template #tip><div class="el-upload__tip">支持 Excel (.xlsx, .xls) 或 CSV 文件</div></template>
            </el-upload>
          </el-form-item>
          <el-form-item label="本周期数据">
            <el-upload ref="currentUpload" :auto-upload="false" :limit="1" accept=".xlsx,.xls,.csv"
              :on-change="(file) => handleFileChange(file, 'current')">
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

      <template v-else>
        <el-card class="filter-card">
          <el-row :gutter="20" align="middle">
            <el-col :span="5">
              <span class="filter-label">门店：</span>
              <el-select v-model="selectedStore" @change="onStoreChange" style="width: 180px">
                <el-option v-for="s in stores" :key="s" :label="s" :value="s" />
              </el-select>
            </el-col>
            <el-col :span="11">
              <span class="filter-label">层级：</span>
              <el-breadcrumb separator="/">
                <el-breadcrumb-item>
                  <a href="#" @click.prevent="goToLevel(0)" :class="{ 'bc-active': drillLevel === 0 }">一级分类</a>
                </el-breadcrumb-item>
                <el-breadcrumb-item v-if="drillLevel >= 1">
                  <a href="#" @click.prevent="goToLevel(1)" :class="{ 'bc-active': drillLevel === 1 }">{{ selectedCat1 }}</a>
                </el-breadcrumb-item>
                <el-breadcrumb-item v-if="drillLevel >= 2">
                  <span class="bc-active">{{ selectedCat2 }}</span>
                </el-breadcrumb-item>
              </el-breadcrumb>
            </el-col>
            <el-col :span="5">
              <el-input v-model="searchKeyword" placeholder="搜索名称..." clearable style="width: 200px">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-col>
            <el-col :span="3" style="text-align: right">
              <el-button @click="resetData" type="danger" size="small">
                <el-icon><RefreshRight /></el-icon> 重新上传
              </el-button>
            </el-col>
          </el-row>
        </el-card>

        <el-row :gutter="20">
          <el-col :span="14">
            <!-- Level 0: 一级分类 -->
            <el-card v-if="drillLevel === 0" class="data-card">
              <template #header><span>📊 一级分类汇总 (点击下钻)</span></template>
              <el-table :data="filteredCat1" stripe @row-click="drillToCat2" style="cursor:pointer"
                max-height="600" :default-sort="{ prop: 'qty_change', order: 'ascending' }">
                <el-table-column prop="category1" label="一级分类" min-width="180" sortable />
                <el-table-column prop="current_qty" label="本期销量" width="110" align="right" sortable :sort-method="(a,b) => a.current_qty - b.current_qty">
                  <template #default="{ row }">{{ formatNumber(row.current_qty) }}</template>
                </el-table-column>
                <el-table-column prop="last_qty" label="上期销量" width="110" align="right" sortable :sort-method="(a,b) => a.last_qty - b.last_qty">
                  <template #default="{ row }">{{ formatNumber(row.last_qty) }}</template>
                </el-table-column>
                <el-table-column prop="qty_change" label="销量变化" width="140" align="right" sortable :sort-method="(a,b) => a.qty_change - b.qty_change">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.qty_change)">{{ formatChange(row.qty_change) }} ({{ formatPercent(row.qty_change_pct) }})</span>
                  </template>
                </el-table-column>
                <el-table-column prop="current_amount" label="本期金额" width="110" align="right" sortable :sort-method="(a,b) => a.current_amount - b.current_amount">
                  <template #default="{ row }">¥{{ formatNumber(row.current_amount) }}</template>
                </el-table-column>
                <el-table-column prop="amount_change" label="金额变化" width="140" align="right" sortable :sort-method="(a,b) => a.amount_change - b.amount_change">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.amount_change)">{{ formatChange(row.amount_change) }} ({{ formatPercent(row.amount_change_pct) }})</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>

            <!-- Level 1: 二级分类 -->
            <el-card v-else-if="drillLevel === 1" class="data-card">
              <template #header><span>📊 {{ selectedCat1 }} - 二级分类 (点击下钻)</span></template>
              <el-table :data="filteredCat2" stripe @row-click="drillToProducts" style="cursor:pointer"
                max-height="600" :default-sort="{ prop: 'qty_change', order: 'ascending' }">
                <el-table-column prop="category" label="二级分类" min-width="200" sortable />
                <el-table-column prop="current_qty" label="本期销量" width="110" align="right" sortable :sort-method="(a,b) => a.current_qty - b.current_qty">
                  <template #default="{ row }">{{ formatNumber(row.current_qty) }}</template>
                </el-table-column>
                <el-table-column prop="last_qty" label="上期销量" width="110" align="right" sortable :sort-method="(a,b) => a.last_qty - b.last_qty">
                  <template #default="{ row }">{{ formatNumber(row.last_qty) }}</template>
                </el-table-column>
                <el-table-column prop="qty_change" label="销量变化" width="140" align="right" sortable :sort-method="(a,b) => a.qty_change - b.qty_change">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.qty_change)">{{ formatChange(row.qty_change) }} ({{ formatPercent(row.qty_change_pct) }})</span>
                  </template>
                </el-table-column>
                <el-table-column prop="current_amount" label="本期金额" width="110" align="right" sortable :sort-method="(a,b) => a.current_amount - b.current_amount">
                  <template #default="{ row }">¥{{ formatNumber(row.current_amount) }}</template>
                </el-table-column>
                <el-table-column prop="amount_change" label="金额变化" width="140" align="right" sortable :sort-method="(a,b) => a.amount_change - b.amount_change">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.amount_change)">{{ formatChange(row.amount_change) }} ({{ formatPercent(row.amount_change_pct) }})</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>

            <!-- Level 2: 商品明细 -->
            <el-card v-else class="data-card">
              <template #header><span>📦 {{ selectedCat2 }} - 商品明细</span></template>
              <el-table :data="filteredProducts" stripe max-height="600"
                :default-sort="{ prop: 'qty_change', order: 'ascending' }">
                <el-table-column prop="product_name" label="商品名称" min-width="200" show-overflow-tooltip sortable />
                <el-table-column prop="spec" label="规格" width="100" sortable />
                <el-table-column prop="sku" label="SKU" width="160" show-overflow-tooltip sortable />
                <el-table-column prop="last_qty" label="上期销量" width="100" align="right" sortable :sort-method="(a,b) => a.last_qty - b.last_qty">
                  <template #default="{ row }">{{ formatNumber(row.last_qty) }}</template>
                </el-table-column>
                <el-table-column prop="current_qty" label="本期销量" width="100" align="right" sortable :sort-method="(a,b) => a.current_qty - b.current_qty">
                  <template #default="{ row }">{{ formatNumber(row.current_qty) }}</template>
                </el-table-column>
                <el-table-column prop="qty_change" label="销量变化" width="100" align="right" sortable :sort-method="(a,b) => a.qty_change - b.qty_change">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.qty_change)">{{ formatChange(row.qty_change) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="qty_change_pct" label="变化率" width="100" align="right" sortable :sort-method="(a,b) => a.qty_change_pct - b.qty_change_pct">
                  <template #default="{ row }">
                    <span :class="getChangeClass(row.qty_change_pct)">{{ formatPercent(row.qty_change_pct) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>

          <el-col :span="10">
            <el-card class="chart-card">
              <template #header><span>📉 销量下跌 TOP 50</span></template>
              <div ref="chartRef" style="height: 600px"></div>
            </el-card>
          </el-col>
        </el-row>
      </template>
    </el-main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

axios.defaults.baseURL = import.meta.env.BASE_URL || '/qnh-drill/'

const dataLoaded = ref(false)
const uploading = ref(false)
const stores = ref([])
const selectedStore = ref('全部')
const searchKeyword = ref('')

const drillLevel = ref(0)
const selectedCat1 = ref(null)
const selectedCat2 = ref(null)

const categories1 = ref([])
const categories2 = ref([])
const products = ref([])
const topDecline = ref([])

const lastFile = ref(null)
const currentFile = ref(null)
const chartRef = ref(null)
let chartInstance = null

const filteredCat1 = computed(() => {
  if (!searchKeyword.value) return categories1.value
  const kw = searchKeyword.value.toLowerCase()
  return categories1.value.filter(r => r.category1.toLowerCase().includes(kw))
})
const filteredCat2 = computed(() => {
  if (!searchKeyword.value) return categories2.value
  const kw = searchKeyword.value.toLowerCase()
  return categories2.value.filter(r => r.category.toLowerCase().includes(kw))
})
const filteredProducts = computed(() => {
  if (!searchKeyword.value) return products.value
  const kw = searchKeyword.value.toLowerCase()
  return products.value.filter(r =>
    r.product_name.toLowerCase().includes(kw) ||
    r.sku.toLowerCase().includes(kw) ||
    (r.spec && r.spec.toLowerCase().includes(kw))
  )
})

const handleFileChange = (file, type) => {
  if (type === 'last') lastFile.value = file.raw
  else currentFile.value = file.raw
}

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
      await loadCat1()
    }
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

const loadCat1 = async () => {
  try {
    const res = await axios.get('/api/categories1', { params: { store: selectedStore.value } })
    categories1.value = res.data.categories
    drillLevel.value = 0
    selectedCat1.value = null
    selectedCat2.value = null
    searchKeyword.value = ''
    await loadTopDecline()
  } catch (e) { ElMessage.error('加载一级分类失败') }
}

const drillToCat2 = async (row) => {
  selectedCat1.value = row.category1
  searchKeyword.value = ''
  try {
    const res = await axios.get('/api/categories', {
      params: { store: selectedStore.value, category1: row.category1 }
    })
    categories2.value = res.data.categories
    drillLevel.value = 1
    await loadTopDecline()
  } catch (e) { ElMessage.error('加载二级分类失败') }
}

const drillToProducts = async (row) => {
  selectedCat2.value = row.category
  searchKeyword.value = ''
  try {
    const res = await axios.get('/api/products', {
      params: { category: row.category, store: selectedStore.value }
    })
    products.value = res.data.products
    drillLevel.value = 2
    await loadTopDecline()
  } catch (e) { ElMessage.error('加载商品数据失败') }
}

const goToLevel = (level) => {
  searchKeyword.value = ''
  if (level === 0) loadCat1()
  else if (level === 1 && selectedCat1.value) drillToCat2({ category1: selectedCat1.value })
}

const onStoreChange = () => loadCat1()

const loadTopDecline = async () => {
  try {
    const params = { store: selectedStore.value, limit: 200 }
    if (drillLevel.value >= 2 && selectedCat2.value) params.category = selectedCat2.value
    const res = await axios.get('/api/top-decline', { params })
    topDecline.value = res.data.products
    await nextTick()
    renderChart()
  } catch (e) { console.error('加载下跌数据失败', e) }
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value, 'dark')
  const data = topDecline.value.slice(0, 50)
  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(20,20,35,0.95)', borderColor: 'rgba(100,100,255,0.2)',
      textStyle: { color: '#e0e0f0' },
      formatter: (params) => {
        const p = data[params[0].dataIndex]
        return `<strong style="color:#fff">${p.product_name}</strong><br/><span style="color:#a0a0b0">规格: ${p.spec}</span><br/>上期: ${p.last_qty} → 本期: ${p.current_qty}<br/>变化: <span style="color:#4ade80">${p.qty_change}</span>`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: data.map((_, i) => i + 1), axisLabel: { interval: 4, color: '#a0a0b0' }, axisLine: { lineStyle: { color: 'rgba(100,100,255,0.2)' } }, name: '排名', nameTextStyle: { color: '#a0a0b0' } },
    yAxis: { type: 'value', name: '销量变化', nameTextStyle: { color: '#a0a0b0' }, axisLabel: { color: '#a0a0b0' }, axisLine: { lineStyle: { color: 'rgba(100,100,255,0.2)' } }, splitLine: { lineStyle: { color: 'rgba(100,100,255,0.08)' } } },
    series: [{ name: '销量变化', type: 'bar',
      data: data.map(item => ({ value: item.qty_change, itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(74,222,128,0.8)'},{offset:1,color:'rgba(74,222,128,0.3)'}]), borderRadius: [4,4,0,0] } })),
      emphasis: { itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(100,100,255,0.9)'},{offset:1,color:'rgba(100,100,255,0.4)'}]) } }
    }],
    dataZoom: [{ type: 'slider', start: 0, end: 100, bottom: 0, backgroundColor: 'rgba(100,100,255,0.05)', borderColor: 'rgba(100,100,255,0.1)', fillerColor: 'rgba(100,100,255,0.15)', handleStyle: { color: '#6464ff' }, textStyle: { color: '#a0a0b0' } }]
  })
}

const exportData = async () => {
  try {
    const res = await axios.get('/api/export', { params: { store: selectedStore.value }, responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url; a.download = '订单数据对比分析.xlsx'
    document.body.appendChild(a); a.click(); a.remove()
    ElMessage.success('导出成功！')
  } catch (e) { ElMessage.error('导出失败') }
}

const resetData = () => {
  dataLoaded.value = false; stores.value = []; categories1.value = []
  categories2.value = []; products.value = []; drillLevel.value = 0
  selectedCat1.value = null; selectedCat2.value = null
  selectedStore.value = '全部'; searchKeyword.value = ''
  lastFile.value = null; currentFile.value = null
  if (chartInstance) { chartInstance.dispose(); chartInstance = null }
}

const formatNumber = (n) => n == null ? '0' : Number(n).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
const formatChange = (n) => { if (n == null) return '0'; return (n > 0 ? '↑' : n < 0 ? '↓' : '') + Math.abs(n).toLocaleString('zh-CN', { maximumFractionDigits: 0 }) }
const formatPercent = (n) => { if (n == null) return '0%'; return (n > 0 ? '↑' : n < 0 ? '↓' : '') + Math.abs(n).toFixed(1) + '%' }
const getChangeClass = (n) => n > 0 ? 'change-up' : n < 0 ? 'change-down' : ''

onMounted(() => { window.addEventListener('resize', () => chartInstance?.resize()) })
</script>

<style>
.app-container { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; }
.header { background: rgba(20,20,35,0.95); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(100,100,255,0.15); color: white; display: flex; justify-content: space-between; align-items: center; padding: 0 30px; height: 70px; }
.header h1 { font-size: 24px; font-weight: 600; background: linear-gradient(135deg, #fff 0%, #a0a0c0 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.el-main { padding: 20px; }
.upload-card { max-width: 600px; margin: 100px auto; }
.filter-card { margin-bottom: 20px; }
.filter-label { font-weight: 500; margin-right: 10px; color: #a0a0b0; }
.data-card, .chart-card { height: calc(100vh - 220px); }

.bc-active { color: #a0a0ff !important; font-weight: 600; }
.el-breadcrumb { display: inline-flex; vertical-align: middle; }
.el-breadcrumb__item .el-breadcrumb__inner a { color: #8080a0; }
.el-breadcrumb__item .el-breadcrumb__inner a:hover { color: #a0a0ff; }
.el-breadcrumb__separator { color: #6a6a7a !important; }

.el-card { background: rgba(26,26,45,0.85) !important; backdrop-filter: blur(20px); border: 1px solid rgba(100,100,255,0.15) !important; border-radius: 16px !important; }
.el-card__header { background: rgba(100,100,255,0.1) !important; border-bottom: 1px solid rgba(100,100,255,0.15) !important; color: #e0e0f0 !important; }
.el-card__body { color: #c0c0d0; }
.el-button--primary { background: linear-gradient(135deg, #6464ff, #8b5cf6) !important; border: none !important; }
.el-button--success { background: linear-gradient(135deg, #22c55e, #16a34a) !important; border: none !important; }
.el-button--warning { background: linear-gradient(135deg, #f59e0b, #d97706) !important; border: none !important; color: #fff !important; }
.el-button--danger { background: linear-gradient(135deg, #ef4444, #dc2626) !important; border: none !important; }

.el-table { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: rgba(100,100,255,0.1); --el-table-row-hover-bg-color: rgba(100,100,255,0.1); --el-table-border-color: rgba(100,100,255,0.1); --el-table-text-color: #c0c0d0; --el-table-header-text-color: #e0e0f0; font-size: 13px; }
.el-table th.el-table__cell { background: rgba(100,100,255,0.1) !important; }
.el-table .el-table__row { cursor: pointer; }
.el-table .el-table__row:hover { background-color: rgba(100,100,255,0.15) !important; }
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell { background: rgba(100,100,255,0.04) !important; }
.el-table .sort-caret.ascending { border-bottom-color: #8b8bff; }
.el-table .sort-caret.descending { border-top-color: #8b8bff; }
.el-table .ascending .sort-caret.ascending { border-bottom-color: #a0a0ff; }
.el-table .descending .sort-caret.descending { border-top-color: #a0a0ff; }

.el-select .el-input__wrapper { background: rgba(30,30,50,0.8) !important; border: 1px solid rgba(100,100,255,0.2) !important; box-shadow: none !important; }
.el-select .el-input__inner { color: #e0e0f0 !important; }
.el-input .el-input__wrapper { background: rgba(30,30,50,0.8) !important; border: 1px solid rgba(100,100,255,0.2) !important; box-shadow: none !important; }
.el-input .el-input__inner { color: #e0e0f0 !important; }
.el-input .el-input__prefix .el-icon { color: #6a6a7a; }

.el-select-dropdown { background: rgba(26,26,45,0.95) !important; border: 1px solid rgba(100,100,255,0.2) !important; }
.el-select-dropdown__item { color: #c0c0d0 !important; }
.el-select-dropdown__item.hover, .el-select-dropdown__item:hover { background: rgba(100,100,255,0.15) !important; }
.el-select-dropdown__item.selected { color: #8b8bff !important; }

.el-tag { background: rgba(100,100,255,0.15) !important; border: 1px solid rgba(100,100,255,0.3) !important; color: #a0a0ff !important; }
.el-tag--info { background: rgba(160,160,176,0.15) !important; border-color: rgba(160,160,176,0.3) !important; color: #a0a0b0 !important; }
.el-form-item__label { color: #a0a0b0 !important; }
.el-upload__tip { color: #6a6a7a !important; }

.change-up { color: #ff6b6b !important; font-weight: 600; }
.change-down { color: #4ade80 !important; font-weight: 600; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: rgba(100,100,255,0.05); }
::-webkit-scrollbar-thumb { background: rgba(100,100,255,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(100,100,255,0.3); }
</style>
