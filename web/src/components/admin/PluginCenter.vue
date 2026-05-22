<template>
  <div class="plugin-page">
    <div class="plugin-toolbar" :class="{ detail: !!selectedPlugin, list: !selectedPlugin }">
      <div v-if="selectedPlugin" class="plugin-detail-topbar">
        <div class="detail-topbar-title">
          <strong>{{ selectedPlugin.name }}</strong>
          <span>v{{ selectedPlugin.version }}</span>
        </div>
        <button type="button" class="btn btn-secondary" @click="backToPluginList">
          <i class="fas fa-chevron-down"></i> 返回插件中心
        </button>
      </div>
      <button v-else class="btn btn-secondary" @click="rescanPlugins" :disabled="rescanLoading || pageLoading">
        <i class="fas fa-rotate"></i> 重新扫描
      </button>
    </div>

    <div v-if="!selectedPlugin" class="plugin-grid">
      <button
        v-for="plugin in plugins"
        :key="plugin.id"
        type="button"
        class="plugin-card market-card"
        @click="selectPlugin(plugin.id)"
      >
        <div class="plugin-card-top">
          <div>
            <div class="plugin-card-name">
              <span>{{ plugin.name }}</span>
              <span class="plugin-card-name-version">v{{ plugin.version }}</span>
            </div>
            <div v-if="plugin.author" class="plugin-card-version">
              <span>作者:{{ plugin.author }}</span>
            </div>
          </div>
          <div class="plugin-card-actions">
            <button class="plugin-config-btn" type="button" @click.stop="openPluginConfig(plugin)">
              <i class="fas fa-gear"></i>
            </button>
          </div>
        </div>
        <div class="plugin-card-desc">{{ plugin.description }}</div>
      </button>
    </div>

    <div v-else class="plugin-detail">
      <div class="plugin-main">
        <div v-if="selectedPlugin.has_frontend && selectedPlugin.frontend_kind === 'module'" ref="pluginRuntimeHost" class="runtime-plugin-panel"></div>
        <div v-else-if="selectedPlugin.has_frontend" class="runtime-plugin-panel">
          <iframe
            :key="pluginFrameKey"
            class="plugin-runtime-frame"
            :src="buildPluginAssetUrl(selectedPlugin.frontend_entry_url, selectedPlugin.frontend_asset_version, pluginFrameKey)"
            :title="selectedPlugin.name"
          ></iframe>
        </div>
        <div v-else-if="selectedPlugin.id === 'resource_search'" class="plugin-panel">
          <div class="plugin-panel-header">
            <div>
              <h3>资源搜索</h3>
              <p>输入关键词后聚合搜索资源，右侧结果按站点与网盘链接展示。</p>
            </div>
          </div>
          <div class="config-summary search-summary">
            <div class="summary-chip">搜索频道 {{ importedChannelCount }}</div>
            <div class="summary-chip">搜索页数 {{ pluginConfig.sync_pages || 2 }}</div>
            <div class="summary-chip">模式 实时搜索</div>
          </div>
          <div v-if="searchStatus.message" class="connection-box" :class="{ success: searchStatus.status === 'completed', danger: searchStatus.status === 'failed' }">
            <div class="connection-title">{{ searchStatus.message }}</div>
            <div class="connection-meta">
              <span>任务状态：{{ searchStatus.status || 'idle' }}</span>
              <span>已搜索频道：{{ searchStatus.processed_channels }}/{{ searchStatus.total_channels }}</span>
              <span>累计结果：{{ searchStatus.result_count }}</span>
            </div>
          </div>
          <div class="search-bar">
            <input
              v-model.trim="searchKeyword"
              type="text"
              class="search-input"
              placeholder="输入资源名称，例如：三体"
              @keyup.enter="runSearch"
            >
            <button class="btn btn-primary" @click="runSearch" :disabled="searchLoading || pageLoading">
              <i class="fas fa-search"></i> {{ searchLoading ? '搜索中' : '搜索' }}
            </button>
          </div>

          <div v-if="searchResults.length" class="search-results">
            <div v-for="item in searchResults" :key="item.id" class="search-item">
              <div class="search-item-main">
                <div class="search-item-title">{{ item.title }}</div>
                <div class="search-item-meta">
                  <span>{{ item.platform_name }}</span>
                  <span v-if="item.password">提取码 {{ item.password }}</span>
                  <span>来源 {{ item.source }}</span>
                  <span v-if="item.datetime">{{ item.datetime }}</span>
                </div>
              </div>
              <div class="search-item-actions">
                <button class="btn btn-secondary small" @click="openShareLink(item.share_url)">
                  <i class="fas fa-arrow-up-right-from-square"></i> 打开链接
                </button>
              </div>
            </div>
          </div>

          <div v-else class="plugin-empty">
            <span>{{ searched ? '没有找到相关资源' : '输入关键词后开始搜索资源' }}</span>
          </div>
        </div>
        <div v-else class="plugin-empty large">
          <span>当前插件未提供运行时前台页面</span>
        </div>
      </div>
    </div>

    <div v-if="configModalVisible && configPlugin" class="config-overlay">
      <div class="config-modal">
        <div class="config-modal-header">
          <div>
            <h3>{{ configPlugin.name }} 配置</h3>
          </div>
          <button type="button" class="plugin-config-btn large" @click="closePluginConfig">
            <i class="fas fa-xmark"></i>
          </button>
        </div>
        <div
          v-if="configPlugin?.has_config_frontend && configPlugin.config_frontend_kind === 'module'"
          ref="pluginConfigHost"
          class="plugin-config-runtime"
        ></div>
        <div v-else-if="configPlugin?.has_config_frontend" class="plugin-config-runtime">
          <iframe
            :key="configFrameKey"
            class="plugin-runtime-frame"
            :src="buildPluginAssetUrl(configPlugin.config_frontend_entry_url, configPlugin.config_frontend_asset_version, configFrameKey)"
            :title="`${configPlugin.name} 配置`"
          ></iframe>
        </div>
        <div v-else-if="configPlugin.id === 'resource_search'" class="resource-config">
          <div class="config-row config-row-proxy">
            <div class="config-item flex-1">
              <label class="config-label">代理地址</label>
              <input
                v-model.trim="pluginConfig.proxy_url"
                type="text"
                class="config-input"
                placeholder="例如：http://192.168.1.1:8888"
              >
            </div>
            <div class="config-inline-actions compact">
              <button class="btn btn-secondary" @click="testPluginConnection" :disabled="testingConnection || saveLoading || pageLoading">
                <i :class="testingConnection ? 'fas fa-spinner fa-spin' : 'fas fa-plug'"></i>
                {{ testingConnection ? '测试中...' : '测试连通性' }}
              </button>
            </div>
          </div>
          <div class="plugin-config-grid compact">
            <div class="config-item">
              <label class="config-label">请求超时秒数</label>
              <input
                v-model.number="pluginConfig.timeout_seconds"
                type="number"
                class="config-input"
                min="3"
                max="60"
              >
            </div>
            <div class="config-item">
              <label class="config-label">搜索页数</label>
              <input
                v-model.number="pluginConfig.sync_pages"
                type="number"
                class="config-input"
                min="1"
                max="5"
              >
            </div>
          </div>
          <div class="config-item">
            <div class="config-section-header">
              <label class="config-label">当前频道列表 {{ importedChannelCount }}</label>
              <button class="config-link-button" @click="toggleImportEditor">
                <i class="fas fa-file-import"></i> {{ showImportEditor ? '收起导入' : '导入频道列表' }}
              </button>
            </div>
            <div class="channel-list-box">
              <textarea
                v-if="showImportEditor"
                v-model="importConfigText"
                class="config-textarea channel-textarea"
                placeholder='粘贴频道列表，例如：Lsp115:115网盘资源分享频道；alyp_1:网盘(高品质)影视'
              ></textarea>
              <div v-else-if="resourceChannelList.length" class="channel-list">
                <span v-for="channel in resourceChannelList" :key="channel.id" class="channel-chip">
                  {{ channel.name }}
                </span>
              </div>
              <div v-else class="channel-empty">当前还没有导入任何频道</div>
            </div>
            <div v-if="showImportEditor" class="config-help">推荐格式：频道ID:频道名称。多个频道可用换行、逗号、分号分隔，也兼容旧的 JSON 数组格式。重新导入会直接覆盖当前频道列表，点击保存后生效。</div>
            <div v-if="showImportEditor" class="config-inline-actions">
              <button class="btn btn-secondary" @click="toggleImportEditor">取消导入</button>
            </div>
          </div>
        </div>
        <div v-else-if="configPlugin.config_schema?.length" class="plugin-config-grid">
          <div v-for="field in configPlugin.config_schema" :key="field.key" class="config-item">
            <label class="config-label">{{ field.label }}</label>
            <input
              v-if="field.type !== 'boolean'"
              v-model="pluginConfig[field.key]"
              :type="field.type === 'number' ? 'number' : 'text'"
              class="config-input"
              :placeholder="field.placeholder || ''"
            >
            <label v-else class="config-switch">
              <input type="checkbox" v-model="pluginConfig[field.key]">
              <span>启用</span>
            </label>
          </div>
        </div>
        <div v-else class="plugin-empty">当前插件没有可配置项</div>
        <div v-if="!configPlugin?.has_config_frontend" class="config-actions">
          <button class="btn btn-primary" @click="savePluginConfig" :disabled="saveLoading || pageLoading">
            <i class="fas fa-save"></i> 保存配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'

