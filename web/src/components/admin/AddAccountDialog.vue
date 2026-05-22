<template>
  <!-- 两步式添加账号对话框 -->
  <div v-if="visible" class="dialog-overlay">
    <div class="dialog dialog-large" @click.stop>
              <div class="dialog-header">
        <div class="header-left">
          <div class="step-badge">{{ step }}</div>
          <h3>{{ step === 1 ? '选择网盘驱动' : '配置账号信息' }}</h3>
        </div>
        <button @click="close" class="close-btn">&times;</button>
      </div>
      
      <div class="dialog-content">
                          <!-- 第一步：选择驱动类型 -->
                  <div v-if="step === 1" class="step-content">
          
          <!-- 垂直切换驱动轮播容器 -->
          <div v-if="driverViewMode === 'carousel'" class="driver-carousel-vertical">
            <div class="driver-carousel-track-vertical" :style="{ transform: `translateY(-${currentDriverIndex * 180}px)` }">
              <div 
                v-for="(driver, index) in filteredDrivers" 
                :key="driver.key"
                class="driver-carousel-item-vertical"
                :class="{ 'active': currentDriverIndex === index }"
                @click="selectDriver(driver)"
              >
                <div class="driver-card-vertical" :class="{ selected: driver.key === form.driver_type }">
                  <!-- 左侧内容区域 -->
                  <div class="driver-content">
                    <DriverIcon
                      :logo="driver.card_logo"
                      :color="driver.card_color || '#4C74DF'"
                      :name="driver.card_name || driver.name"
                      size="xlarge"
                    />
                    <div class="driver-info">
                      <h3>{{ driver.display_name }}</h3>
                      <p>{{ driver.description || '云存储服务，支持高速上传下载' }}</p>
                    </div>
                  </div>
                  
                  <!-- 右侧控制区域 -->
                  <div class="driver-controls-right" v-show="filteredDrivers.length > 1">
                    <!-- 上箭头 -->
                    <button 
                      class="nav-arrow nav-arrow-up" 
                      @click.stop="moveDriver(-1)"
                    >
                      <i class="fas fa-chevron-up"></i>
                    </button>
                    
                    <!-- 位置指示器 -->
                    <div class="position-indicator">
                      <span class="position-text">{{ currentDriverIndex + 1 }}</span>
                      <div class="position-divider"></div>
                      <span class="total-text">{{ filteredDrivers.length }}</span>
                    </div>
                    
                    <!-- 下箭头 -->
                    <button 
                      class="nav-arrow nav-arrow-down" 
                      @click.stop="moveDriver(1)"
                    >
                      <i class="fas fa-chevron-down"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="driver-card-grid-view">
            <button
              v-for="(driver, index) in filteredDrivers"
              :key="driver.key"
              type="button"
              class="driver-mini-card"
              :class="{ selected: driver.key === form.driver_type }"
              @click="selectDriverFromGrid(driver, index)"
            >
              <DriverIcon
                :logo="driver.card_logo"
                :color="driver.card_color || '#4C74DF'"
                :name="driver.card_name || driver.name"
                size="large"
              />
              <div class="driver-mini-name">{{ driver.display_name }}</div>
            </button>

            <div v-if="filteredDrivers.length === 0" class="driver-empty-state">
              未找到匹配的驱动
            </div>
          </div>
          
          <!-- 第一步底部操作区 -->
          <div class="step-actions step-actions-with-search">
            <!-- 搜索区域 -->
            <div class="search-area">
              <button
                type="button"
                class="view-toggle-btn"
                :title="driverViewMode === 'carousel' ? '切换到卡片视图' : '切换到翻动视图'"
                @click="toggleDriverViewMode"
              >
                <i :class="driverViewMode === 'carousel' ? 'fas fa-th-large' : 'fas fa-exchange-alt'"></i>
              </button>
              <div class="search-container-compact">
                <div class="search-icon"><SvgIcon name="search" :size="15" /></div>
                <input 
                  id="driver-search"
                  name="driver-search"
                  type="text" 
                  class="search-input-compact" 
                  placeholder="搜索驱动..." 
                  v-model="searchQuery"
                  @input="handleSearch"
                >
                <button 
                  class="search-clear" 
                  v-show="searchQuery" 
                  @click="clearSearch"
                >×</button>
              </div>
              <div class="search-result-text" v-show="searchQuery">
                找到 {{ filteredDrivers.length }} 个匹配的驱动
              </div>
            </div>
            
            <!-- 下一步按钮 -->
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="nextStep" 
              :disabled="!canProceed"
            >
              下一步 <i class="fas fa-arrow-right"></i>
            </button>
          </div>
        </div>

        
        <!-- 第二步：配置账号信息 -->
        <div v-if="step === 2" class="step-content">
          <form @submit.prevent="submitForm" class="config-form">
            <!-- 纵向多行：整行全宽 / 或一行两列（如 WebDAV 根 URL + 子目录） -->
            <div class="config-fields">
              <div
                v-for="(row, rowIdx) in configLayoutRows"
                :key="'cfg-row-' + rowIdx"
                :class="row.mode === 'full' ? 'config-fields-row-full' : 'config-fields-row-half'"
              >
                <div
                  v-for="field in row.fields"
                  :key="field.name"
                  :class="['form-group', field.className || '']"
                >
                  <label :for="field.name">
                    {{ field.label }}
                    <span v-if="field.required" class="required">*</span>
                  </label>

                  <input
                    v-if="field.type === 'text'"
                    :id="field.name"
                    :name="field.name"
                    :value="getFieldValue(field.name)"
                    @input="setFieldValue(field.name, $event.target.value)"
                    @paste="handleSmartPaste($event, field.name)"
                    type="text"
                    class="form-input"
                    :class="{ 'error': errors[field.name] }"
                    :placeholder="field.placeholder"
                  />

                  <div
                    v-else-if="field.type === 'local_dir'"
                    class="form-input-with-action"
                  >
                    <input
                      :id="field.name"
                      :name="field.name"
                      :value="getFieldValue(field.name)"
                      @input="setFieldValue(field.name, $event.target.value)"
                      type="text"
                      class="form-input"
                      :class="{ 'error': errors[field.name] }"
                      :placeholder="field.placeholder"
                    />
                    <button
                      type="button"
                      class="form-input-action-btn"
                      @click="openLocalDirBrowser(field.name)"
                    >
                      <i class="fas fa-folder-open"></i> 浏览
                    </button>
                  </div>

                  <input
                    v-else-if="field.type === 'password'"
                    :id="field.name"
                    :name="field.name"
                    :value="config[field.name]"
                    @input="config[field.name] = $event.target.value"
                    @paste="handleSmartPaste($event, field.name)"
                    type="password"
                    class="form-input"
                    :class="{ 'error': errors[field.name] }"
                    :placeholder="field.placeholder"
                  />

                  <input
                    v-else-if="field.type === 'number'"
                    :id="field.name"
                    :name="field.name"
                    v-model.number="config[field.name]"
                    type="number"
                    class="form-input"
                    :class="{ 'error': errors[field.name] }"
                    :placeholder="field.placeholder"
                    :min="field.min"
                    :max="field.max"
                  />

                  <CustomSelect
                    v-else-if="field.type === 'select'"
                    :id="field.name"
                    v-model="config[field.name]"
                    :options="field.options"
                    :placeholder="`请选择${field.label}`"
                    :class="{ 'error': errors[field.name] }"
                  />

                  <textarea
                    v-else-if="field.type === 'textarea'"
                    :id="field.name"
                    :value="config[field.name]"
                    @input="config[field.name] = $event.target.value"
                    @paste="handleSmartPaste($event, field.name)"
                    class="form-input"
                    :class="{ 'error': errors[field.name] }"
                    :placeholder="field.placeholder"
                    rows="4"
                  ></textarea>

                  <div v-if="errors[field.name]" class="error-message">{{ errors[field.name] }}</div>
                </div>
              </div>
            </div>
          </form>
          
          <!-- 第二步按钮 -->
          <div class="step-actions">
            <div class="step-actions-left">
              <button 
                v-if="hasOAuthSupport" 
                type="button" 
                class="btn btn-oauth" 
                @click="handleOAuthAuth"
                :disabled="oauthLoading"
              >
                <i v-if="oauthLoading" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-key"></i>
                {{ oauthLoading ? '正在获取...' : (isEditMode ? '重新获取Token' : '自动获取Token') }}
              </button>
              <button 
                v-if="hasQrLoginSupport" 
                type="button" 
                class="btn btn-oauth" 
                @click="handleQrLogin"
                :disabled="qrLoading"
              >
                <i v-if="qrLoading" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-qrcode"></i>
                {{ qrActionText }}
              </button>
            </div>
            
            <!-- 右侧按钮 -->
            <div class="step-actions-right">
              <button v-if="!isEditMode" type="button" class="btn btn-secondary" @click="prevStep">
                <i class="fas fa-arrow-left"></i> 上一步
              </button>
              <button 
                type="button" 
                class="btn btn-primary" 
                @click="submitForm" 
                :disabled="loading"
              >
                <i v-if="loading" class="fas fa-spinner fa-spin"></i>
                {{ isEditMode ? '保存修改' : '添加账号' }}
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>

    <div v-if="qrModalVisible" class="qr-overlay" @click.self="closeQrModal">
      <div class="qr-panel">
        <div class="qr-panel-header">
          <div class="qr-panel-title">
            <i class="fas fa-qrcode"></i>
            {{ qrPanelTitle }}
          </div>
          <button class="close-btn" @click="closeQrModal">&times;</button>
        </div>
        <div class="qr-panel-body">
          <div v-if="qrStatus === 'loading'" class="qr-state qr-state-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>正在生成二维码...</span>
          </div>

          <div v-else-if="qrStatus === 'waiting'" class="qr-state qr-state-waiting">
            <img :src="qrImageBase64" class="qr-image" :alt="`${qrDriverName}扫码二维码`" />
            <div class="qr-hint">
              {{ qrHintText }}
            </div>
            <div class="qr-countdown" v-if="qrCountdown > 0">
              二维码剩余有效时间：{{ qrCountdown }} 秒
            </div>
          </div>

          <div v-else-if="qrStatus === 'success'" class="qr-state qr-state-success">
            <i class="fas fa-check-circle"></i>
            <div class="qr-result-title">已获取授权信息</div>
            <div class="qr-hint">请核对表单后保存</div>
          </div>

          <div v-else-if="qrStatus === 'expired'" class="qr-state qr-state-expired">
            <i class="fas fa-hourglass-end"></i>
            <div class="qr-result-title">二维码已过期</div>
            <div class="qr-hint">{{ qrMessage || '请重新获取二维码' }}</div>
            <button class="btn btn-oauth" @click="handleQrLogin" :disabled="qrLoading">
              <i class="fas fa-redo"></i>
              重新获取
            </button>
          </div>

          <div v-else-if="qrStatus === 'failed'" class="qr-state qr-state-failed">
            <i class="fas fa-times-circle"></i>
            <div class="qr-result-title">获取失败</div>
            <div class="qr-hint">{{ qrMessage || '请重试' }}</div>
            <button class="btn btn-oauth" @click="handleQrLogin" :disabled="qrLoading">
              <i class="fas fa-redo"></i>
              重新获取
            </button>
          </div>
        </div>
      </div>
    </div>

    <LocalDirBrowserModal
      v-if="localDirBrowserVisible"
      :initial-path="getFieldValue(localDirBrowserField)"
      @resolve="handleLocalDirSelected"
      @cancel="localDirBrowserVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '../../stores/admin'
