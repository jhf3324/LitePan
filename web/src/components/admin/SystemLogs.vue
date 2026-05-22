<template>
  <div class="logs-page">
    <div v-if="stats" class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon blue">
          <i class="fas fa-file-alt"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总日志数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ recentErrorCount }}</div>
          <div class="stat-label">近 24 小时错误</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">
          <i class="fas fa-cubes"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ activeModuleCount }}</div>
          <div class="stat-label">活跃模块</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon amber">
          <i class="fas fa-list"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ logs.length }}</div>
          <div class="stat-label">当前结果数</div>
        </div>
      </div>
    </div>

    <div class="logs-controls">
      <div class="controls-fields">
        <div class="filter-item">
          <label for="log-level-filter">级别</label>
          <select id="log-level-filter" v-model="filters.level" @change="loadLogs">
            <option value="">所有级别</option>
            <option v-for="level in levels" :key="level.value" :value="level.value">
              {{ level.emoji }} {{ level.name }}
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label for="log-module-filter">模块</label>
          <select id="log-module-filter" v-model="filters.module" @change="loadLogs">
            <option value="">所有模块</option>
            <option v-for="module in modules" :key="module.value" :value="module.value">
              {{ module.name }}
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label for="log-period-filter">时间范围</label>
          <select id="log-period-filter" v-model="filters.period" @change="loadLogs">
            <option value="all">全部时间</option>
            <option value="today">今天</option>
            <option value="24h">近 24 小时</option>
            <option value="7d">近 7 天</option>
          </select>
        </div>

        <div class="filter-item search-item">
          <label for="log-search">关键词</label>
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input
              id="log-search"
              v-model="filters.keyword"
              type="text"
              placeholder="搜索消息内容..."
              @input="debouncedSearch"
            >
          </div>
        </div>
      </div>

      <div class="controls-actions">
        <button
          type="button"
          class="toolbar-btn icon-only primary"
          :disabled="loading"
          title="刷新日志"
          @click="refreshAll"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn icon-only"
          title="重置筛选"
          @click="resetFilters"
        >
          <i class="fas fa-undo-alt"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn icon-only danger"
          :disabled="cleanupLoading"
          title="清理当前筛选日志"
          @click="cleanupLogs"
        >
          <i class="fas" :class="cleanupLoading ? 'fa-spinner fa-spin' : 'fa-eraser'"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn icon-only danger"
          :disabled="clearAllLoading"
          title="清空全部日志"
          @click="clearAllLogs"
        >
          <i class="fas" :class="clearAllLoading ? 'fa-spinner fa-spin' : 'fa-trash-alt'"></i>
        </button>
      </div>
    </div>

    <div class="logs-container">
      <div v-if="loading" class="logs-state">
        <i class="fas fa-spinner fa-spin"></i>
        <span>正在加载日志...</span>
      </div>

      <div v-else-if="logs.length === 0" class="logs-state empty">
        <i class="fas fa-inbox"></i>
        <span>当前筛选条件下暂无日志</span>
      </div>

      <div v-else class="logs-list">
        <article
          v-for="log in logs"
          :key="log.id"
          class="log-card"
          :class="getLogLevelClass(log.level)"
        >
          <header class="log-card-header">
            <div class="log-card-main">
              <span class="log-level-badge" :class="getLogLevelClass(log.level)">
                {{ log.level_emoji }} {{ log.level_name }}
              </span>
              <span class="log-module-badge" :style="{ '--module-color': log.module_color }">
                {{ log.module_name }}
              </span>
            </div>
            <time class="log-time">{{ formatDateTime(log.timestamp) }}</time>
          </header>

          <div class="log-message">{{ log.message }}</div>

          <div v-if="log.driver_name || log.account_id" class="log-meta">
            <span v-if="log.driver_name" class="meta-chip">
              <i class="fas fa-plug"></i>
              {{ log.driver_name }}
            </span>
            <span v-if="log.account_id" class="meta-chip">
              <i class="fas fa-user-circle"></i>
              账号 {{ log.account_id }}
            </span>
          </div>

          <div v-if="log.details" class="log-details">
            <button type="button" class="details-toggle" @click="toggleExpanded(log.id)">
              <span>{{ expandedLogIds.has(log.id) ? '收起详细信息' : '查看详细信息' }}</span>
              <i class="fas" :class="expandedLogIds.has(log.id) ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            </button>
            <pre v-if="expandedLogIds.has(log.id)" class="details-content">{{ formatDetails(log.details) }}</pre>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useModal } from '../../composables/useModal'