const plugins = ref([])
const selectedPluginId = ref('')
const configPluginId = ref('')
const pluginRuntimeHost = ref(null)
const pluginConfigHost = ref(null)
const pluginConfig = ref({})
const searchKeyword = ref('')
const searchResults = ref([])
const searched = ref(false)
const pageLoading = ref(false)
const rescanLoading = ref(false)
const saveLoading = ref(false)
const searchLoading = ref(false)
const configModalVisible = ref(false)
const importConfigText = ref('')
const connectionTest = ref(null)
const testingConnection = ref(false)
const showImportEditor = ref(false)
const pluginFrameKey = ref(0)
const configFrameKey = ref(0)
let runtimePluginInstance = null
let runtimeConfigInstance = null
const activeSearchJobId = ref('')
const searchPollTimer = ref(null)
const searchStatus = ref({
  status: '',
  message: '',
  processed_channels: 0,
  total_channels: 0,
  result_count: 0
})

const selectedPlugin = computed(() => plugins.value.find(plugin => plugin.id === selectedPluginId.value) || null)
const configPlugin = computed(() => plugins.value.find(plugin => plugin.id === configPluginId.value) || null)
const importedChannelCount = computed(() => Array.isArray(pluginConfig.value?.channels) ? pluginConfig.value.channels.length : 0)
const resourceChannelList = computed(() => Array.isArray(pluginConfig.value?.channels) ? pluginConfig.value.channels : [])