import CustomSelect from '../CustomSelect.vue'
import SvgIcon from '../icons/SvgIcon.vue'
import DriverIcon from '../common/DriverIcon.vue'
import LocalDirBrowserModal from '../common/LocalDirBrowserModal.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  editAccount: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'success'])

// Store
const adminStore = useAdminStore()
const { drivers, accounts } = storeToRefs(adminStore)

// 状态
const step = ref(1)
const loading = ref(false)
const errors = ref({})
const localDirBrowserVisible = ref(false)
const localDirBrowserField = ref('')

const openLocalDirBrowser = (fieldName) => {
  localDirBrowserField.value = fieldName
  localDirBrowserVisible.value = true
}

const handleLocalDirSelected = (path) => {
  if (localDirBrowserField.value) {
    setFieldValue(localDirBrowserField.value, path)
  }
  localDirBrowserVisible.value = false
}
const isTransitioning = ref(true)

// OAuth相关状态
const oauthLoading = ref(false)
const oauthError = ref(null)
const oauthCancelled = ref(false)
let oauthPollTimer = null
let oauthPopup = null
const globalCacheTtl = ref(null)

const qrLoading = ref(false)
const qrModalVisible = ref(false)
const qrImageBase64 = ref('')
const qrStatus = ref('loading')
const qrMessage = ref('')
const qrCountdown = ref(0)
let qrPollTimer = null
let qrCountdownTimer = null
let qrStateId = null
let qrCancelled = false

// 轮播相关状态
const searchQuery = ref('')
const currentDriverIndex = ref(0)
const filteredDrivers = ref([])
const DRIVER_VIEW_MODE_KEY = 'litepan_add_account_driver_view_mode'
const savedDriverViewMode = localStorage.getItem(DRIVER_VIEW_MODE_KEY)
const driverViewMode = ref(['carousel', 'grid'].includes(savedDriverViewMode) ? savedDriverViewMode : 'carousel')


// 表单数据
const form = ref({
  name: '',
  driver_type: ''
})

const config = ref({})