import { formatDateTime } from '../../utils/format.js'

const logs = ref([])
const stats = ref(null)
const levels = ref([])
const modules = ref([])
const loading = ref(false)
const cleanupLoading = ref(false)
const clearAllLoading = ref(false)
const expandedLogIds = ref(new Set())
const { confirm } = useModal()

const filters = ref({
  level: '',
  module: '',
  period: 'all',
  keyword: ''
})

const activeModuleCount = computed(() => {
  if (!stats.value?.by_module) return 0
  return Object.keys(stats.value.by_module).length
})

const recentErrorCount = computed(() => stats.value?.recent_errors || 0)

let searchTimeout = null

const getTimeRange = () => {
  const now = new Date()

  if (filters.value.period === 'today') {
    const start = new Date(now)
    start.setHours(0, 0, 0, 0)
    return { start_time: start.toISOString() }
  }

  if (filters.value.period === '24h') {
    return {
      start_time: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
    }
  }

  if (filters.value.period === '7d') {
    return {
      start_time: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
    }
  }

  return {}
}

const buildLogQueryParams = () => {
  const params = {
    ...getTimeRange()
  }
  if (filters.value.level) params.level = Number(filters.value.level)
  if (filters.value.module) params.module = filters.value.module
  if (filters.value.keyword.trim()) params.keyword = filters.value.keyword.trim()
  return params
}

const hasActiveFilters = () => {
  const params = buildLogQueryParams()
  return Object.keys(params).length > 0
}

const loadLogs = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/logs/', { params: buildLogQueryParams() })
    logs.value = response.data
  } catch (error) {
    console.error('加载日志失败:', error)
    window.appNotification?.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await axios.get('/api/logs/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载日志统计失败:', error)
  }
}

const loadOptions = async () => {
  try {
    const [levelsRes, modulesRes] = await Promise.all([
      axios.get('/api/logs/levels'),
      axios.get('/api/logs/modules')
    ])
    levels.value = levelsRes.data
    modules.value = modulesRes.data
  } catch (error) {
    console.error('加载日志选项失败:', error)
  }
}

const refreshAll = async () => {
  await Promise.all([loadStats(), loadLogs()])
}

const cleanupLogs = async () => {
  const activeFilters = hasActiveFilters()
  try {
    await confirm({
      title: activeFilters ? '清理筛选日志' : '清理全部日志',
      content: activeFilters
        ? '确定要清理当前筛选条件匹配的日志吗？此操作无法恢复。'
        : '当前没有筛选条件，将清空全部日志。确定继续吗？此操作无法恢复。',
      confirmText: '清理',
      confirmClass: 'btn-danger',
      icon: 'trash'
    })

    cleanupLoading.value = true
    const response = await axios.delete('/api/logs/filtered', { params: buildLogQueryParams() })
    window.appNotification?.success(response.data?.message || '日志已清理')
    expandedLogIds.value = new Set()
    await refreshAll()
  } catch (error) {
    if (error.message !== 'Modal closed') {
      console.error('清理日志失败:', error)
      window.appNotification?.error('清理日志失败')
    }
  } finally {
    cleanupLoading.value = false
  }
}

const clearAllLogs = async () => {
  try {
    await confirm({
      title: '清空全部日志',
      content: '确定要清空全部日志吗？此操作会删除所有日志文件，且无法恢复。',
      confirmText: '清空',
      confirmClass: 'btn-danger',
      icon: 'trash'
    })

    clearAllLoading.value = true
    const response = await axios.delete('/api/logs/cleanup', {
      params: { days: 0 }
    })
    window.appNotification?.success(response.data?.message || '日志已清空')
    expandedLogIds.value = new Set()
    await refreshAll()
  } catch (error) {
    if (error.message !== 'Modal closed') {
      console.error('清空日志失败:', error)
      window.appNotification?.error('清空日志失败')
    }
  } finally {
    clearAllLoading.value = false
  }
}

const resetFilters = async () => {
  filters.value = {
    level: '',
    module: '',
    period: 'all',
    keyword: ''
  }
  expandedLogIds.value = new Set()
  await refreshAll()
}

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadLogs()
  }, 350)
}

const toggleExpanded = (logId) => {
  const next = new Set(expandedLogIds.value)
  if (next.has(logId)) {
    next.delete(logId)
  } else {
    next.add(logId)
  }
  expandedLogIds.value = next
}