const buildPluginAssetUrl = (baseUrl, assetVersion, frameVersion) => {
  if (!baseUrl) return ''
  const versionParts = [assetVersion, frameVersion].filter(Boolean)
  const version = versionParts.join('-')
  if (!version) return baseUrl
  return `${baseUrl}?v=${version}`
}

const loadPlugins = async () => {
  pageLoading.value = true
  try {
    const response = await axios.get('/api/plugins')
    plugins.value = response.data?.data || []
    if (selectedPluginId.value && !plugins.value.some(plugin => plugin.id === selectedPluginId.value)) {
      selectedPluginId.value = ''
    }
    if (configPluginId.value && !plugins.value.some(plugin => plugin.id === configPluginId.value)) {
      configPluginId.value = ''
      configModalVisible.value = false
    }
  } catch (error) {
    window.appNotification?.error('加载插件失败')
  } finally {
    pageLoading.value = false
  }
}

const selectPlugin = (pluginId) => {
  selectedPluginId.value = pluginId
}

const backToPluginList = () => {
  stopSearchPolling()
  selectedPluginId.value = ''
}

const openPluginConfig = (plugin) => {
  configPluginId.value = plugin.id
  pluginConfig.value = { ...(plugin?.config || {}) }
  syncImportTextFromConfig(pluginConfig.value)
  connectionTest.value = null
  configModalVisible.value = true
  showImportEditor.value = false
}