// 计算属性
const isEditMode = computed(() => !!props.editAccount)

const selectedDriver = computed(() => {
  return drivers.value[form.value.driver_type]
})

const canProceed = computed(() => {
  return form.value.driver_type
})

// OAuth支持检查
const hasOAuthSupport = computed(() => {
  const driver = drivers.value[form.value.driver_type]
  return driver && driver.auto_oauth === 1
})

const hasQrLoginSupport = computed(() => {
  const driver = drivers.value[form.value.driver_type]
  return driver && driver.supports_qr_login === 1
})

const selectedDriverInfo = computed(() => drivers.value[form.value.driver_type] || {})
const qrDriverName = computed(() => selectedDriverInfo.value.display_name || '网盘')
const qrPanelTitle = computed(() => {
  if (form.value.driver_type === '189_cloud') return '扫码获取Token'
  return form.value.driver_type === 'quark_reverse' ? '扫码获取 Cookie' : '扫码登录'
})
const qrActionText = computed(() => {
  if (qrLoading.value) return '正在获取...'
  if (form.value.driver_type === 'quark_reverse') {
    return isEditMode.value ? '重新获取Cookie' : '扫码获取Cookie'
  }
  if (form.value.driver_type === '189_cloud') {
    return isEditMode.value ? '重新获取Token' : '扫码获取Token'
  }
  return isEditMode.value ? '重新扫码登录' : '扫码登录'
})
const qrHintText = computed(() => {
  if (form.value.driver_type === '189_cloud') {
    return '请使用小翼管家/天翼云盘/支付宝 APP扫码，成功后授权信息将填入表单'
  }
  return `请使用${qrDriverName.value} App扫码，成功后授权信息将填入表单`
})

// 驱动配置schema
const driverConfigSchema = ref({})

function _classListHasFullWidth(className) {
  if (!className) return false
  return String(className).split(/\s+/).includes('full-width')
}

const configLayoutRows = computed(() => {
  const driverConfig = driverConfigSchema.value || {}

  const buildFormField = (key, field) => {
    const formField = {
      name: key,
      label: field.label,
      type: field.type,
      placeholder: field.placeholder || `请输入${field.label}`,
      required: field.required || false,
      options: field.options || [],
      min: field.min,
      max: field.max,
      default: field.default,
      className: field.className || ''
    }
    if (key === 'api_url') {
      formField.className = 'full-width'
    }
    if (field.type === 'textarea' || field.type === 'local_dir' || (field.description && field.description.includes('cookie'))) {
      formField.className = 'full-width'
    }
    return formField
  }

  const nameField = {
    name: 'name',
    label: '账号名称',
    type: 'text',
    placeholder: '请输入账号名称',
    required: true,
    className: 'full-width'
  }

  const rows = [{ mode: 'full', fields: [nameField] }]
  const rawEntries = Object.entries(driverConfig)
    .filter(([, field]) => field && field.type !== 'hidden')
  /** 将相同 pairRow 的字段紧挨排列，避免 JSON 按键排序后无法两两配对 */
  const entries = []
  const seenPairRow = new Set()
  for (const item of rawEntries) {
    const [, f] = item
    if (f == null || f.pairRow == null) {
      entries.push(item)
      continue
    }
    const pr = f.pairRow
    if (seenPairRow.has(pr)) continue
    rawEntries.forEach((e) => {
      const [, ef] = e
      if (ef && ef.pairRow === pr) entries.push(e)
    })
    seenPairRow.add(pr)
  }

  const pending = []

  const flushPairs = () => {
    while (pending.length >= 2) {
      rows.push({ mode: 'half', fields: pending.splice(0, 2) })
    }
  }

  let i = 0
  while (i < entries.length) {
    const [key, field] = entries[i]
    const next = entries[i + 1]
    if (field.pairRow != null && next && next[1].pairRow === field.pairRow) {
      flushPairs()
      rows.push({
        mode: 'half',
        fields: [buildFormField(key, field), buildFormField(next[0], next[1])]
      })
      i += 2
      continue
    }
    const f = buildFormField(key, field)
    if (_classListHasFullWidth(f.className)) {
      flushPairs()
      if (pending.length) {
        rows.push({ mode: 'half', fields: [pending.pop()] })
      }
      rows.push({ mode: 'full', fields: [f] })
      i += 1
      continue
    }
    pending.push(f)
    flushPairs()
    i += 1
  }
  flushPairs()
  if (pending.length) {
    rows.push({ mode: 'half', fields: [pending.pop()] })
  }
  return rows
})

const configFieldsFlat = computed(() => configLayoutRows.value.flatMap((row) => row.fields))

// 获取驱动配置schema
const fetchDriverConfigSchema = async (driverName) => {
  try {
    const response = await fetch(`/api/admin/drivers/${driverName}/config-schema`)
    const result = await response.json()
    if (result.success) {
      driverConfigSchema.value = result.data
    } else {
      console.error('获取驱动配置失败:', result.message)
      driverConfigSchema.value = {}
    }
  } catch (error) {
    console.error('获取驱动配置失败:', error)
    driverConfigSchema.value = {}
  }
}

const fetchGlobalCacheTtl = async () => {
  if (globalCacheTtl.value !== null) {
    return globalCacheTtl.value
  }

  try {
    const response = await fetch('/api/admin/cache-config')
    const result = await response.json()
    if (result.success && result.data?.cache_ttl !== undefined && result.data?.cache_ttl !== null) {
      globalCacheTtl.value = Number(result.data.cache_ttl)
      return globalCacheTtl.value
    }
  } catch (error) {
    console.error('获取全局缓存默认值失败:', error)
  }

  globalCacheTtl.value = 30
  return globalCacheTtl.value
}

// 字段值处理辅助方法
const getFieldValue = (fieldName) => {
  if (fieldName === 'name') {
    return form.value.name
  }
  return config.value[fieldName]
}

const setFieldValue = (fieldName, value) => {
  if (fieldName === 'name') {
    form.value.name = value
  } else {
    config.value[fieldName] = value
  }
}

const handleSmartPaste = (event, fieldName) => {
  const clipboard = event.clipboardData || window.clipboardData
  if (!clipboard) return
  const raw = clipboard.getData('text')
  if (!raw) return
  let cleaned = raw.replace(/^[\s\u00A0]+|[\s\u00A0]+$/g, '')
  cleaned = cleaned.replace(/^(?:Basic|Bearer)[\s\u00A0]+/i, '')
  if (cleaned === raw) return
  event.preventDefault()
  setFieldValue(fieldName, cleaned)
}



// 方法
const close = () => {
  oauthCancelled.value = true
  oauthLoading.value = false
  if (oauthPollTimer) {
    clearTimeout(oauthPollTimer)
    oauthPollTimer = null
  }
  stopQrPolling()
  qrModalVisible.value = false
  resetForm()
  emit('close')
}