const getLogLevelClass = (level) => {
  const classes = {
    10: 'debug',
    20: 'info',
    30: 'warning',
    40: 'error',
    50: 'critical'
  }
  return classes[level] || 'info'
}




const formatDetails = (details) => JSON.stringify(details, null, 2)

onMounted(async () => {
  await Promise.all([
    loadOptions(),
    loadStats(),
    loadLogs()
  ])
})
</script>

<style scoped>
.logs-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toolbar-btn {
  height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.toolbar-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.toolbar-btn.primary {
  border-color: #c7d8ff;
  background: #eef4ff;
  color: #2f5fd0;
}

.toolbar-btn.primary:hover {
  background: #e4eeff;
}

.toolbar-btn.danger {
  color: #c2410c;
  border-color: #fed7aa;
  background: #fff7ed;
}

.toolbar-btn.danger:hover {
  background: #ffedd5;
  border-color: #fdba74;
}

.toolbar-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.toolbar-btn.icon-only {
  width: 40px;
  padding: 0;
  justify-content: center;
  flex: 0 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 22px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.stat-icon {
  width: 46px;
  height: 46px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #ffffff;
  font-size: 18px;
}

.stat-icon.blue {
  background: linear-gradient(135deg, #4c74df, #02a6f0);
}

.stat-icon.red {
  background: linear-gradient(135deg, #ef4444, #f97316);
}

.stat-icon.purple {
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
}

.stat-icon.amber {
  background: linear-gradient(135deg, #f59e0b, #f97316);
}

.stat-content {
  min-width: 0;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
  color: #111827;
}

.stat-label {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
}

.logs-controls {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 18px;
  padding: 20px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.controls-fields {
  flex: 1;
  min-width: 0;
  display: grid;
  grid-template-columns: 160px 160px 170px minmax(260px, 1fr);
  gap: 14px;
}

.controls-actions {
  width: auto;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  gap: 10px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.filter-item select,
.search-box {
  height: 42px;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  background: #ffffff;
}

.filter-item select {
  padding: 0 12px;
  color: #334155;
  font-size: 14px;
  outline: none;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  color: #94a3b8;
}

.search-box input {
  width: 100%;
  border: none;
  background: transparent;
  outline: none;
  color: #334155;
  font-size: 14px;
}

.logs-container {
  min-height: 360px;
  border-radius: 20px;
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.logs-state {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  font-size: 15px;
}

.logs-state i {
  font-size: 24px;
}

.logs-state.empty i {
  color: #94a3b8;
}

.logs-list {
  display: flex;
  flex-direction: column;
}

.log-card {
  padding: 20px 24px;
  border-bottom: 1px solid #eef2f7;
  transition: background-color 0.18s ease;
}

.log-card:last-child {
  border-bottom: none;
}

.log-card:hover {
  background: #fafcff;
}

.log-card.warning {
  background-image: linear-gradient(90deg, rgba(245, 158, 11, 0.08), transparent 36%);
}

.log-card.error,
.log-card.critical {
  background-image: linear-gradient(90deg, rgba(239, 68, 68, 0.08), transparent 36%);
}

.log-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.log-card-main {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.log-level-badge,
.log-module-badge,
.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.log-level-badge.debug {
  background: #eef2ff;
  color: #4f46e5;
}

.log-level-badge.info {
  background: #eff6ff;
  color: #2563eb;
}

.log-level-badge.warning {
  background: #fff7ed;
  color: #c2410c;
}

.log-level-badge.error,
.log-level-badge.critical {
  background: #fef2f2;
  color: #dc2626;
}

.log-module-badge {
  background: #f8fafc;
  color: var(--module-color);
}

.log-module-badge::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--module-color);
}

.log-time {
  font-size: 13px;
  color: #64748b;
  white-space: nowrap;
}

.log-message {
  font-size: 14px;
  line-height: 1.8;
  color: #1f2937;
  word-break: break-word;
}

.log-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.meta-chip {
  background: #f8fafc;
  color: #475569;
}

.log-details {
  margin-top: 14px;
}

.details-toggle {
  width: 100%;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  color: #334155;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.details-content {
  margin: 10px 0 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 1100px) {
  .logs-controls {
    flex-direction: column;
  }

  .controls-fields {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .controls-actions {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .logs-controls {
    padding: 16px;
  }

  .controls-fields {
    grid-template-columns: 1fr;
  }

  .controls-actions,
  .log-card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .controls-actions {
    align-items: flex-start;
  }

  .log-time {
    white-space: normal;
  }
}
</style>