const closePluginConfig = () => {
  destroyConfigPlugin()
  configModalVisible.value = false
  configPluginId.value = ''
}

watch(selectedPlugin, (plugin) => {
  stopSearchPolling()
  pluginFrameKey.value += 1
  pluginConfig.value = plugin ? { ...(plugin.config || {}) } : {}
  syncImportTextFromConfig(pluginConfig.value)
  connectionTest.value = null
  showImportEditor.value = false
  searchResults.value = []
  searched.value = false
  searchStatus.value = {
    status: '',
    message: '',
    processed_channels: 0,
    total_channels: 0,
    result_count: 0
  }
  mountRuntimePlugin()
})

const rescanPlugins = async () => {
  rescanLoading.value = true
  try {
    const response = await axios.post('/api/plugins/rescan')
    plugins.value = response.data?.data || []
    if (selectedPluginId.value && !plugins.value.some(plugin => plugin.id === selectedPluginId.value)) {
      selectedPluginId.value = ''
    }
    window.appNotification?.success('插件扫描完成')
  } catch (error) {
    window.appNotification?.error('插件扫描失败')
  } finally {
    rescanLoading.value = false
  }
}

const savePluginConfig = async () => {
  if (!configPlugin.value) return
  saveLoading.value = true
  try {
    if (configPlugin.value.id === 'resource_search' && showImportEditor.value) {
      pluginConfig.value = {
        ...pluginConfig.value,
        channels: parseImportedChannelsInput(importConfigText.value)
      }
    }
    const normalized = configPlugin.value.id === 'resource_search'
      ? normalizeResourceSearchConfig(pluginConfig.value)
      : normalizePluginConfig(configPlugin.value.config_schema || [], pluginConfig.value)
    const response = await axios.put(`/api/plugins/${configPlugin.value.id}/config`, {
      config: normalized
    })
    updatePluginItem(response.data?.data)
    pluginConfig.value = { ...(response.data?.data?.config || normalized) }
    syncImportTextFromConfig(pluginConfig.value)
    if (configPlugin.value?.has_frontend && selectedPlugin.value?.id === configPlugin.value.id) {
      pluginFrameKey.value += 1
      mountRuntimePlugin()
    }
    showImportEditor.value = false
    configModalVisible.value = false
    configPluginId.value = ''
    window.appNotification?.success('插件配置已保存')
  } catch (error) {
    const message = error instanceof SyntaxError ? '导入频道列表格式不正确' : '保存插件配置失败'
    window.appNotification?.error(message)
  } finally {
    saveLoading.value = false
  }
}

const savePluginConfigFromRuntime = async (config, options = {}) => {
  if (!configPlugin.value) {
    throw new Error('当前没有正在配置的插件')
  }
  saveLoading.value = true
  try {
    const response = await axios.put(`/api/plugins/${configPlugin.value.id}/config`, {
      config
    })
    updatePluginItem(response.data?.data)
    pluginConfig.value = { ...(response.data?.data?.config || config) }
    if (configPlugin.value?.has_frontend && selectedPlugin.value?.id === configPlugin.value.id) {
      pluginFrameKey.value += 1
      mountRuntimePlugin()
    }
    if (options.closeAfterSave) {
      closePluginConfig()
    }
    return response.data?.data
  } finally {
    saveLoading.value = false
  }
}

const testPluginConnectionFromRuntime = async (config) => {
  if (!configPlugin.value) {
    throw new Error('当前没有正在配置的插件')
  }
  testingConnection.value = true
  try {
    await axios.put(`/api/plugins/${configPlugin.value.id}/config`, {
      config
    })
    pluginConfig.value = { ...config }
    const testResponse = await axios.post(`/api/plugins/${configPlugin.value.id}/test-connection`)
    return testResponse.data?.data || null
  } finally {
    testingConnection.value = false
  }
}

