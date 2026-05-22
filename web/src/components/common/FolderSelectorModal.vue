<template>
  <div class="folder-selector-shell">
    <div class="folder-selector-modal-header">
      <h3 class="folder-selector-modal-title">{{ title }}</h3>
      <button type="button" class="folder-selector-modal-close" @click="$emit('cancel')" aria-label="关闭">×</button>
    </div>

    <div class="folder-selector-content">
      <nav class="breadcrumb" style="margin-bottom:2px;">
        <span
          class="breadcrumb-item"
          :class="{ active: pathHistory.length === 1 }"
          data-idx="0"
          @click="navigateToIndex(0)"
        ><span class="breadcrumb-item-label">根目录</span></span>

        <template v-if="hiddenBreadcrumbItems.length">
          <div
            class="breadcrumb-ellipsis-dropdown"
            @mouseenter="openDropdown"
            @mouseleave="scheduleCloseDropdown"
          >
            <span class="breadcrumb-ellipsis" @click.stop="toggleDropdown">...</span>
            <div v-if="dropdownOpen" class="breadcrumb-dropdown">
              <div
                v-for="item in hiddenBreadcrumbItems"
                :key="item.index"
                class="breadcrumb-dropdown-item"
                :title="item.name"
                @click.stop="selectHiddenBreadcrumb(item.index)"
              >
                {{ item.name }}
              </div>
            </div>
          </div>
        </template>

        <template v-for="item in trailingBreadcrumbItems" :key="item.index">
          <span
            class="breadcrumb-item"
            :class="{ active: item.index === pathHistory.length - 1 }"
            :data-idx="item.index"
            :title="item.name"
            @click="navigateToIndex(item.index)"
          ><span class="breadcrumb-item-label">{{ item.name }}</span></span>
        </template>
      </nav>

      <div id="move-folder-list" class="file-list" style="margin-bottom:0;">
        <div v-if="showCreateInput" class="file-row move-folder-input folder-row">
          <i class="icon"><SvgIcon name="folder" :size="18" /></i>
          <input
            ref="newFolderInputRef"
            v-model.trim="newFolderName"
            type="text"
            class="file-name move-folder-inputbox"
            placeholder="输入文件夹名称"
            maxlength="100"
            :disabled="creatingFolder"
            @keyup.enter="createFolder"
            @keyup.esc="cancelCreateFolder"
          >
          <button type="button" class="folder-inline-btn confirm" :disabled="creatingFolder" @click="createFolder">
            <i class="fas fa-check"></i>
          </button>
          <button type="button" class="folder-inline-btn cancel" :disabled="creatingFolder" @click="cancelCreateFolder">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div v-if="loading" class="folder-state">加载中...</div>
        <div v-else-if="errorMessage" class="folder-state error">{{ errorMessage }}</div>
        <div v-else-if="!visibleDirectories.length" class="folder-state">没有子目录</div>
        <div
          v-for="dir in visibleDirectories"
          v-else
          :key="dir.id"
          class="file-row move-folder-item folder-row"
          :title="dir.name"
          @click="openDirectory(dir)"
        >
          <i class="icon"><SvgIcon name="folder" :size="18" /></i>
          <span class="file-name">{{ dir.name }}</span>
        </div>
      </div>
    </div>

    <div class="folder-selector-modal-footer">
      <button
        v-if="allowCreateFolder"
        type="button"
        class="folder-selector-secondary-btn"
        :disabled="loading || creatingFolder"
        @click="showCreateFolderInput"
      >
        <i class="fas fa-folder-plus"></i>
        新建文件夹
      </button>
      <button
        type="button"
        class="folder-selector-secondary-btn"
        :disabled="loading || creatingFolder"
        @click="refreshCurrentDirectory"
      >
        <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
        刷新
      </button>
      <div class="folder-selector-footer-spacer" aria-hidden="true"></div>
      <button type="button" class="folder-selector-confirm-btn" :disabled="loading || creatingFolder" @click="selectCurrent">
        <i class="fas fa-check"></i>
        {{ confirmText }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import axios from 'axios'
import SvgIcon from '../icons/SvgIcon.vue'

const props = defineProps({
  accountId: {
    type: [Number, String],
    required: true
  },
  title: {
    type: String,
    default: '选择目录'
  },
  confirmText: {
    type: String,
    default: '选择当前目录'
  },
  rootId: {
    type: [Number, String],
    default: '0'
  },
  excludedFolderIds: {
    type: Array,
    default: () => []
  },
  allowCreateFolder: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['resolve', 'cancel'])

const loading = ref(false)
const creatingFolder = ref(false)
const errorMessage = ref('')
const directories = ref([])
const currentPath = ref('root')
const currentDisplayPath = ref('/')
const pathHistory = ref([{ id: 'root', name: '根目录' }])
const dropdownOpen = ref(false)
const showCreateInput = ref(false)
const newFolderName = ref('')
const newFolderInputRef = ref(null)
let dropdownCloseTimer = null

const normalizedRootId = computed(() => String(props.rootId ?? '0'))
const excludedFolderIdSet = computed(() => new Set((props.excludedFolderIds || []).map(id => String(id))))
const effectiveCurrentId = computed(() => currentPath.value === 'root' ? normalizedRootId.value : currentPath.value)

const hiddenBreadcrumbItems = computed(() => {
  if (pathHistory.value.length <= 3) return []
  return pathHistory.value.slice(1, -2).map((item, offset) => ({
    ...item,
    index: offset + 1
  }))
})

const trailingBreadcrumbItems = computed(() => {
  const startIndex = hiddenBreadcrumbItems.value.length ? pathHistory.value.length - 2 : 1
  return pathHistory.value.slice(startIndex).map((item, offset) => ({
    ...item,
    index: startIndex + offset
  }))
})

const visibleDirectories = computed(() => (
  directories.value.filter(dir => !excludedFolderIdSet.value.has(String(dir.id)))
))

const updateDisplayPath = () => {
  const names = pathHistory.value.slice(1).map(item => String(item.name || '').trim()).filter(Boolean)
  const path = '/' + names.join('/')
  currentDisplayPath.value = path === '/' ? path : path.replace(/\/+$/, '')
}

const resetCreateFolderState = () => {
  showCreateInput.value = false
  newFolderName.value = ''
}

const loadDirectories = async (parentId = 'root', options = {}) => {
  loading.value = true
  errorMessage.value = ''
  dropdownOpen.value = false
  try {
    const requestParentId = parentId === 'root' ? normalizedRootId.value : String(parentId)
    const params = new URLSearchParams({ parent_id: requestParentId })
    if (options.forceRefresh) {
      params.set('force_refresh', 'true')
    }
    const response = await axios.get(`/api/cache-retention/accounts/${props.accountId}/directories?${params.toString()}`)
    if (!response.data.success) {
      throw new Error(response.data.message || '加载失败')
    }
    directories.value = response.data.data || []
  } catch (error) {
    directories.value = []
    errorMessage.value = error?.response?.data?.message || error?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const refreshCurrentDirectory = async () => {
  resetCreateFolderState()
  await loadDirectories(currentPath.value, { forceRefresh: true })
}

const openDirectory = async (dir) => {
  currentPath.value = String(dir.id)
  pathHistory.value = [...pathHistory.value, { id: currentPath.value, name: String(dir.name) }]
  updateDisplayPath()
  resetCreateFolderState()
  await loadDirectories(currentPath.value)
}

const navigateToIndex = async (index) => {
  if (index < 0 || index >= pathHistory.value.length) return
  pathHistory.value = pathHistory.value.slice(0, index + 1)
  currentPath.value = pathHistory.value[index].id
  updateDisplayPath()
  resetCreateFolderState()
  await loadDirectories(currentPath.value)
}

const clearDropdownTimer = () => {
  if (dropdownCloseTimer) {
    clearTimeout(dropdownCloseTimer)
    dropdownCloseTimer = null
  }
}

const openDropdown = () => {
  clearDropdownTimer()
  dropdownOpen.value = true
}

const scheduleCloseDropdown = () => {
  clearDropdownTimer()
  dropdownCloseTimer = setTimeout(() => {
    dropdownOpen.value = false
  }, 120)
}

const toggleDropdown = () => {
  clearDropdownTimer()
  dropdownOpen.value = !dropdownOpen.value
}

const selectHiddenBreadcrumb = async (index) => {
  dropdownOpen.value = false
  await navigateToIndex(index)
}

const showCreateFolderInput = () => {
  if (!props.allowCreateFolder || creatingFolder.value) {
    return
  }
  showCreateInput.value = true
}

const cancelCreateFolder = () => {
  if (creatingFolder.value) return
  resetCreateFolderState()
}

const createFolder = async () => {
  const folderName = String(newFolderName.value || '').trim()
  if (!folderName) {
    window.appNotification?.warning('请输入文件夹名称')
    return
  }
  if (folderName.length > 100) {
    window.appNotification?.warning('文件夹名称不能超过100个字符')
    return
  }
  if (visibleDirectories.value.some(dir => String(dir.name || '').toLowerCase() === folderName.toLowerCase())) {
    window.appNotification?.warning('当前目录已存在同名文件夹')
    return
  }

  creatingFolder.value = true
  try {
    const formData = new FormData()
    formData.append('account_id', props.accountId)
    formData.append('path', effectiveCurrentId.value)
    formData.append('name', folderName)

    const response = await axios.post('/api/files/create-folder', formData)
    if (!response.data?.success) {
      throw new Error(response.data?.message || '创建文件夹失败')
    }

    window.appNotification?.success(response.data?.message || '文件夹创建成功')
    const createdFolderId = String(response.data?.data?.folder_id || '')
    resetCreateFolderState()
    await loadDirectories(currentPath.value)

    const createdFolder = visibleDirectories.value.find(dir =>
      (createdFolderId && String(dir.id) === createdFolderId) ||
      String(dir.name || '').toLowerCase() === folderName.toLowerCase()
    )

    if (createdFolder) {
      await openDirectory(createdFolder)
    }
  } catch (error) {
    window.appNotification?.error(error.response?.data?.message || error.message || '创建文件夹失败')
  } finally {
    creatingFolder.value = false
  }
}

const selectCurrent = () => {
  emit('resolve', {
    id: currentPath.value === 'root' ? normalizedRootId.value : currentPath.value,
    path: currentDisplayPath.value || '/'
  })
}

watch(
  () => [props.accountId, props.rootId],
  async () => {
    currentPath.value = 'root'
    currentDisplayPath.value = '/'
    pathHistory.value = [{ id: 'root', name: '根目录' }]
    resetCreateFolderState()
    await loadDirectories()
  },
  { immediate: true }
)

watch(showCreateInput, async (visible) => {
  if (visible) {
    await nextTick()
    newFolderInputRef.value?.focus()
    newFolderInputRef.value?.select?.()
  }
})
</script>

<style scoped>
.folder-selector-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  max-height: 100%;
  box-sizing: border-box;
  overflow: visible;
}

.folder-selector-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}

.folder-selector-modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.folder-selector-modal-close {
  background: none;
  border: none;
  color: #999;
  font-size: 20px;
  line-height: 1;
  width: 24px;
  height: 24px;
  padding: 0;
  cursor: pointer;
}

.folder-selector-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 20px 24px 12px;
  box-sizing: border-box;
  overflow: visible; /* 必须为 visible，否则下拉菜单会被截断 */
  position: relative;
  z-index: 1;
}

.breadcrumb {
  display: flex;
  align-items: center;
  min-height: 20px;
  height: 20px;
  margin-top: -6px !important;
  margin-bottom: 2px !important;
}

.file-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin-top: 2px !important;
  min-height: 300px !important;
  max-height: 300px !important;
  height: 300px !important;
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

/* 修复面包屑下拉菜单被模态框遮挡的问题 */
.breadcrumb-ellipsis-dropdown {
  position: relative;
  display: inline-flex;
}

.breadcrumb-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 99999;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 4px 0;
  min-width: 150px;
  max-width: 250px;
  max-height: 300px;
  overflow-y: auto;
}