const resetForm = () => {
  step.value = 1
  form.value = {
    name: '',
    driver_type: ''
  }
  config.value = {}
  errors.value = {}
  loading.value = false
  searchQuery.value = ''
  currentDriverIndex.value = 0
  initializeDrivers()
}

// 初始化驱动列表
const initializeDrivers = () => {
  if (drivers.value) {
    filteredDrivers.value = Object.keys(drivers.value).map(key => ({
      key,
      ...drivers.value[key]
    }))
    // 自动选中第一个驱动
    if (filteredDrivers.value.length > 0) {
      selectDriverByIndex(0)
    }
  }
}

// 搜索处理
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    filteredDrivers.value = Object.keys(drivers.value).map(key => ({
      key,
      ...drivers.value[key]
    })).filter(driver => 
      driver.display_name.toLowerCase().includes(query) || 
      (driver.description && driver.description.toLowerCase().includes(query))
    )
  } else {
    initializeDrivers()
  }
  
  // 重置到第一个
  currentDriverIndex.value = 0
  if (filteredDrivers.value.length > 0) {
    selectDriverByIndex(0)
  }
}

// 清除搜索
const clearSearch = () => {
  searchQuery.value = ''
  initializeDrivers()
}

const toggleDriverViewMode = () => {
  driverViewMode.value = driverViewMode.value === 'carousel' ? 'grid' : 'carousel'
  localStorage.setItem(DRIVER_VIEW_MODE_KEY, driverViewMode.value)
}

// 移动驱动选择 - 简化版循环
const moveDriver = (direction) => {
  if (filteredDrivers.value.length <= 1) return
  
  isTransitioning.value = true
  
  if (direction > 0) {
    // 向下滚动
    currentDriverIndex.value++
    if (currentDriverIndex.value >= filteredDrivers.value.length) {
      currentDriverIndex.value = 0 // 循环到第一个
    }
  } else {
    // 向上滚动
    currentDriverIndex.value--
    if (currentDriverIndex.value < 0) {
      currentDriverIndex.value = filteredDrivers.value.length - 1 // 循环到最后一个
    }
  }
  
  selectDriverByIndex(currentDriverIndex.value)
}

// 跳转到指定驱动
const goToDriver = (index) => {
  currentDriverIndex.value = index
  selectDriverByIndex(index)
}

// 选择驱动
const selectDriver = (driver) => {
  form.value.driver_type = driver.key
  // 清除配置数据，避免驱动切换时配置残留
  config.value = {}
}

const selectDriverFromGrid = (driver, index) => {
  currentDriverIndex.value = index
  selectDriver(driver)
}

// 通过索引选择驱动
const selectDriverByIndex = (index) => {
  if (filteredDrivers.value[index]) {
    form.value.driver_type = filteredDrivers.value[index].key
    // 清除配置数据，避免驱动切换时配置残留
    config.value = {}
  }
}

const validateStep1 = () => {
  errors.value = {}
  
  if (!form.value.driver_type) {
    errors.value.driver_type = '请选择驱动类型'
    return false
  }
  
  return true
}

const validateStep2 = () => {
  errors.value = {}

  // 验证账号名称
  if (!form.value.name.trim()) {
    errors.value.name = '账号名称不能为空'
  } else if (!isEditMode.value) {
    // 检查账号名称是否已存在（编辑模式下跳过）
    const existingAccount = accounts.value.find(
      account => account.name.toLowerCase() === form.value.name.trim().toLowerCase()
    )
    if (existingAccount) {
      errors.value.name = '账号名称已存在，请使用其他名称'
    }
  }
  
  // 验证配置字段
  configFieldsFlat.value.forEach(field => {
    if (field.name === 'name') {
      return // 跳过name字段，因为已经单独验证
    }
    
    // 特殊处理TTL字段：允许为空值（空值表示使用全局默认值，0表示禁用缓存）
    if (field.name === 'cache_ttl') {
      const ttlValue = config.value[field.name]
      // 空字符串、null、undefined都是有效值（表示使用全局默认值）
      if (ttlValue !== undefined && ttlValue !== null && ttlValue !== '') {
        const numValue = Number(ttlValue)
        if (isNaN(numValue) || numValue < 0 || numValue > 1440) {
          errors.value[field.name] = `${field.label}必须在0-1440分钟之间，0表示禁用缓存，空值表示使用全局默认值`
        }
      }
      return // TTL字段不进行required验证
    }
    
    if (field.required && (!config.value[field.name] || config.value[field.name].toString().trim() === '')) {
      errors.value[field.name] = `${field.label}不能为空`
    }
  })
  
  return Object.keys(errors.value).length === 0
}



const nextStep = async () => {
  if (!validateStep1()) return
  
  await fetchDriverConfigSchema(form.value.driver_type)

  config.value = {}
  const cacheTtlDefault = await fetchGlobalCacheTtl()
  
  configFieldsFlat.value.forEach(field => {
    if (field.name === 'name') return // 跳过账号名称字段
    
    if (field.name === 'cache_ttl') {
      config.value[field.name] = cacheTtlDefault
    } else if (field.default !== undefined) {
      config.value[field.name] = field.default
    } else if (field.type === 'select' && field.options && field.options.length > 0) {
      config.value[field.name] = field.options[0].value
    }
  })
  
  step.value = 2
}

const prevStep = () => {
  step.value = 1
  errors.value = {}
  // 清除配置数据，避免驱动切换时配置残留
  config.value = {}
}

// OAuth处理方法
const renderOAuthPopupState = (title, message, isError = false) => {
  if (!oauthPopup || oauthPopup.closed) return

  try {
    oauthPopup.document.open()
    oauthPopup.document.write(`
      <!DOCTYPE html>
      <html lang="zh-CN">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${title}</title>
        <style>
          body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f6f8fb;
            color: #1f2937;
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
          }
          .panel {
            width: min(420px, calc(100vw - 32px));
            padding: 28px 24px;
            border-radius: 16px;
            background: #ffffff;
            box-shadow: 0 16px 48px rgba(15, 23, 42, 0.12);
            text-align: center;
          }
          .title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
            color: ${isError ? '#b91c1c' : '#111827'};
          }
          .message {
            font-size: 14px;
            line-height: 1.7;
            color: #4b5563;
            white-space: pre-wrap;
          }
        </style>
      </head>
      <body>
        <div class="panel">
          <div class="title">${title}</div>
          <div class="message">${message}</div>
        </div>
      </body>
      </html>
    `)
    oauthPopup.document.close()
  } catch (error) {
    console.warn('更新OAuth中转页失败:', error)
  }
}

const openOAuthProgressPage = () => {
  oauthPopup = window.open('', '_blank')
  if (!oauthPopup) {
    throw new Error('浏览器拦截了授权页面，请允许弹出窗口后重试')
  }

  renderOAuthPopupState('正在连接授权服务', '请稍候，页面将自动跳转到 OAuth 授权页。')
}