const toggleImportEditor = () => {
  showImportEditor.value = !showImportEditor.value
  if (showImportEditor.value) {
    syncImportTextFromConfig(pluginConfig.value)
  }
}

const testPluginConnection = async () => {
  if (!configPlugin.value) return
  testingConnection.value = true
  connectionTest.value = null
  try {
    const normalized = normalizeResourceSearchConfig(pluginConfig.value)
    const response = await axios.put(`/api/plugins/${configPlugin.value.id}/config`, {
      config: normalized
    })
    updatePluginItem(response.data?.data)
    pluginConfig.value = { ...(response.data?.data?.config || normalized) }
    const testResponse = await axios.post(`/api/plugins/${configPlugin.value.id}/test-connection`)
    connectionTest.value = testResponse.data?.data || null
    if (connectionTest.value?.ok) {
      window.appNotification?.success('连通性测试通过')
    } else {
      window.appNotification?.warning('连通性测试未通过，请检查代理或频道可访问性')
    }
  } catch (error) {
    connectionTest.value = {
      ok: false,
      message: extractErrorMessage(error, '连通性测试失败'),
      tested_channels: []
    }
    window.appNotification?.error(connectionTest.value.message)
  } finally {
    testingConnection.value = false
  }
}

const runSearch = async () => {
  if (!searchKeyword.value) {
    window.appNotification?.warning('请输入关键词')
    return
  }
  if (!selectedPlugin.value?.enabled) {
    window.appNotification?.warning('请先启用资源搜索插件')
    return
  }

  searchLoading.value = true
  searched.value = true
  stopSearchPolling()
  searchResults.value = []
  searchStatus.value = {
    status: 'starting',
    message: '搜索任务启动中',
    processed_channels: 0,
    total_channels: importedChannelCount.value || 0,
    result_count: 0
  }
  try {
    const response = await axios.post('/api/plugins/search-jobs', {
      plugin_id: selectedPlugin.value.id,
      keyword: searchKeyword.value,
      page: 1
    })
    activeSearchJobId.value = response.data?.data?.job_id || ''
    if (!activeSearchJobId.value) {
      throw new Error('搜索任务创建失败')
    }
    await pollSearchJob()
    if (activeSearchJobId.value) {
      searchPollTimer.value = window.setInterval(pollSearchJob, 1000)
    }
  } catch (error) {
    searchResults.value = []
    searchStatus.value = {
      status: 'failed',
      message: extractErrorMessage(error, '资源搜索失败'),
      processed_channels: 0,
      total_channels: importedChannelCount.value || 0,
      result_count: 0
    }
    window.appNotification?.error(extractErrorMessage(error, '资源搜索失败'))
  }
}

const pollSearchJob = async () => {
  if (!activeSearchJobId.value) return
  try {
    const response = await axios.get(`/api/plugins/search-jobs/${activeSearchJobId.value}`)
    const data = response.data?.data || {}
    searchResults.value = data.items || []
    const progress = data.progress || {}
    searchStatus.value = {
      status: data.status || '',
      message: data.message || '',
      processed_channels: progress.processed_channels || 0,
      total_channels: progress.total_channels || importedChannelCount.value || 0,
      result_count: progress.result_count || (data.items || []).length
    }
    if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
      stopSearchPolling()
      searchLoading.value = false
      if (data.status === 'failed') {
        window.appNotification?.error(data.error || data.message || '资源搜索失败')
      }
    }
  } catch (error) {
    stopSearchPolling()
    searchLoading.value = false
    searchStatus.value = {
      status: 'failed',
      message: extractErrorMessage(error, '获取搜索结果失败'),
      processed_channels: 0,
      total_channels: importedChannelCount.value || 0,
      result_count: 0
    }
    window.appNotification?.error(searchStatus.value.message)
  }
}

const stopSearchPolling = () => {
  if (searchPollTimer.value) {
    window.clearInterval(searchPollTimer.value)
    searchPollTimer.value = null
  }
  activeSearchJobId.value = ''
}

const openShareLink = (url) => {
  window.open(url, '_blank', 'noopener,noreferrer')
}