.breadcrumb-dropdown-item {
  padding: 8px 16px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background-color 0.2s;
}

.breadcrumb-dropdown-item:hover {
  background-color: #f3f4f6;
}

/* 确保滚动条在各浏览器下表现良好 */
.breadcrumb-dropdown::-webkit-scrollbar {
  width: 6px;
}

.breadcrumb-dropdown::-webkit-scrollbar-track {
  background: transparent;
}

.breadcrumb-dropdown::-webkit-scrollbar-thumb {
  background-color: #D9D9D9;
  border-radius: 3px;
}

.folder-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 10px;
  font-size: 14px;
  line-height: 1.8;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  min-width: 0;
}

.move-folder-input {
  background: transparent;
}

.move-folder-inputbox {
  flex: 1;
  min-width: 0;
  border: 1px solid #2196F3;
  background: #fff;
  font-size: 14px;
  padding: 0 12px;
  color: #333;
  transition: border 0.2s;
  border-radius: 8px;
  height: 32px;
  box-sizing: border-box;
}

.folder-inline-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.folder-inline-btn.confirm {
  background: #2196F3;
}

.folder-inline-btn.cancel {
  background: #D1D5DB;
}

.folder-state {
  padding: 20px;
  text-align: center;
  color: #666;
}

.folder-state.error {
  color: #dc2626;
}

.folder-selector-modal-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  flex-shrink: 0;
  padding: 0 24px 24px;
}

.folder-selector-footer-spacer {
  flex: 1;
}

.folder-selector-secondary-btn,
.folder-selector-confirm-btn {
  height: 38px;
  border-radius: 10px;
  padding: 0 16px;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.folder-selector-secondary-btn {
  background: #fff;
  color: #475569;
  border: 1px solid #dbe3ee;
}

.folder-selector-confirm-btn {
  min-width: 140px;
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  color: #fff;
}

.folder-selector-secondary-btn:disabled,
.folder-selector-confirm-btn:disabled,
.folder-inline-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