const getOAuthErrorMessage = (error, fallback = 'OAuth认证失败') => {
  if (error instanceof Error && error.message) {
    return error.message
  }
  if (typeof error === 'string' && error.trim()) {
    return error
  }
  if (error && typeof error === 'object') {
    if (typeof error.detail === 'string' && error.detail.trim()) return error.detail
    if (typeof error.message === 'string' && error.message.trim()) return error.message
    if (typeof error.error === 'string' && error.error.trim()) return error.error
  }
  return fallback
}

const createOAuthError = (message, retryable = false) => {
  const error = new Error(message)
  error.retryable = retryable
  return error
}

const parseOAuthResponseError = async (response, fallback) => {
  const payload = await response.json().catch(async () => {
    const text = await response.text().catch(() => '')
    return { detail: text }
  })
  return createOAuthError(
    payload?.detail || payload?.message || payload?.error || fallback,
    false
  )
}

const handleOAuthAuth = async () => {
  oauthLoading.value = true
  oauthError.value = null
  oauthCancelled.value = false
  if (oauthPollTimer) {
    clearTimeout(oauthPollTimer)
    oauthPollTimer = null
  }
  
  try {
    openOAuthProgressPage()
    const startResponse = await fetch('/api/oauth/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        driver_type: form.value.driver_type,
        server_use: true
      })
    })
    
    if (!startResponse.ok) {
      const errorResult = await startResponse.json().catch(() => ({}))
      throw new Error(errorResult.detail || errorResult.message || '启动OAuth认证失败')
    }
    
    const startResult = await startResponse.json()
    if (!startResult.success) {
      throw new Error(startResult.message || '启动OAuth认证失败')
    }
    
    if (oauthPopup && !oauthPopup.closed) {
      oauthPopup.location.href = startResult.data.oauth_url
    } else {
      window.open(startResult.data.oauth_url, '_blank')
    }
    
    await pollOAuthStatus(startResult.data.session_id)
    
  } catch (error) {
    const errorMessage = getOAuthErrorMessage(error)
    if (oauthCancelled.value && errorMessage.includes('已取消')) {
      return
    }
    console.error('OAuth认证失败:', error)
    oauthError.value = errorMessage

    renderOAuthPopupState('OAuth认证失败', `${errorMessage}\n\n你可以关闭此页后重试。`, true)
    
    if (window.appNotification) {
      window.appNotification.error(`OAuth认证失败: ${errorMessage}`, 8000)
    }
  } finally {
    oauthLoading.value = false
  }
}

// 轮询OAuth状态
const pollOAuthStatus = async (sessionId) => {
  const maxAttempts = 30 // 最多轮询30次（约2分钟）
  let attempts = 0

  return await new Promise((resolve, reject) => {
    const scheduleNextPoll = (delay) => {
      oauthPollTimer = setTimeout(() => {
        poll().catch(reject)
      }, delay)
    }

    const poll = async () => {
      if (oauthCancelled.value) {
        oauthPollTimer = null
        reject(new Error('OAuth认证已取消'))
        return
      }
      
      if (attempts >= maxAttempts) {
        oauthPollTimer = null
        reject(new Error('OAuth认证超时，请检查是否已完成授权'))
        return
      }
      
      attempts++
      
      try {
        const response = await fetch(`/api/oauth/status/${sessionId}`)
        if (!response.ok) {
          throw await parseOAuthResponseError(response, '查询OAuth状态失败')
        }
        
        const result = await response.json()
        if (!result?.success) {
          throw createOAuthError(
            result?.message || result?.detail || result?.data?.error || '查询OAuth状态失败',
            false
          )
        }
        if (!result?.data?.status) {
          throw createOAuthError('OAuth状态响应缺少 status 字段', false)
        }
        
        if (result.success && result.data.status === 'success') {
          // 认证成功，自动填入token
          const tokens = result.data.token_data || {}
          
          let filledCount = 0
          
          // 如果是编辑模式，先清空相关字段
          if (isEditMode.value) {
            for (const [key, value] of Object.entries(tokens)) {
              if (driverConfigSchema.value.hasOwnProperty(key)) {
                config.value[key] = ''
              }
            }
            // 强制触发Vue响应式更新
            config.value = { ...config.value }
            await nextTick()
          }
          
          // 只填充驱动配置schema中定义的字段
          for (const [key, value] of Object.entries(tokens)) {
            if (driverConfigSchema.value.hasOwnProperty(key)) {
              config.value[key] = value
              filledCount++
            }
          }
          
          // 强制触发Vue响应式更新
          config.value = { ...config.value }
          
          // 额外确保响应式更新
          await nextTick()
          
          // 通知服务器已收到Token
          try {
            await fetch(`/api/oauth/confirm-received/${sessionId}`, {
              method: 'POST'
            })
          } catch (confirmError) {
            console.warn('通知OAuth服务器失败:', confirmError.message)
          }
          
          if (form.value.driver_type === '115_open') {
            await new Promise(resolveDelay => setTimeout(resolveDelay, 2000))
          }
          
          oauthPollTimer = null
          if (window.appNotification) {
            // 使用更长的显示时间，确保用户从OAuth页面切回来时能看到通知
            window.appNotification.success(`OAuth认证成功，已自动填充 ${filledCount} 个字段`, 8000)
          }
          resolve()
          return
        }

        if (result.data.status === 'error') {
          oauthPollTimer = null
          reject(createOAuthError(result.data.error || result.data.message || 'OAuth认证失败'))
          return
        }
        
        const interval = attempts <= 3 ? 2000 : (attempts <= 10 ? 3000 : 4000)
        scheduleNextPoll(interval)
      } catch (error) {
        if (oauthCancelled.value) {
          oauthPollTimer = null
          reject(new Error('OAuth认证已取消'))
          return
        }
        if (error?.retryable === false) {
          oauthPollTimer = null
          reject(error)
          return
        }
        const retryInterval = Math.min(attempts * 2000, 10000)
        oauthPollTimer = null
        scheduleNextPoll(retryInterval)
      }
    }

    poll().catch(reject)
  })
}

const stopQrPolling = () => {
  qrCancelled = true
  if (qrPollTimer) {
    clearTimeout(qrPollTimer)
    qrPollTimer = null
  }
  if (qrCountdownTimer) {
    clearInterval(qrCountdownTimer)
    qrCountdownTimer = null
  }
}

const closeQrModal = () => {
  stopQrPolling()
  qrModalVisible.value = false
}