const updatePluginItem = (pluginData) => {
  if (!pluginData) return
  const index = plugins.value.findIndex(item => item.id === pluginData.id)
  if (index >= 0) {
    plugins.value[index] = pluginData
  } else {
    plugins.value.push(pluginData)
  }
}

const extractErrorMessage = (error, fallback) => {
  return error?.response?.data?.detail || error?.response?.data?.message || error?.message || fallback
}

const normalizePluginConfig = (schema, config) => {
  const normalized = {}
  for (const field of schema) {
    const value = config[field.key]
    if (field.type === 'number') {
      normalized[field.key] = Number(value || field.default || 0)
    } else if (field.type === 'boolean') {
      normalized[field.key] = Boolean(value)
    } else {
      normalized[field.key] = (value ?? '').toString()
    }
  }
  return normalized
}

const normalizeImportedChannels = (payload) => {
  const channelList = Array.isArray(payload)
    ? payload
    : Array.isArray(payload?.channels)
      ? payload.channels
      : []
  return channelList
        .map(item => {
          if (typeof item === 'string') return { id: item, name: item }
          const id = (item?.id || '').toString().trim()
          const name = (item?.name || id).toString().trim()
          return id ? { id, name } : null
        })
        .filter(Boolean)
}

const parseSimpleChannelsText = (text) => {
  return text
    .split(/[\r\n,;；，]+/)
    .map(item => item.trim())
    .filter(Boolean)
    .map(item => {
      const separatorIndex = item.indexOf(':') >= 0 ? item.indexOf(':') : item.indexOf('：')
      if (separatorIndex < 0) {
        const id = item.trim()
        return id ? { id, name: id } : null
      }
      const id = item.slice(0, separatorIndex).trim()
      const name = item.slice(separatorIndex + 1).trim() || id
      return id ? { id, name } : null
    })
    .filter(Boolean)
}

const parseImportedChannelsInput = (text) => {
  const trimmed = (text || '').trim()
  if (!trimmed) return []
  if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
    const parsed = JSON.parse(trimmed)
    return normalizeImportedChannels(parsed)
  }
  return parseSimpleChannelsText(trimmed)
}

const normalizeResourceSearchConfig = (config) => ({
  proxy_url: (config.proxy_url || '').toString().trim(),
  timeout_seconds: Math.max(3, Number(config.timeout_seconds || 10)),
  sync_pages: Math.max(1, Math.min(5, Number(config.sync_pages || 2))),
  channels: Array.isArray(config.channels) ? config.channels : [],
  cloud_types: Array.isArray(config.cloud_types) && config.cloud_types.length
    ? config.cloud_types
    : ['baidu', 'aliyun', 'quark', 'tianyi', 'uc', 'mobile', '115', 'pikpak', 'xunlei', '123', 'others']
})

const syncImportTextFromConfig = (config) => {
  if (!selectedPlugin.value || selectedPlugin.value.id !== 'resource_search') {
    importConfigText.value = ''
    return
  }

  const channels = Array.isArray(config?.channels) ? config.channels : []
  importConfigText.value = channels
    .map(item => `${item.id}:${item.name || item.id}`)
    .join('\n')
}

onMounted(() => {
  loadPlugins()
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  stopSearchPolling()
  destroyRuntimePlugin()
  window.removeEventListener('keydown', handleGlobalKeydown)
})

const handleGlobalKeydown = (event) => {
  if (event.key === 'Escape' && configModalVisible.value) {
    closePluginConfig()
  }
}

const destroyRuntimePlugin = () => {
  if (runtimePluginInstance && typeof runtimePluginInstance.unmount === 'function') {
    runtimePluginInstance.unmount()
  }
  runtimePluginInstance = null
}

const destroyConfigPlugin = () => {
  if (runtimeConfigInstance && typeof runtimeConfigInstance.unmount === 'function') {
    runtimeConfigInstance.unmount()
  }
  runtimeConfigInstance = null
}

const mountRuntimePlugin = async () => {
  destroyRuntimePlugin()
  const plugin = selectedPlugin.value
  if (!plugin?.has_frontend || plugin.frontend_kind !== 'module') return
  await nextTick()
  if (!pluginRuntimeHost.value) return

  try {
    const runtimeModule = await import(/* @vite-ignore */ buildPluginAssetUrl(
      plugin.frontend_entry_url,
      plugin.frontend_asset_version,
      pluginFrameKey.value
    ))
    if (selectedPlugin.value?.id !== plugin.id) return
    const mount = runtimeModule?.mount
    if (typeof mount !== 'function') {
      throw new Error('插件前台未导出 mount 方法')
    }
    const instance = await mount(pluginRuntimeHost.value, {
      plugin,
      notify: window.appNotification
    })
    runtimePluginInstance = instance && typeof instance === 'object' ? instance : null
  } catch (error) {
    window.appNotification?.error(error?.message || '加载插件前台失败')
  }
}

const mountConfigPlugin = async () => {
  destroyConfigPlugin()
  const plugin = configPlugin.value
  if (!configModalVisible.value || !plugin?.has_config_frontend || plugin.config_frontend_kind !== 'module') return
  await nextTick()
  if (!pluginConfigHost.value) return

  try {
    const configModule = await import(/* @vite-ignore */ buildPluginAssetUrl(
      plugin.config_frontend_entry_url,
      plugin.config_frontend_asset_version,
      configFrameKey.value
    ))
    if (configPlugin.value?.id !== plugin.id) return
    const mount = configModule?.mount
    if (typeof mount !== 'function') {
      throw new Error('插件配置前台未导出 mount 方法')
    }
    const instance = await mount(pluginConfigHost.value, {
      plugin,
      config: { ...(plugin.config || {}) },
      notify: window.appNotification,
      saveConfig: savePluginConfigFromRuntime,
      testConnection: testPluginConnectionFromRuntime,
      closeConfig: closePluginConfig
    })
    runtimeConfigInstance = instance && typeof instance === 'object' ? instance : null
  } catch (error) {
    window.appNotification?.error(error?.message || '加载插件配置前台失败')
  }
}

watch(
  [configModalVisible, configPlugin],
  async ([visible, plugin]) => {
    configFrameKey.value += 1
    if (!visible || !plugin) {
      destroyConfigPlugin()
      return
    }
    await mountConfigPlugin()
  }
)
</script>

<style scoped>
.plugin-page {
  display: grid;
  gap: 20px;
}

.plugin-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.plugin-toolbar.list {
  justify-content: flex-end;
}

.plugin-toolbar.detail {
  align-items: center;
}

.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.plugin-detail {
  display: grid;
  gap: 16px;
}

.plugin-detail-topbar {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
}

.detail-topbar-title {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  color: #64748b;
  font-size: 13px;
}

.detail-topbar-title strong {
  color: #0f172a;
  font-size: 15px;
}

.plugin-card,
.plugin-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}

.plugin-card {
  padding: 16px;
  text-align: left;
  cursor: pointer;
}

.market-card:hover {
  border-color: #bfd2ff;
  box-shadow: 0 10px 24px rgba(76, 116, 223, 0.08);
}

.plugin-card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.plugin-card-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.plugin-card-name {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  color: #0f172a;
  font-size: 15px;
  font-weight: 700;
}

.plugin-card-name-version {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 400;
}

.plugin-card-version {
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: #94a3b8;
  font-size: 12px;
}

.plugin-card-desc {
  margin-top: 10px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.plugin-config-btn {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dbe3f0;
  border-radius: 10px;
  background: #fff;
  color: #64748b;
  cursor: pointer;
}

.plugin-config-btn.large {
  width: 32px;
  height: 32px;
}

.plugin-main {
  display: grid;
  gap: 16px;
}

.plugin-panel {
  padding: 20px;
}

.runtime-plugin-panel {
  padding: 0;
  overflow: hidden;
  background: transparent;
  border: none;
  box-shadow: none;
  border-radius: 0;
}

.plugin-runtime-frame {
  width: 100%;
  min-height: 720px;
  border: none;
  display: block;
  background: transparent;
}

.plugin-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.plugin-panel-header h3,
.plugin-section-title {
  margin: 0 0 6px;
  color: #0f172a;
}

.plugin-panel-header p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.plugin-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 13px;
  white-space: nowrap;
}