const handleQrLogin = async () => {
  if (qrLoading.value) return
  stopQrPolling()
  qrCancelled = false
  qrLoading.value = true
  qrStatus.value = 'loading'
  qrMessage.value = ''
  qrImageBase64.value = ''
  qrCountdown.value = 0
  qrModalVisible.value = true

  try {
    const resp = await fetch('/api/admin/qr-login/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ driver_type: form.value.driver_type })
    })
    const result = await resp.json()
    if (!resp.ok || !result.success) {
      throw new Error(result?.message || result?.detail || '生成二维码失败')
    }

    const data = result.data || {}
    qrStateId = data.state_id
    qrImageBase64.value = data.qr_image_base64
    qrCountdown.value = data.expires_in || 300
    qrStatus.value = 'waiting'

    qrCountdownTimer = setInterval(() => {
      if (qrCountdown.value > 0) {
        qrCountdown.value -= 1
      } else if (qrCountdownTimer) {
        clearInterval(qrCountdownTimer)
        qrCountdownTimer = null
      }
    }, 1000)

    scheduleQrPoll(1500)
  } catch (error) {
    qrStatus.value = 'failed'
    qrMessage.value = error?.message || '生成二维码失败'
    if (window.appNotification) {
      window.appNotification.error(`扫码登录失败：${qrMessage.value}`)
    }
  } finally {
    qrLoading.value = false
  }
}

const scheduleQrPoll = (delay) => {
  if (qrCancelled) return
  qrPollTimer = setTimeout(() => {
    qrPollTimer = null
    runQrPoll()
  }, delay)
}

const runQrPoll = async () => {
  if (qrCancelled || !qrStateId) return
  try {
    const url = `/api/admin/qr-login/status/${encodeURIComponent(qrStateId)}?driver_type=${encodeURIComponent(form.value.driver_type)}`
    const resp = await fetch(url)
    const result = await resp.json()
    if (!resp.ok || !result.success) {
      scheduleQrPoll(3000)
      return
    }

    const data = result.data || {}
    const status = data.status

    if (status === 'success') {
      stopQrPolling()
      qrStatus.value = 'success'
      qrMessage.value = ''

      const qrConfig = data.config && typeof data.config === 'object' ? data.config : null
      if (qrConfig) {
        config.value = { ...config.value, ...qrConfig }
      } else if (data.cookie) {
        config.value.cookie = data.cookie || ''
      }
      config.value = { ...config.value }
      await nextTick()

      if (window.appNotification) {
        window.appNotification.success('授权信息已填入表单')
      }

      setTimeout(() => {
        qrModalVisible.value = false
      }, 1200)
      return
    }

    if (status === 'expired') {
      stopQrPolling()
      qrStatus.value = 'expired'
      qrMessage.value = data.message || '二维码已过期'
      return
    }

    if (status === 'failed') {
      stopQrPolling()
      qrStatus.value = 'failed'
      qrMessage.value = data.message || '登录失败'
      return
    }

    scheduleQrPoll(2000)
  } catch (error) {
    scheduleQrPoll(3000)
  }
}