.plugin-config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.resource-config {
  display: grid;
  gap: 14px;
}

.config-row {
  display: flex;
  gap: 14px;
  align-items: end;
}

.config-row-proxy {
  align-items: flex-end;
}

.flex-1 {
  flex: 1;
}

.plugin-config-grid.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.config-item {
  display: grid;
  gap: 6px;
}

.config-label {
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.config-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #dbe3f0;
  border-radius: 12px;
  outline: none;
}

.config-input:focus {
  border-color: #4c74df;
}

.config-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  color: #475569;
  font-size: 13px;
}

.channel-list-box {
  height: 144px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #fbfdff;
  overflow-y: auto;
}

.channel-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.channel-chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: #eef4ff;
  color: #3158c9;
  font-size: 12px;
  font-weight: 600;
}

.channel-empty {
  color: #94a3b8;
  font-size: 13px;
}

.import-editor {
  margin-top: 12px;
}

.config-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.config-textarea {
  width: 100%;
  min-height: 180px;
  padding: 12px;
  border: 1px solid #dbe3f0;
  border-radius: 14px;
  resize: vertical;
  outline: none;
  font-family: Consolas, Monaco, monospace;
  font-size: 12px;
  line-height: 1.6;
}

.config-textarea:focus {
  border-color: #4c74df;
}

.config-help {
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}

.config-inline-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  align-items: center;
  gap: 10px;
}

.config-inline-actions.compact {
  flex-wrap: nowrap;
  justify-content: flex-end;
  white-space: nowrap;
}

.config-link-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: none;
  background: transparent;
  color: #4c74df;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.config-link-button:hover {
  color: #3158c9;
}

.inline-test-result {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f8fafc;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.inline-test-result.success {
  background: #ecfdf5;
  color: #059669;
}

.inline-test-result.danger {
  background: #fff7ed;
  color: #ea580c;
}

.config-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.config-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f8fbff;
  border: 1px solid #dbe3f0;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
}

.connection-box {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #dbe3f0;
  background: #fbfdff;
}

.connection-box.success {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.connection-box.danger {
  background: #fff7ed;
  border-color: #fed7aa;
}

.connection-title {
  color: #0f172a;
  font-size: 13px;
  font-weight: 600;
}

.connection-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #64748b;
  font-size: 12px;
}

.connection-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.search-input {
  flex: 1;
  height: 42px;
  padding: 0 14px;
  border: 1px solid #dbe3f0;
  border-radius: 12px;
  outline: none;
}

.search-results {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border: 1px solid #edf2f7;
  border-radius: 14px;
  background: #fbfdff;
}

.search-item-title {
  color: #0f172a;
  font-size: 14px;
  font-weight: 600;
}

.search-item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}

.plugin-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 140px;
  border: 1px dashed #dbe3f0;
  border-radius: 16px;
  color: #64748b;
  background: #fbfdff;
}

.plugin-empty.large {
  min-height: 260px;
}

.config-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.36);
}

.config-modal {
  width: min(680px, 100%);
  max-height: min(88vh, 820px);
  overflow-y: auto;
  background: #fff;
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}

.config-modal-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.config-modal-header h3 {
  margin: 0 0 6px;
  color: #0f172a;
}

.config-modal-header p {
  display: none;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  padding: 0 16px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(76, 116, 223, 0.18);
}

.btn-secondary {
  background: #fff;
  color: #334155;
  border: 1px solid #dbe3f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #f8fbff;
}

.btn.small {
  height: 34px;
  padding: 0 12px;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .plugin-config-grid {
    grid-template-columns: 1fr;
  }

  .plugin-config-grid.compact {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .plugin-toolbar,
  .plugin-panel-header,
  .search-bar,
  .search-item,
  .config-row,
  .config-section-header,
  .plugin-detail-topbar {
    flex-direction: column;
    align-items: stretch;
  }

  .detail-topbar-title {
    justify-content: flex-start;
  }

  .config-inline-actions.compact {
    justify-content: flex-start;
    white-space: normal;
  }
}
</style>