const submitForm = async () => {
  if (!validateStep2()) return
  
  loading.value = true
  
  try {
    // 处理配置数据，将空字符串转换为null
    const processedConfig = { ...config.value }
    Object.keys(processedConfig).forEach(key => {
      if (processedConfig[key] === '') {
        processedConfig[key] = null
      }
    })
    
    const submitData = {
      name: form.value.name,
      config: processedConfig
    }
    
    let response
    if (isEditMode.value) {
      // 编辑模式
      response = await fetch(`/api/admin/accounts/${props.editAccount.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData)
      })
    } else {
      // 添加模式
      submitData.driver_type = form.value.driver_type
      response = await fetch('/api/admin/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData)
      })
    }
    
    const result = await response.json()
    
    if (result.success) {
      // 🔧 添加成功通知
      const successMessage = isEditMode.value ? '账号更新成功！' : '账号添加成功！'
      
      // 如果是编辑模式，清空下载模式缓存
      if (isEditMode.value && props.editAccount) {
        await clearDownloadModeCache(props.editAccount.id)
      }
      
      if (window.appNotification) {
        window.appNotification.success(successMessage)
      }
      emit('success', successMessage)
      close()
    } else {
      // 🔧 添加错误通知（后端已返回完整友好文案，前端不再追加“操作失败:”前缀）
      const errorMessage = result.message || '操作失败'
      if (window.appNotification) {
        window.appNotification.error(errorMessage)
      }
      errors.value.general = errorMessage
    }
  } catch (error) {
    console.error('提交失败:', error)
    errors.value.general = error.message || '操作失败'
  } finally {
    loading.value = false
  }
}

// 清空下载模式缓存
const clearDownloadModeCache = async (accountId) => {
  try {
    await fetch(`/api/admin/accounts/${accountId}/clear-download-cache`, {
      method: 'POST'
    })
  } catch (error) {
    console.warn('清空下载模式缓存失败:', error)
  }
}

// 监听编辑账号变化
watch(() => props.editAccount, async (newAccount) => {
  if (newAccount) {
    // 编辑模式：直接跳到第二步，并填充数据
    form.value.name = newAccount.name
    form.value.driver_type = newAccount.driver_type
    
    // 🔧 先获取驱动配置schema，然后清理不相关的配置字段
    await fetchDriverConfigSchema(newAccount.driver_type)
    
    // 只保留当前驱动支持的配置字段
    const validConfig = {}
    if (driverConfigSchema.value) {
      Object.keys(driverConfigSchema.value).forEach(fieldName => {
        if (newAccount.config[fieldName] !== undefined) {
          validConfig[fieldName] = newAccount.config[fieldName]
        }
      })
    }
    config.value = validConfig
    
    step.value = 2
  }
}, { immediate: true })

// 监听弹窗显示状态
watch(() => props.visible, (visible) => {
  if (!visible) {
    resetForm()
  } else if (!isEditMode.value) {
    // 新增模式：从第一步开始
    step.value = 1
    initializeDrivers()
  }
})

// 监听驱动列表变化
watch(drivers, () => {
  if (props.visible && !isEditMode.value) {
    initializeDrivers()
  }
}, { deep: true })



// ESC按键监听
onMounted(() => {
  const handleEsc = (event) => {
    if (event.key === 'Escape' && props.visible) {
      close()
    }
  }
  document.addEventListener('keydown', handleEsc)
  
  // 清理函数
  onUnmounted(() => {
    document.removeEventListener('keydown', handleEsc)
  })
})
</script>

<style scoped>
/* 对话框基础样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100000;
  backdrop-filter: blur(4px);
}

.dialog {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  max-width: 700px;
  width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: dialogSlideIn 0.3s ease-out;
}

.dialog-large {
  max-width: 700px;
  max-height: 90vh;
}

@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 30px;
  border-bottom: 1px solid #e9ecef;
  background: #F9FAFB;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4C74DF 0%, #02A6F0 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

/* 移除旧的步骤指示器样式 */

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f8f9fa;
  color: #495057;
}

.dialog-content {
  padding: 20px 20px 0px 20px;
  overflow: hidden;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* 第一步内容 */
.step-content {
  padding: 0;
  display: flex;
  flex-direction: column;
  min-height: auto;
  flex: 1;
}



/* 搜索容器距下12px */
.step-content .search-container {
  margin-bottom: 12px;
}

/* 搜索结果距下10px */
.step-content .search-result {
  margin-bottom: 10px;
}

/* 垂直轮播容器距下20px */
.step-content .driver-carousel-vertical {
  margin-bottom: 20px;
}

/* 移除旧的导航控件样式，现在使用内嵌箭头 */

/* 步骤操作按钮 */
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 0px;
  margin-bottom: 0px;
  padding: 20px 20px;
  flex-shrink: 0;
}

/* 带搜索框的底部操作区 */
.step-actions-with-search {
  justify-content: space-between;
  align-items: center;
}

/* 第一步的下一步按钮右对齐 */
.step-actions-with-search .btn-primary {
  margin-right: -20px; /* 补偿dialog-content的右边距，让按钮与内容区域右对齐 */
}

/* 搜索区域 */
.search-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  margin-left: -20px; /* 补偿dialog-content的左边距，让搜索框与内容区域左对齐 */
}

.view-toggle-btn {
  width: 40px;
  height: 40px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background: #fff;
  color: #4285F4;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.view-toggle-btn:hover {
  border-color: #4285F4;
  background: rgba(66, 133, 244, 0.06);
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.08);
}

/* 紧凑搜索框容器 */
.search-container-compact {
  position: relative;
  width: 240px;
  flex-shrink: 0;
}

.search-input-compact {
  width: 100%;
  padding: 10px 16px 10px 45px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.3s;
  background: white;
  height: 40px; /* 与按钮高度一致 */
}

.search-input-compact:focus {
  outline: none;
  border-color: #4285F4;
  background: white;
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
}

/* 搜索结果文字 */
.search-result-text {
  font-size: 13px;
  color: #6c757d;
  font-weight: 500;
  white-space: nowrap;
}

/* 搜索容器 */
.search-container {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 12px 16px 12px 45px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.3s;
  background: white;
}

.search-input:focus {
  outline: none;
  border-color: #4285F4;
  background: white;
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
  line-height: 0;
  display: flex;
  align-items: center;
  pointer-events: none;
}

.search-clear {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #dc3545;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-result {
  text-align: center;
  color: #6c757d;
  font-size: 14px;
}

/* 垂直驱动轮播 */
.driver-carousel-vertical {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
  border-radius: 12px;
  margin-bottom: 0;
}

.driver-card-grid-view {
  width: 100%;
  min-height: 180px;
  max-height: 236px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-auto-rows: 66px;
  align-content: start;
  gap: 10px;
  margin-bottom: 20px;
  padding-right: 2px;
}

.driver-mini-card {
  height: 66px;
  min-height: 66px;
  border: 1px solid #e4eaf0;
  border-radius: 11px;
  background: #fbfcfe;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  text-align: left;
  overflow: hidden;
}

.driver-mini-card:hover {
  border-color: #d3dfeb;
  background: #fff;
  box-shadow: 0 5px 16px rgba(44, 62, 80, 0.08);
}

.driver-mini-card.selected {
  border-color: #4285F4;
  background: linear-gradient(135deg, rgba(66, 133, 244, 0.035) 0%, rgba(66, 133, 244, 0.075) 100%);
  box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.08);
}

.driver-mini-card.selected:hover {
  border-color: #4285F4;
  box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.08);
}

.driver-mini-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.driver-mini-name {
  min-width: 0;
  color: #2c3e50;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.driver-empty-state {
  grid-column: 1 / -1;
  min-height: 180px;
  border: 2px dashed #d7dee6;
  border-radius: 12px;
  color: #8a96a3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.driver-carousel-track-vertical {
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  position: relative;
  width: 100%;
}

.driver-carousel-item-vertical {
  height: 180px; /* 固定高度与容器一致 */
  width: 100%;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  position: relative;
}

.driver-card-vertical {
  width: 100%;
  height: 100%;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  padding: 24px;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}

.driver-card-vertical:hover {
  border-color: #4285F4;
  box-shadow: 0 4px 24px rgba(66, 133, 244, 0.12);
  background: #ffffff;
}

.driver-card-vertical.selected {
  border-color: #4285F4;
  background: linear-gradient(135deg, rgba(66, 133, 244, 0.03) 0%, rgba(66, 133, 244, 0.06) 100%);
}

/* 左侧内容区域 */
.driver-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20px;
}

.driver-icon-large {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 600;
  font-size: 18px;
  color: white;
  text-transform: uppercase;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.driver-info {
  flex: 1;
}

.driver-info h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.driver-info p {
  margin: 0;
  color: #6c757d;
  font-size: 13px;
  line-height: 1.4;
}

/* 右侧控制区域 */
.driver-controls-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding-left: 20px;
  opacity: 0.7;
  transition: opacity 0.3s ease;
}

.driver-card-vertical:hover .driver-controls-right {
  opacity: 1;
}

/* 位置指示器 */
.position-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #4285F4;
  min-width: 20px;
}

.position-text {
  font-size: 14px;
  font-weight: 700;
  color: #4285F4;
  line-height: 1;
}

.position-divider {
  width: 12px;
  height: 1px;
  background: rgba(66, 133, 244, 0.4);
  margin: 2px 0;
}

.total-text {
  font-size: 11px;
  font-weight: 500;
  color: rgba(66, 133, 244, 0.7);
  line-height: 1;
}



/* 垂直箭头按钮 */
.nav-arrow {
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #4285F4;
  font-size: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-arrow:hover {
  background: rgba(66, 133, 244, 1);
  color: white;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}



/* 导航控件 */
.driver-navigation {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 8px;
}

.driver-indicators {
  display: flex;
  gap: 12px;
}

.nav-button {
  background: none;
  border: none;
  color: rgba(0, 0, 0, 0.4);
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}

.nav-button:hover {
  color: rgba(0, 0, 0, 0.7);
}

.nav-button:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.driver-indicator {
  position: relative;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e9ecef;
  cursor: pointer;
  transition: all 0.3s;
}

.driver-indicator:hover {
  background: #4285F4;
  transform: scale(1.3);
}

.driver-indicator.active {
  background: #4285F4;
  transform: scale(1.4);
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.2);
}

.indicator-tooltip {
  position: absolute;
  bottom: 130%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s;
  z-index: 20;
}

.driver-indicator:hover .indicator-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-3px);
}

/* 清理旧样式 - 已合并到上面的简洁设计中 */

/* 导航控件 */
.driver-navigation {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 8px;
}

.driver-indicators {
  display: flex;
  gap: 12px;
}

.nav-button {
  background: none;
  border: none;
  color: rgba(0, 0, 0, 0.4);
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}

.nav-button:hover {
  color: rgba(0, 0, 0, 0.7);
}

.nav-button:active {
  color: rgba(0, 0, 0, 0.8);
}

.nav-button:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.nav-button:disabled:hover {
  color: rgba(0, 0, 0, 0.4);
}

.driver-indicator {
  position: relative;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e9ecef;
  cursor: pointer;
  transition: all 0.3s;
}

.driver-indicator:hover {
  background: #4285F4;
  transform: scale(1.3);
}

.driver-indicator.active {
  background: #4285F4;
  transform: scale(1.4);
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.2);
}

.indicator-tooltip {
  position: absolute;
  bottom: 130%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s;
  z-index: 20;
}

.indicator-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.8);
}

.driver-indicator:hover .indicator-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-3px);
}

.step-content h4 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.step-description {
  margin: 0 0 30px 0;
  color: #6c757d;
  font-size: 14px;
}

.dialog-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 10px 20px 20px 20px;
}

.form-group {
  margin-bottom: 20px;
}

/* 重置网格中所有form-group的间距，让grid gap控制 */
.config-fields .form-group {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

/* 已移动到上面，统一设置为12px */

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #374151;
  font-size: 13px;
}

.required {
  color: #ef4444;
}

.form-input-with-action {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.form-input-with-action .form-input {
  flex: 1;
}

.form-input-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 14px;
  height: 40px;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}

.form-input-action-btn:hover {
  filter: brightness(1.05);
}

.form-input-action-btn:active {
  filter: brightness(0.95);
}

.form-input,
.form-select,
textarea.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.4;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
  height: 40px; /* 统一精确高度 */
}

/* select特殊处理 */
.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 8px center;
  background-repeat: no-repeat;
  background-size: 16px;
  padding-right: 36px;
}

/* textarea特殊样式 */
textarea.form-input {
  resize: vertical;
  height: 60px;
  min-height: 60px;
  margin: 0; /* 重置浏览器默认margin */
  display: block; /* 确保块级显示 */
  vertical-align: top; /* 避免基线对齐问题 */
}



.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #4C74DF;
  box-shadow: 0 0 0 2px rgba(76, 116, 223, 0.1);
}

.form-input.readonly {
  background-color: #f8fafc;
  color: #64748b;
  cursor: not-allowed;
}

.form-input.error,
.form-select.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.1);
}

.error-message {
  margin: 4px 0 0 0 !important;
  font-size: 11px;
  color: #ef4444;
  line-height: 1.2;
  padding: 0 !important;
  display: block;
}



.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #4C74DF 0%, #02A6F0 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #3b5bdb, #1e88e5);
  box-shadow: 0 4px 12px rgba(76, 116, 223, 0.4);
}

.btn-secondary {
  background: #fff;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}

.btn-secondary:hover {
  background: #f8fafc;
}

/* 驱动选择列表 - 简洁单列，自然排列 */
.driver-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

/* 驱动容器 */
.driver-container {
  position: relative;
}

.driver-card {
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 15px;
  position: relative;
  width: 100%;
}

.driver-card:hover {
  background-color: #f8f9fa;
}

.driver-card.selected {
  border-color: #4C74DF;
  background: linear-gradient(135deg, rgba(76, 116, 223, 0.05) 0%, rgba(2, 166, 240, 0.05) 100%);
}

.driver-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 600;
  font-size: 14px;
  color: white;
  text-transform: uppercase;
}

.driver-info {
  flex: 1;
  text-align: left;
}

.driver-info h5 {
  margin: 0 0 4px 0;
  color: #2c3e50;
  font-size: 14px;
  font-weight: 600;
}

.driver-info p {
  margin: 0;
  color: #6c757d;
  font-size: 12px;
  line-height: 1.3;
}

.driver-check {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.driver-check i {
  width: 20px;
  height: 20px;
  background: #28a745;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

/* 配置表单 */
.config-form {
  margin-top: 0;
  padding-top: 0;
}

.config-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;
  margin-bottom: 0;
}

.config-fields-row-half {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 20px;
  align-items: start;
}

.config-fields-row-full {
  display: block;
}

.config-fields-row-full .form-group.full-width {
  width: 100%;
}

/* 滚动条美化 */
.config-fields::-webkit-scrollbar {
  width: 6px;
}

.config-fields::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.config-fields::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.config-fields::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 对话框内容区域滚动条美化 */
.dialog-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 直接重置包含 textarea 的全宽 form-group */
.config-fields .form-group.full-width {
  margin: 0 !important;
  padding: 0 !important;
}

/* 删除重复规则，已在上面统一处理 */

.config-form .config-fields {
  margin-top: 0;
}

/* OAuth按钮样式 */
.btn-oauth {
  background: #4C74DF;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-left: -20px; /* 补偿dialog-content的左边距，让按钮与内容区域左对齐 */
}

.btn-oauth:hover:not(:disabled) {
  background: #3d5bc7;
}

.btn-oauth:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 步骤操作区域布局 */
.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.step-actions-left {
  display: flex;
  align-items: center;
  margin-left: 0; /* 确保与表单字段左边距对齐 */
}

.step-actions-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-right: -20px; /* 补偿dialog-content的右边距，让按钮与内容区域右对齐 */
}

.qr-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100010;
  backdrop-filter: blur(4px);
}

.qr-panel {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  width: 360px;
  max-width: 92vw;
  display: flex;
  flex-direction: column;
  animation: dialogSlideIn 0.2s ease-out;
}

.qr-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #e9ecef;
  background: #F9FAFB;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.qr-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
}

.qr-panel-title i {
  color: #4C74DF;
}

.qr-panel-body {
  padding: 24px 20px;
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  color: #374151;
  font-size: 13px;
  width: 100%;
}

.qr-state > i {
  font-size: 40px;
}

.qr-state-loading i {
  color: #4C74DF;
}

.qr-state-success i {
  color: #10b981;
}

.qr-state-expired i {
  color: #d97706;
}

.qr-state-failed i {
  color: #ef4444;
}

.qr-image {
  width: 220px;
  height: 220px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  padding: 8px;
  box-sizing: border-box;
}

.qr-hint {
  color: #4b5563;
  font-size: 13px;
  line-height: 1.5;
}

.qr-hint strong {
  color: #2c3e50;
}

.qr-countdown {
  color: #6b7280;
  font-size: 12px;
}

.qr-result-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .dialog-large {
    width: 95%;
    margin: 20px;
  }
  
  .step-indicator {
    gap: 10px;
  }
  
  .step-line {
    width: 30px;
  }
  
  .driver-grid {
    grid-template-columns: 1fr;
  }

  .driver-card-grid-view {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .search-area {
    margin-left: 0;
    width: 100%;
  }

  .search-container-compact {
    width: 100%;
  }
  
  .form-row,
  .config-fields-row-half {
    grid-template-columns: 1fr;
  }
  
  .step-actions {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .step-actions-left,
  .step-actions-right {
    justify-content: center;
  }
}
</style> 
