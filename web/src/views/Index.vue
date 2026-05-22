<template>
  <div class="index-page">
    <!-- 文件操作加载遮罩 -->
    <div v-if="operationLoading" class="operation-loading-overlay">
      <div class="operation-loading-content">
        <div class="loading-spinner"></div>
        <div class="loading-text">{{ operationMessage }}</div>
      </div>
    </div>
    <!-- 顶部导航 -->
    <div class="header">
      <div class="content-container-fluid">
        <div class="header-content">
          <h1>
            <div class="logo-container">
              <img src="/static/img/logo.png" alt="LitePan" class="logo">
              <span v-if="isAdmin" class="admin-indicator">管理员</span>
              <span v-else-if="mustChangePassword" class="admin-indicator warning">需改密</span>
            </div>
          </h1>
          <div class="header-actions">
            <div id="auth-buttons">
              <template v-if="mustChangePassword">
                <a href="/admin" class="btn btn-warning">立即改密码</a>
                <button @click="handleLogout" class="btn btn-logout">退出登录</button>
              </template>
              <template v-else-if="isAdmin">
                <a href="/admin" class="btn">管理后台</a>
                <button @click="handleLogout" class="btn btn-logout">退出登录</button>
              </template>
              <router-link v-else to="/login" class="btn">管理员登录</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <div class="content-container-fluid">
        <IndexTopNav
          :dropdown-open="dropdownOpen"
          :selected-account-id="selectedAccountId"
          :selected-account-name="selectedAccountName"
          :active-accounts="activeAccounts"
          :breadcrumb-items="breadcrumbItems"
          :max-breadcrumb-items="maxBreadcrumbItems"
          :hidden-breadcrumb-items="hiddenBreadcrumbItems"
          :visible-last-items="visibleLastItems"
          :account-switch-mode="accountSwitchMode"
          @toggle-dropdown="toggleDropdown"
          @select-account="selectAccount"
          @navigate-to-path="navigateToPath"
        />

        <div
          v-if="floatingAccountSwitchEnabled"
          class="floating-account-switcher"
          aria-label="账号切换"
        >
          <button
            v-for="account in activeAccounts"
            :key="account.id"
            type="button"
            class="floating-account-btn"
            :class="{ active: String(selectedAccountId) === String(account.id), 'has-logo': !!account.driver_card_logo }"
            :style="{ '--driver-color': getFloatingAccountColor(account) }"
            @click="selectAccount(account)"
          >
            <img
              v-if="account.driver_card_logo"
              :src="account.driver_card_logo"
              class="floating-account-logo"
              :alt="account.driver_card_name || account.name"
            >
            <span v-else class="floating-account-icon">{{ getFloatingAccountText(account) }}</span>
            <span class="floating-account-tooltip">{{ account.name }}</span>
          </button>
        </div>

      <!-- 工具栏和文件列表框架 -->
      <div class="main-frame">
        <FileToolbar
          :is-admin="isAdmin"
          :selected-files-count="selectedFiles.size"
          :view-mode="fileViewMode"
          :response-time="responseTime"
          :cache-rate="cacheRate"
          :upload-task-count="displayUploadTasks.length"
          :upload-task-active="activeUploadTasks.length > 0"
          :upload-task-failed="displayUploadTasks.some(task => task.status === 'failed')"
          :upload-task-success="displayUploadTasks.some(task => task.status === 'success')"
          :upload-task-title="uploadTaskTitle"
          :upload-task-label="uploadTaskLabel"
          @create-folder="startInlineCreateFolder"
          @upload-file="handleUploadFile"
          @upload-folder="handleUploadFolder"
          @refresh="handleRefreshClick"
          @batch-move="batchMove"
          @batch-copy="batchCopy"
          @batch-delete="batchDelete"
          @update:view-mode="handleViewModeChange"
          @open-upload-tasks="openUploadTaskPanel"
        />

        <FileTable
          :is-admin="isAdmin"
          :selected-account-id="selectedAccountId"
          :loading="loading"
          :files="files"
          :sorted-files="sortedFiles"
          :selected-files-count="selectedFiles.size"
          :selected-files-list="selectedFilesList"
          :sort-key="sortKey"
          :sort-order="sortOrder"
          :view-mode="fileViewMode"
          :rename-file-inline="renameFileInline"
          :create-folder-request="createFolderRequest"
          :create-folder-inline="createFolderInline"
          :delete-file-inline="deleteFileInline"
          :move-file-inline="moveFileInline"
          :copy-file-inline="copyFileInline"
          @update:selected-files-list="selectedFilesList = $event"
          @sort-by="sortBy"
          @set-sort="handleSetSort"
          @file-click="handleFileClick"
          @download-file="handleFileDownload"
          @rename-file="renameFile"
          @delete-file="deleteFile"
          @move-file="moveFile"
          @copy-file="copyFile"
          @generate-current-strm="generateCurrentDirectoryStrm"
        />

        <FilePreviewModal
          :visible="previewVisible"
          :files="previewFiles"
          :current-index="previewIndex"
          :account-id="selectedAccountId"
          @close="closeFilePreview"
          @previous="showPreviousPreview"
          @next="showNextPreview"
          @download="handleFileDownload"
        />
      </div>
      </div>
    </div>

    <!-- 页脚 -->
    <div class="footer">
      <div class="content-container-fluid">
        <p>
          2026 LitePan. {{ appVersion }}
          <span class="collab-divider">×</span>
          <a
            class="footer-link"
            href="https://haoyongzhai.com/"
            target="_blank"
            rel="noopener noreferrer"
          >
            好用斋
          </a>
          联合发布
        </p>
      </div>
    </div>



    <!-- 消息通知容器 -->
    <div id="message-container"></div>

    <input
      ref="uploadFileInput"
      type="file"
      multiple
      style="display: none"
      @change="handleUploadFileChange"
    >

    <input
      ref="uploadFolderInput"
      type="file"
      webkitdirectory
      directory
      multiple
      style="display: none"
      @change="handleUploadFolderChange"
    >

    <div v-if="uploadTaskPanelOpen" class="upload-task-panel">
      <div class="upload-task-panel-header">
        <span>任务面板</span>
        <div class="upload-task-panel-actions">
          <button
            type="button"
            class="upload-task-header-info-btn"
            title="查看上传说明"
            @click="openUploadNoticeFromPanel"
          >
            !
          </button>
          <button type="button" class="upload-task-close-btn" @click="closeUploadTaskPanel" aria-label="关闭">×</button>
        </div>
      </div>
      <div class="upload-task-panel-body">
        <div class="upload-task-layout">
          <div class="upload-task-sidebar">
            <button
              type="button"
              class="upload-task-nav-item active"
            >
              <span class="upload-task-nav-icon"><SvgIcon name="upload" :size="16" /></span>
              <span>上传任务</span>
            </button>
          </div>

          <div class="upload-task-content">
            <div class="upload-task-toolbar">
              <div class="upload-task-batch-actions">
                <button
                  v-if="uploadTaskView === 'running'"
                  type="button"
                  class="task-toolbar-btn"
                  :class="{ primary: batchToggleMode === 'resume' }"
                  :disabled="!canBatchToggle"
                  :title="batchToggleTitle"
                  @click="handleBatchToggle"
                >
                  <span class="task-btn-icon">
                    <SvgIcon :name="batchToggleMode === 'pause' ? 'pause' : 'play'" :size="14" />
                  </span>
                  {{ batchToggleLabel }}
                </button>
                <button
                  type="button"
                  class="task-toolbar-btn danger"
                  :disabled="!canBatchDelete"
                  :title="canBatchDelete ? '删除当前页签中的任务' : '当前没有可删除的任务'"
                  @click="handleBatchDelete"
                >
                  <span class="task-btn-icon"><SvgIcon name="trash-button" :size="14" /></span>
                  {{ batchDeleteLabel }}
                </button>
              </div>
              <div class="upload-task-tabs">
                <button
                  type="button"
                  class="upload-task-tab"
                  :class="{ active: uploadTaskView === 'running' }"
                  @click="uploadTaskView = 'running'"
                >
                  进行中
                  <span class="upload-task-tab-count">{{ runningUploadTasks.length }}</span>
                </button>
                <button
                  type="button"
                  class="upload-task-tab"
                  :class="{ active: uploadTaskView === 'completed' }"
                  @click="uploadTaskView = 'completed'"
                >
                  已完成
                  <span class="upload-task-tab-count">{{ completedUploadTasks.length }}</span>
                </button>
              </div>
            </div>

            <div v-if="uploadTaskPanelLoading" class="upload-task-loading-state">
              <div class="loading-spinner"></div>
              <div class="upload-task-loading-text">{{ uploadTaskPanelLoadingText }}</div>
            </div>

            <div v-else-if="filteredUploadTasks.length > 0" class="upload-task-list">
              <div
                v-for="task in filteredUploadTasks"
                :key="task.task_id"
                class="upload-task-item"
                :class="{ completed: ['success', 'skipped'].includes(task.status) }"
              >
                <div class="upload-task-item-main">
                  <DriverIcon
                    class="upload-task-file-icon"
                    :logo="getUploadTaskDriverBadge(task).logo"
                    :color="getUploadTaskDriverBadge(task).color"
                    :name="getUploadTaskDriverBadge(task).name"
                    :title="getUploadTaskDriverBadge(task).title"
                    size="badge"
                  />
                  <div class="upload-task-file-info">
                    <div class="upload-task-title-row">
                      <span class="upload-task-name" :title="task.file_name">{{ task.file_name }}</span>
                      <span
                        v-if="['success', 'skipped'].includes(task.status)"
                        class="upload-task-status"
                        :class="`status-${task.status}`"
                      >
                        {{ getUploadTaskStatusText(task.status) }}
                      </span>
                    </div>
                    <div v-if="shouldShowUploadTaskProgressBar(task)" class="upload-task-progress-bar">
                      <div class="upload-task-progress-inner" :style="{ width: `${task.progress || 0}%` }"></div>
                    </div>
                    <div v-if="!['success', 'skipped', 'failed'].includes(task.status)" class="upload-task-meta">
                      <span>{{ getUploadTaskMessage(task) }}</span>
                      <span v-if="shouldShowUploadTaskMetaPercent(task)">{{ task.progress || 0 }}%</span>
                    </div>
                    <div v-if="task.error" class="upload-task-error">{{ task.error }}</div>
                  </div>
                </div>
                <div class="upload-task-item-actions">
                  <button
                    type="button"
                    class="task-row-btn"
                    :disabled="!canHandleUploadTaskPrimaryAction(task)"
                    :title="getUploadTaskPrimaryActionTitle(task)"
                    @click="handleUploadTaskPrimaryAction(task)"
                  >
                    <i :class="getUploadTaskPrimaryActionIconClass(task)" class="task-btn-icon font-icon"></i>
                  </button>
                  <button
                    type="button"
                    class="task-row-btn danger"
                    :disabled="!canDeleteUploadTask(task)"
                    :title="canDeleteUploadTask(task) ? '删除任务' : '当前不可删除'"
                    @click="handleDeleteUploadTask(task)"
                  >
                    <i class="fas fa-trash task-btn-icon font-icon"></i>
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="upload-task-empty">
              <div class="upload-task-empty-text">{{ uploadTaskEmptyText }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 全局加载遮罩 -->
    <div v-if="globalLoading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner loading-large"></div>
        <div class="loading-text">加载中...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useModal } from '../composables/useModal.js'
import { useIndexFileActions } from '../composables/useIndexFileActions.js'
import IndexTopNav from '../components/index/IndexTopNav.vue'
import FileToolbar from '../components/index/FileToolbar.vue'
import FileTable from '../components/index/FileTable.vue'
import FilePreviewModal from '../components/index/FilePreviewModal.vue'
import SvgIcon from '../components/icons/SvgIcon.vue'
import DriverIcon from '../components/common/DriverIcon.vue'
import UploadNoticeDialog from '../components/index/UploadNoticeDialog.vue'
import UploadConflictDialog from '../components/index/UploadConflictDialog.vue'
import { APP_VERSION } from '../constants/app'
import { canPreviewFile, getPreviewKind, getPreviewableFiles } from '../utils/fileTypes.js'

const { confirm, form, custom, closeModal } = useModal()
import axios from 'axios'

const appVersion = APP_VERSION
const router = useRouter()

// 响应式数据
const accounts = ref([])
const selectedAccountId = ref(null)
const selectedAccountName = ref('')
const LAZY_FOLDER_SIZE_DRIVER = '115_open'
const dropdownOpen = ref(false)
const files = ref([])
const loading = ref(false)
const globalLoading = ref(false)
const operationLoading = ref(false)  // 文件操作加载状态
const operationMessage = ref('正在处理文件操作...')  // 操作提示信息
const uploadFileInput = ref(null)
const uploadFolderInput = ref(null)
const uploadTasks = ref([])
const localUploadTasks = ref([])
const uploadTaskPanelOpen = ref(false)
const uploadTaskView = ref('running')
const uploadTaskPanelLoading = ref(false)
const uploadTaskPanelLoadingText = ref('正在准备上传任务...')
const uploadTaskOrderMap = ref({})
let uploadTaskPollingTimer = null
let uploadTaskEventSource = null
let uploadTaskSseReconnectTimer = null
const localUploadTaskControllers = new Map()
const localUploadTaskPayloads = new Map()
const uploadTaskMetaCache = new Map()
const canceledLocalUploadTaskIds = new Set()
const pausedLocalUploadTaskIds = new Set()
const localDispatchingTaskIds = new Set()
const pendingRemoteResumeTaskIds = new Set()
const hiddenUploadTaskKeys = new Set()
const batchPauseInProgress = ref(false)
let singleDeleteWithFileChain = Promise.resolve()
let uploadTaskOrderCounter = 0
const uploadTaskServerConcurrency = ref(3)
const publicIndexEnabled = ref(true)
const accountSwitchMode = ref('dropdown')
let uploadTaskSchedulerRunning = false



// 操作提示信息映射
const operationMessages = {
  create_folder: '正在创建文件夹...',
  delete_file: '正在删除文件...',
  delete_folder: '正在删除文件夹...',
  rename_file: '正在重命名文件...',
  rename_folder: '正在重命名文件夹...',
  move: '正在移动项目...',
  move_file: '正在移动文件...',
  move_folder: '正在移动文件夹...',
  batch_delete: '正在删除项目...',
  upload_file: '正在上传文件...',
  download_file: '正在准备下载...',
  copy_file: '正在复制文件...',
  copy_folder: '正在复制文件夹...'
}

// 统一的操作加载管理
const setOperationLoading = (isLoading, operationType = null, customMessage = null, itemName = null) => {
  operationLoading.value = isLoading
  if (isLoading) {
    if (customMessage) {
      operationMessage.value = customMessage
    } else if (operationType && operationMessages[operationType]) {
      let message = operationMessages[operationType]
      // 如果提供了项目名称，追加到提示信息中
      if (itemName) {
        message = message.replace('...', ` "${itemName}"...`)
      }
      operationMessage.value = message
    } else {
      operationMessage.value = '正在处理文件操作...'
    }
  }
}
const isAdmin = ref(false)
const mustChangePassword = ref(false)
const selectedFiles = ref(new Set())
const selectedFilesList = ref([])
const createFolderRequest = ref(0)
const currentPath = ref('0')
const breadcrumbItems = ref([{ name: '根目录', path: '0' }])
const maxBreadcrumbItems = ref(4)
const sortKey = ref('name')
const sortOrder = ref('asc')
const fileViewMode = ref('list')
const responseTime = ref('-')
const cacheRate = ref('-')
const previewVisible = ref(false)
const previewFiles = ref([])
const previewIndex = ref(0)
const FILE_VIEW_MODE_STORAGE_KEY = 'litepan:index:file-view-mode'
const UPLOAD_NOTICE_STORAGE_KEY = 'litepan:index:upload-server-transfer-notice-hidden'

// 计算属性
const activeAccounts = computed(() => {
  // 只显示启用的账号，兼容 SQLite 的 0/1 和接口序列化后的布尔值。
  return accounts.value.filter(account => account.is_active === 1 || account.is_active === true || account.enabled === 1 || account.enabled === true)
})

const firstActiveAccount = computed(() => {
  // 获取第一个启用账号（后端已排序，默认账号通常在第一位）
  return activeAccounts.value[0] || null
})

const floatingAccountSwitchEnabled = computed(() => (
  accountSwitchMode.value === 'floating' && activeAccounts.value.length > 1
))

const selectedAccountDriverType = computed(() => {
  const account = accounts.value.find(item => String(item.id) === String(selectedAccountId.value))
  return String(account?.driver_type || '').trim().toLowerCase()
})

const usesLazyFolderSizes = () => selectedAccountDriverType.value === LAZY_FOLDER_SIZE_DRIVER

const mergeFolderSizeEntries = (fileList, entries) => {
  if (!entries || !Object.keys(entries).length) return fileList
  return fileList.map(file => {
    if (!file.is_dir) return file
    const entry = entries[String(file.id)]
    if (!entry) return file
    return {
      ...file,
      size: entry.size ?? file.size,
      modified: entry.modified ?? file.modified
    }
  })
}

const applyCachedFolderSizes = async (accountId, path) => {
  if (!usesLazyFolderSizes()) return
  const folderIds = (files.value || [])
    .filter(file => file.is_dir && (!Number(file.size) || Number(file.size) <= 0))
    .map(file => String(file.id))
  if (!folderIds.length) return

  try {
    const response = await axios.post('/api/files/folder-sizes', {
      account_id: accountId,
      parent_id: path,
      file_ids: folderIds,
      fetch_missing: false
    })
    if (String(selectedAccountId.value) !== String(accountId) || currentPath.value !== path) return
    if (!response.data?.success) return
    files.value = mergeFolderSizeEntries(files.value, response.data.data || {})
  } catch (error) {
    console.debug('读取已缓存文件夹大小失败:', error)
  }
}

const fetchFolderSizeOnEnter = async (accountId, parentId, folderId) => {
  if (!usesLazyFolderSizes() || !folderId) return
  try {
    await axios.post('/api/files/folder-sizes', {
      account_id: accountId,
      parent_id: parentId,
      file_ids: [String(folderId)],
      fetch_missing: true
    })
  } catch (error) {
    console.debug('获取文件夹大小失败:', error)
  }
}

const getUploadTaskStableKey = (task) => String(task?.client_task_id || task?.task_id || '')

const ensureUploadTaskDisplayOrder = (task) => {
  const taskKey = getUploadTaskStableKey(task)
  if (!taskKey || uploadTaskOrderMap.value[taskKey]) {
    return
  }
  const preferredOrder = Number(task?.queue_order || 0)
  const nextOrder = preferredOrder > 0 ? preferredOrder : uploadTaskOrderCounter + 1
  uploadTaskOrderCounter = Math.max(uploadTaskOrderCounter, nextOrder)
  uploadTaskOrderMap.value = {
    ...uploadTaskOrderMap.value,
    [taskKey]: nextOrder
  }
}

const removeUploadTaskDisplayOrder = (task) => {
  const taskKey = typeof task === 'string' ? task : getUploadTaskStableKey(task)
  if (!taskKey || !uploadTaskOrderMap.value[taskKey]) {
    return
  }
  const nextMap = { ...uploadTaskOrderMap.value }
  delete nextMap[taskKey]
  uploadTaskOrderMap.value = nextMap
}

const sortUploadTasksForDisplay = (tasks) => {
  return [...tasks].sort((a, b) => {
    const orderA = uploadTaskOrderMap.value[getUploadTaskStableKey(a)]
    const orderB = uploadTaskOrderMap.value[getUploadTaskStableKey(b)]
    if (orderA && orderB && orderA !== orderB) {
      return orderA - orderB
    }

    const queueOrderA = Number(a?.queue_order || 0)
    const queueOrderB = Number(b?.queue_order || 0)
    if (queueOrderA > 0 && queueOrderB > 0 && queueOrderA !== queueOrderB) {
      return queueOrderA - queueOrderB
    }

    const createdAtA = Number(a?.created_at || 0)
    const createdAtB = Number(b?.created_at || 0)
    if (createdAtA !== createdAtB) {
      return createdAtA - createdAtB
    }

    return Number(orderA || Number.MAX_SAFE_INTEGER) - Number(orderB || Number.MAX_SAFE_INTEGER)
  })
}

const displayUploadTasks = computed(() => {
  return sortUploadTasksForDisplay(
    [...localUploadTasks.value, ...uploadTasks.value]
      .filter(task => !hiddenUploadTaskKeys.has(getUploadTaskStableKey(task)))
  )
})

const activeUploadTasks = computed(() => {
  return displayUploadTasks.value.filter(task => ['pending', 'running'].includes(task.status))
})

const runningUploadTasks = computed(() => {
  return displayUploadTasks.value.filter(task => ['pending', 'running', 'failed', 'paused', 'canceled'].includes(task.status))
})

const completedUploadTasks = computed(() => {
  return displayUploadTasks.value.filter(task => ['success', 'skipped'].includes(task.status))
})

const filteredUploadTasks = computed(() => {
  return uploadTaskView.value === 'completed'
    ? completedUploadTasks.value
    : runningUploadTasks.value
})

const canBatchPause = computed(() => {
  return filteredUploadTasks.value.some(task => ['pending', 'running'].includes(task.status))
})

const canBatchResume = computed(() => {
  return filteredUploadTasks.value.some(task => ['failed', 'paused', 'canceled'].includes(task.status))
})

const canBatchToggle = computed(() => {
  return canBatchPause.value || canBatchResume.value
})

const canBatchDelete = computed(() => {
  return filteredUploadTasks.value.length > 0
})

const batchToggleMode = computed(() => {
  return canBatchResume.value ? 'resume' : 'pause'
})

const batchToggleLabel = computed(() => {
  return batchToggleMode.value === 'pause' ? '全部暂停' : '全部开始'
})

const batchToggleTitle = computed(() => {
  if (!canBatchToggle.value) {
    return '当前没有可操作的任务'
  }
  return batchToggleMode.value === 'pause'
    ? '暂停当前页签中的任务'
    : '继续当前页签中的任务'
})

const batchDeleteLabel = computed(() => {
  return uploadTaskView.value === 'completed' ? '全部清空' : '全部删除'
})

const uploadTaskEmptyText = computed(() => {
  return uploadTaskView.value === 'completed'
    ? '暂无已完成任务'
    : '暂无进行中的上传任务'
})

const uploadTaskBadgeText = computed(() => {
  const runningCount = activeUploadTasks.value.length
  if (runningCount > 0) {
    return `上传中 ${runningCount}`
  }

  const failedCount = displayUploadTasks.value.filter(task => task.status === 'failed').length
  if (failedCount > 0) {
    return `失败 ${failedCount}`
  }

  const pausedCount = displayUploadTasks.value.filter(task => task.status === 'paused').length
  if (pausedCount > 0) {
    return `已暂停 ${pausedCount}`
  }

  const successCount = displayUploadTasks.value.filter(task => task.status === 'success').length
  if (successCount > 0) {
    return `上传完成 ${successCount}`
  }

  return ''
})

const uploadTaskTitle = computed(() => {
  if (activeUploadTasks.value.length > 0) {
    return uploadTaskBadgeText.value
  }
  if (displayUploadTasks.value.some(task => task.status === 'failed')) {
    return uploadTaskBadgeText.value || '传输列表'
  }
  if (displayUploadTasks.value.some(task => task.status === 'paused')) {
    return uploadTaskBadgeText.value || '传输列表'
  }
  if (displayUploadTasks.value.some(task => task.status === 'success')) {
    return uploadTaskBadgeText.value || '传输列表'
  }
  return '传输列表'
})

const uploadTaskLabel = computed(() => {
  if (activeUploadTasks.value.length > 0) {
    return uploadTaskBadgeText.value
  }
  if (displayUploadTasks.value.some(task => task.status === 'failed')) {
    return uploadTaskBadgeText.value || '传输失败'
  }
  if (displayUploadTasks.value.some(task => task.status === 'paused')) {
    return uploadTaskBadgeText.value || '传输已暂停'
  }
  if (displayUploadTasks.value.some(task => task.status === 'success')) {
    return uploadTaskBadgeText.value || '上传完成'
  }
  return '暂无传输任务'
})

const getActiveUploadSlotUsage = () => (
  localDispatchingTaskIds.size +
  uploadTasks.value.filter(task => {
    const taskId = String(task?.task_id || '')
    const status = String(task?.status || '')
    if (status === 'running') {
      return true
    }
    if (status === 'pending') {
      return !pendingRemoteResumeTaskIds.has(taskId)
    }
    return false
  }).length
)

const isRemoteTaskWaitingResume = (task) => {
  const taskId = String(task?.task_id || '')
  return Boolean(taskId) && pendingRemoteResumeTaskIds.has(taskId)
}

const getUploadTaskStatusText = (status) => {
  if (status === 'pending') return '等待中'
  if (status === 'running') return '上传中'
  if (status === 'paused') return '已暂停'
  if (status === 'success') return '已完成'
  if (status === 'skipped') return '已跳过'
  if (status === 'failed') return '失败'
  return '已取消'
}

const getUploadTaskMessage = (task) => {
  if (isRemoteTaskWaitingResume(task)) {
    return '等待继续上传'
  }
  return task.message || '-'
}

const getUploadTaskDriverType = (task) => {
  const taskDriverType = String(task?.driver_type || '').trim().toLowerCase()
  if (taskDriverType) {
    return taskDriverType
  }
  const account = accounts.value.find(item => String(item.id) === String(task?.account_id))
  return String(account?.driver_type || '').trim().toLowerCase()
}

const getUploadTaskDriverBadge = (task) => {
  const driverType = getUploadTaskDriverType(task)
  const account = accounts.value.find(item => {
    const sameId = task?.account_id != null && String(item.id) === String(task.account_id)
    const sameType = driverType && String(item.driver_type || '').toLowerCase() === driverType
    return sameId || sameType
  })
  const fallbackTitle = task?.account_name ? String(task.account_name) : '上传目标网盘'
  if (account) {
    return {
      logo: account.driver_card_logo || '',
      color: account.driver_card_color || '#64748b',
      name: account.driver_card_name || (task?.account_name ? String(task.account_name).slice(0, 2) : '网盘'),
      title: fallbackTitle,
    }
  }
  return {
    logo: '',
    color: '#64748b',
    name: task?.account_name ? String(task.account_name).slice(0, 2) : '网盘',
    title: fallbackTitle,
  }
}

const translateUploadErrorMessage = (message) => {
  const text = String(message || '').trim()
  if (!text) return '上传失败'
  if (text.includes('Server disconnected')) return '服务器连接已断开'
  if (text.includes('Connection timeout')) return '连接服务器超时'
  if (text.includes('Timeout')) return '请求超时'
  if (text.includes('Network Error')) return '网络连接异常'
  if (text.includes('Failed to fetch')) return '网络请求失败'
  return text
}

const normalizeUploadRelativePath = (file) => {
  const rawPath = String(file?.webkitRelativePath || file?.name || '').replace(/\\/g, '/')
  return rawPath
    .split('/')
    .filter(Boolean)
    .join('/')
}

const splitUploadRelativePath = (relativePath) => (
  String(relativePath || '')
    .split('/')
    .filter(Boolean)
)

const getUploadRelativeDirectory = (relativePath) => {
  const parts = splitUploadRelativePath(relativePath)
  parts.pop()
  return parts.join('/')
}

const getUploadFolderRootName = (relativePath) => splitUploadRelativePath(relativePath)[0] || ''

const getCurrentBreadcrumbNameParts = () => (
  breadcrumbItems.value
    .map(item => String(item?.name || '').trim())
    .filter(Boolean)
    .slice(1)
)

const getCurrentDisplayPath = () => {
  const parts = getCurrentBreadcrumbNameParts()
  return parts.length ? `/${parts.join('/')}` : '/'
}

const buildUploadTargetDisplayPath = (relativeDirectory = '') => {
  const currentParts = getCurrentBreadcrumbNameParts()
  const relativeParts = splitUploadRelativePath(relativeDirectory)
  return [...currentParts, ...relativeParts].join('/')
}

const createSkippedUploadTask = (file, reason, options = {}) => ({
  task_id: `local-skip-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  account_id: selectedAccountId.value,
  account_name: selectedAccountName.value,
  file_name: options.displayName || file.name,
  target_path: options.targetPath || currentPath.value,
  target_display_path: options.targetDisplayPath || '',
  status: 'skipped',
  progress: 0,
  message: reason,
  error: ''
})

const isLocalUploadTask = (task) => String(task?.task_id || '').startsWith('local-')

const isSendingToLitePanServerTask = (task) => (
  isLocalUploadTask(task) && String(task?.status || '') === 'pending'
)

const hasStartedUploadTask = (task) => {
  const status = String(task?.status || '')
  if (['running', 'paused'].includes(status)) {
    return true
  }
  return Number(task?.progress || 0) > 0
}

const shouldShowUploadTaskProgressBar = (task) => {
  const status = String(task?.status || '')
  return !['pending', 'canceled', 'success', 'skipped'].includes(status) && hasStartedUploadTask(task)
}

const shouldShowUploadTaskMetaPercent = (task) => shouldShowUploadTaskProgressBar(task)

const shouldSkipUploadNotice = () => {
  try {
    return localStorage.getItem(UPLOAD_NOTICE_STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

const markUploadNoticeSkipped = () => {
  try {
    localStorage.setItem(UPLOAD_NOTICE_STORAGE_KEY, 'true')
  } catch {
    // 本地存储不可用时静默降级
  }
}

const clearUploadNoticeSkipped = () => {
  try {
    localStorage.removeItem(UPLOAD_NOTICE_STORAGE_KEY)
  } catch {
    // 本地存储不可用时静默降级
  }
}

const showUploadNoticeDialog = () => {
  if (shouldSkipUploadNotice()) {
    return Promise.resolve(true)
  }
  return openUploadNoticeDialog()
}

const openUploadNoticeDialog = async () => {
  const result = await custom({
    title: '',
    size: 'medium',
    closable: false,
    hideFooter: true,
    component: UploadNoticeDialog,
    componentProps: {
      skipChecked: shouldSkipUploadNotice()
    }
  }).catch(() => null)

  if (!result?.confirmed) {
    return false
  }

  if (result.skipNextTime) {
    markUploadNoticeSkipped()
  } else {
    clearUploadNoticeSkipped()
  }

  return true
}

const ensureUploadNoticeConfirmed = async () => {
  return await showUploadNoticeDialog()
}

const openUploadNoticeFromPanel = async () => {
  await openUploadNoticeDialog()
}

const showUploadConflictDialog = async (fileName) => {
  return await custom({
    title: '',
    size: 'medium',
    closable: false,
    hideFooter: true,
    component: UploadConflictDialog,
    componentProps: {
      fileName
    }
  }).catch(() => null)
}

const showUploadTaskDeleteDialog = async (task) => {
  return await new Promise((resolve) => {
    const isUploadedTask = task.status === 'success'
    const actionButtonsHtml = isUploadedTask
      ? `
        <label style="display:flex;align-items:center;gap:8px;padding:0 22px 18px;color:#64748b;font-size:14px;cursor:pointer;">
          <input type="checkbox" data-role="delete-file" style="width:16px;height:16px;">
          <span>同时删除文件</span>
        </label>
      `
      : ''

    const overlay = document.createElement('div')
    overlay.style.cssText = `
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.28);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10020;
    `

    const dialog = document.createElement('div')
    dialog.style.cssText = `
      width: min(520px, calc(100vw - 40px));
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
      overflow: hidden;
    `

    dialog.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 22px 0;">
        <div style="font-size:28px;font-weight:700;color:#111827;">删除任务</div>
        <button type="button" data-action="close" style="width:24px;height:24px;border:none;background:transparent;color:#64748b;font-size:24px;line-height:1;cursor:pointer;">×</button>
      </div>
      <div style="padding:18px 22px 16px;color:#475569;font-size:15px;line-height:1.8;">
        <div>确定要删除任务</div>
        <div style="margin-top:4px;color:#111827;word-break:break-all;">${task.file_name}</div>
      </div>
      ${actionButtonsHtml}
      <div style="display:flex;justify-content:flex-end;padding:0 22px 22px;">
        <button type="button" data-action="delete-task" style="min-width:96px;height:36px;border:none;border-radius:10px;background:linear-gradient(135deg, #ef4444 0%, #f97316 100%);color:#fff;cursor:pointer;">删除</button>
      </div>
    `

    const cleanup = (result = null) => {
      overlay.remove()
      resolve(result)
    }

    overlay.addEventListener('click', (event) => {
      if (event.target === overlay) {
        cleanup(null)
      }
    })

    dialog.querySelector('[data-action="close"]').addEventListener('click', () => cleanup(null))
    dialog.querySelector('[data-action="delete-task"]').addEventListener('click', () => cleanup({
      deleteUploadedFile: Boolean(dialog.querySelector('[data-role="delete-file"]')?.checked)
    }))

    overlay.appendChild(dialog)
    document.body.appendChild(overlay)
  })
}

const showBatchUploadTaskDeleteDialog = async (tasks) => {
  return await new Promise((resolve) => {
    const successCount = tasks.filter(task => task.status === 'success').length
    const overlay = document.createElement('div')
    overlay.style.cssText = `
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.28);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10020;
    `

    const dialog = document.createElement('div')
    dialog.style.cssText = `
      width: min(540px, calc(100vw - 40px));
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
      overflow: hidden;
    `

    dialog.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 22px 0;">
        <div style="font-size:28px;font-weight:700;color:#111827;">批量删除任务</div>
        <button type="button" data-action="close" style="width:24px;height:24px;border:none;background:transparent;color:#64748b;font-size:24px;line-height:1;cursor:pointer;">×</button>
      </div>
      <div style="padding:18px 22px 16px;color:#475569;font-size:15px;line-height:1.8;">
        <div>确定要删除 ${tasks.length} 个任务吗？</div>
      </div>
      ${successCount > 0 ? `
        <label style="display:flex;align-items:center;gap:8px;padding:0 22px 18px;color:#64748b;font-size:14px;cursor:pointer;">
          <input type="checkbox" data-role="delete-file" style="width:16px;height:16px;">
          <span>同时删除文件</span>
        </label>
      ` : ''}
      <div style="display:flex;justify-content:flex-end;padding:0 22px 22px;">
        <button type="button" data-action="delete-task" style="min-width:96px;height:36px;border:none;border-radius:10px;background:linear-gradient(135deg, #ef4444 0%, #f97316 100%);color:#fff;cursor:pointer;">删除</button>
      </div>
    `

    const cleanup = (result = null) => {
      overlay.remove()
      resolve(result)
    }

    overlay.addEventListener('click', (event) => {
      if (event.target === overlay) {
        cleanup(null)
      }
    })

    dialog.querySelector('[data-action="close"]').addEventListener('click', () => cleanup(null))
    dialog.querySelector('[data-action="delete-task"]').addEventListener('click', () => cleanup({
      deleteUploadedFile: Boolean(dialog.querySelector('[data-role="delete-file"]')?.checked)
    }))

    overlay.appendChild(dialog)
    document.body.appendChild(overlay)
  })
}

const canHandleUploadTaskPrimaryAction = (task) => {
  return ['success', 'skipped', 'pending', 'running', 'failed', 'paused', 'canceled'].includes(task.status)
}

const getUploadTaskPrimaryActionTitle = (task) => {
  if (['success', 'skipped'].includes(task.status)) {
    return '打开所在目录'
  }
  if (['pending', 'running'].includes(task.status)) {
    return '暂停上传任务'
  }
  return '继续上传任务'
}

const getUploadTaskPrimaryActionLabel = (task) => {
  if (['success', 'skipped'].includes(task.status)) {
    return '打开'
  }
  if (['pending', 'running'].includes(task.status)) {
    return '暂停'
  }
  return '继续'
}

const getUploadTaskPrimaryActionIconClass = (task) => {
  if (['success', 'skipped'].includes(task.status)) {
    return 'fas fa-folder-open'
  }
  if (['pending', 'running'].includes(task.status)) {
    return 'fas fa-pause'
  }
  return 'fas fa-play'
}

const getUploadTaskOpenPath = (task) => (
  String(task?.result?.parent_id || task?.result?.parent_path || task?.target_path || '0')
)

const isUploadTaskInCurrentPath = (task) => (
  String(task?.account_id) === String(selectedAccountId.value) &&
  getUploadTaskOpenPath(task) === String(currentPath.value || '0')
)

const getUploadTaskDirectorySegments = (task) => {
  const meta = getUploadTaskMeta(task)
  const targetDisplayPath = String(task?.target_display_path || meta?.targetDisplayPath || '')
    .replace(/\\/g, '/')
    .split('/')
    .filter(Boolean)
  if (targetDisplayPath.length > 0) {
    return targetDisplayPath
  }

  return String(task?.file_name || '')
    .replace(/\\/g, '/')
    .split('/')
    .filter(Boolean)
    .slice(0, -1)
}

const buildUploadTaskBreadcrumb = async (account, task) => {
  const rootId = getRootId(account?.config || {})
  const targetPath = getUploadTaskOpenPath(task)
  if (targetPath === rootId || (targetPath === '0' && rootId === '0')) {
    return [{ name: '根目录', path: rootId }]
  }

  const directorySegments = getUploadTaskDirectorySegments(task)
  if (directorySegments.length === 0) {
    return [
      { name: '根目录', path: rootId },
      { name: '当前目录', path: targetPath }
    ]
  }

  const breadcrumb = [{ name: '根目录', path: rootId }]
  let currentParentId = rootId

  for (let index = 0; index < directorySegments.length; index += 1) {
    const segment = directorySegments[index]
    const isLast = index === directorySegments.length - 1
    try {
      const response = await axios.get('/api/files/list', {
        params: {
          account_id: account.id,
          path: currentParentId
        }
      })
      const files = Array.isArray(response.data?.data) ? response.data.data : []
      const matchedFolder = files.find(item => item?.is_dir && String(item?.name || '') === segment)
      const resolvedPath = matchedFolder?.id ? String(matchedFolder.id) : (isLast ? targetPath : currentParentId)
      breadcrumb.push({
        name: segment,
        path: resolvedPath
      })
      currentParentId = resolvedPath
    } catch (error) {
      breadcrumb.push({
        name: segment,
        path: isLast ? targetPath : currentParentId
      })
    }
  }

  if (breadcrumb[breadcrumb.length - 1]?.path !== targetPath) {
    breadcrumb[breadcrumb.length - 1] = {
      ...breadcrumb[breadcrumb.length - 1],
      path: targetPath
    }
  }

  return breadcrumb
}

const canDeleteUploadTask = (task) => {
  return Boolean(task?.task_id)
}

const pauseUploadTask = async (task, silent = false) => {
  if (isLocalUploadTask(task)) {
    pauseLocalUploadTask(task.task_id)
    return
  }
  clearPendingRemoteResumeTask(task.task_id)
  try {
    patchRemoteUploadTask(task.task_id, {
      status: 'paused',
      message: '上传已暂停',
      error: ''
    })
    const response = await axios.post(`/api/files/upload/tasks/${task.task_id}/pause`)
    if (!response.data?.success) {
      await fetchUploadTasks()
      if (!silent) {
        window.appNotification.error(response.data?.message || '暂停上传任务失败')
      }
      return
    }
    await fetchUploadTasks()
  } catch (error) {
    console.error('暂停上传任务失败:', error)
    if (!silent) {
      window.appNotification.error(error.response?.data?.message || '暂停上传任务失败')
    }
  }
}

const resumeUploadTask = async (task, silent = false) => {
  if (isLocalUploadTask(task)) {
    const payload = getLocalUploadTaskPayload(task.task_id)
    if (!payload?.file) {
      updateLocalUploadTask(task.task_id, {
        status: 'failed',
        message: '继续上传失败',
        error: '缺少本地上传数据，无法继续'
      })
      if (!silent) {
        window.appNotification.error('缺少本地上传数据，无法继续')
      }
      return
    }

    clearLocalUploadTaskPausedState(task.task_id)
    clearLocalUploadTaskCanceledState(task.task_id)
    updateLocalUploadTask(task.task_id, {
      status: 'pending',
      message: '等待上传',
      error: ''
    })
    uploadTaskView.value = 'running'
    startUploadTaskScheduler()
    return
  }
  pendingRemoteResumeTaskIds.add(String(task.task_id))
  patchRemoteUploadTask(task.task_id, {
    message: '等待继续上传',
    error: ''
  })
  startUploadTaskPolling()
  uploadTaskView.value = 'running'
  startUploadTaskScheduler()
}

const handleDeleteUploadTask = async (task, options = {}) => {
  const { silent = false, deleteUploadedFile = null, skipDialog = false } = options
  if (!canDeleteUploadTask(task)) {
    return
  }

  if (isLocalUploadTask(task)) {
    if (!skipDialog) {
      const deleteResult = await showUploadTaskDeleteDialog(task)
      if (!deleteResult) {
        return
      }
    }
    hideUploadTask(task)
    cancelLocalUploadTask(task.task_id)
    return
  }

  const deleteResult = skipDialog
    ? { deleteUploadedFile: Boolean(deleteUploadedFile) }
    : await showUploadTaskDeleteDialog(task)
  if (!deleteResult) {
    return
  }

  const runDelete = async () => {
    try {
      hideUploadTask(task)
      removeRemoteUploadTask(task.task_id)
      const response = await axios.delete(`/api/files/upload/tasks/${task.task_id}`, {
        params: {
          delete_uploaded_file: deleteResult.deleteUploadedFile ? 'true' : 'false'
        }
      })
      if (!response.data?.success) {
        showUploadTask(task)
        await fetchUploadTasks()
        if (!silent) {
          window.appNotification.error(response.data?.message || '删除上传任务失败')
        }
        return
      }

      await fetchUploadTasks()
      if (
        deleteResult.deleteUploadedFile &&
        isUploadTaskInCurrentPath(task)
      ) {
        await loadFiles(true)
      }
      removeUploadTaskDisplayOrder(task)
    } catch (error) {
      showUploadTask(task)
      await fetchUploadTasks()
      console.error('删除上传任务失败:', error)
      if (!silent) {
        window.appNotification.error(error.response?.data?.message || '删除上传任务失败')
      }
    }
  }

  const shouldSerializeDeleteWithFile = deleteResult.deleteUploadedFile && task.status === 'success'
  if (shouldSerializeDeleteWithFile) {
    const runner = async () => runDelete()
    const chainedPromise = singleDeleteWithFileChain.then(runner, runner)
    singleDeleteWithFileChain = chainedPromise.catch(() => {})
    await chainedPromise
    return
  }

  await runDelete()
}

const handleUploadTaskPrimaryAction = async (task) => {
  if (['pending', 'running'].includes(task.status)) {
    await pauseUploadTask(task)
    return
  }

  if (['failed', 'paused', 'canceled'].includes(task.status)) {
    await resumeUploadTask(task)
    return
  }

  if (!['success', 'skipped'].includes(task.status)) {
    return
  }

  const account = accounts.value.find(item => String(item.id) === String(task.account_id))
  if (!account) {
    window.appNotification.warning('未找到对应账号')
    return
  }

  try {
    if (String(selectedAccountId.value) !== String(task.account_id)) {
      await selectAccount(account)
    }

    currentPath.value = getUploadTaskOpenPath(task)
    breadcrumbItems.value = await buildUploadTaskBreadcrumb(account, task)
    selectedFilesList.value = []
    await loadFiles(true)
    closeUploadTaskPanel()
  } catch (error) {
    console.error('打开上传目录失败:', error)
    window.appNotification.error('打开目录失败')
  }
}

const getBatchTasksByStatus = (statuses) => {
  return filteredUploadTasks.value.filter(task => statuses.includes(task.status))
}

const handleBatchPause = async () => {
  batchPauseInProgress.value = true
  try {
    for (let attempt = 0; attempt < 4; attempt += 1) {
      const tasks = getBatchTasksByStatus(['pending', 'running'])
      if (tasks.length === 0) {
        break
      }
      for (const task of tasks) {
        await pauseUploadTask(task, true)
      }
      await wait(150)
      await fetchUploadTasks()
    }
  } finally {
    batchPauseInProgress.value = false
  }
}

const handleBatchResume = async () => {
  const tasks = getBatchTasksByStatus(['failed', 'paused', 'canceled'])
  if (tasks.length === 0) {
    return
  }
  for (const task of tasks) {
    await resumeUploadTask(task, true)
  }
}

const handleBatchToggle = async () => {
  if (batchToggleMode.value === 'pause') {
    await handleBatchPause()
    return
  }
  await handleBatchResume()
}

const handleBatchDelete = async () => {
  const tasks = [...filteredUploadTasks.value]
  if (tasks.length === 0) {
    return
  }

  const hasRemoteTasks = tasks.some(task => !isLocalUploadTask(task))
  let deleteUploadedFile = false
  if (hasRemoteTasks) {
    const deleteResult = await showBatchUploadTaskDeleteDialog(tasks)
    if (!deleteResult) {
      return
    }
    deleteUploadedFile = Boolean(deleteResult.deleteUploadedFile)
  }

  const localTasks = tasks.filter(task => isLocalUploadTask(task))
  const remoteTasks = tasks.filter(task => !isLocalUploadTask(task))
  const shouldShowDeleteFileLoading = deleteUploadedFile && remoteTasks.some(task => task.status === 'success')

  localTasks.forEach(task => {
    handleDeleteUploadTask(task, { silent: true, skipDialog: true })
  })

  if (remoteTasks.length > 0) {
    if (shouldShowDeleteFileLoading) {
      uploadTaskPanelLoading.value = true
      uploadTaskPanelLoadingText.value = '正在删除文件...'
    }
    try {
      const removedRemoteTasks = [...remoteTasks]
      remoteTasks.forEach(task => {
        hideUploadTask(task)
        removeRemoteUploadTask(task.task_id)
      })

      let hasFailedDelete = false
      let hasRejectedResponse = false
      try {
        const response = await axios.post('/api/files/upload/tasks/batch-delete', {
          task_ids: remoteTasks.map(task => task.task_id),
          delete_uploaded_file: deleteUploadedFile,
        })

        if (!response.data?.success) {
          hasRejectedResponse = true
          remoteTasks.forEach(task => showUploadTask(task))
        } else {
          const deletedTaskIdSet = new Set(response.data.data?.deleted_task_ids || [])
          remoteTasks.forEach(task => {
            if (deletedTaskIdSet.has(task.task_id)) {
              removeUploadTaskDisplayOrder(task)
            } else {
              showUploadTask(task)
            }
          })
          hasRejectedResponse = Boolean((response.data.data?.failed_task_ids || []).length)
        }
      } catch (error) {
        hasFailedDelete = true
        remoteTasks.forEach(task => showUploadTask(task))
      }

      if (hasFailedDelete || hasRejectedResponse) {
        await fetchUploadTasks()
        if (removedRemoteTasks.some(task =>
          deleteUploadedFile &&
          task.status === 'success' &&
          isUploadTaskInCurrentPath(task)
        )) {
          await loadFiles(true)
        }
      } else if (removedRemoteTasks.some(task =>
        deleteUploadedFile &&
        task.status === 'success' &&
        isUploadTaskInCurrentPath(task)
      )) {
        await loadFiles(true)
      }
    } finally {
      if (shouldShowDeleteFileLoading) {
        uploadTaskPanelLoading.value = false
        uploadTaskPanelLoadingText.value = '正在准备上传任务...'
      }
    }
  }

}

// 自然排序函数，处理包含数字的文件名
const naturalSort = (a, b) => {
  // 将字符串拆分为数字和非数字部分
  const splitA = String(a).match(/(\d+|\D+)/g) || []
  const splitB = String(b).match(/(\d+|\D+)/g) || []
  
  const maxLength = Math.max(splitA.length, splitB.length)
  
  for (let i = 0; i < maxLength; i++) {
    const partA = splitA[i] || ''
    const partB = splitB[i] || ''
    
    // 如果两个部分都是数字，按数字大小比较
    if (/^\d+$/.test(partA) && /^\d+$/.test(partB)) {
      const numA = parseInt(partA, 10)
      const numB = parseInt(partB, 10)
      if (numA !== numB) {
        return numA - numB
      }
    } else {
      // 否则按字符串比较
      const comparison = partA.toLowerCase().localeCompare(partB.toLowerCase(), 'zh-CN')
      if (comparison !== 0) {
        return comparison
      }
    }
  }
  
  return 0
}

const sortedFiles = computed(() => {
  const sorted = [...files.value].sort((a, b) => {
    // 文件夹优先
    if (a.is_dir && !b.is_dir) return -1
    if (!a.is_dir && b.is_dir) return 1
    
    let aVal = a[sortKey.value]
    let bVal = b[sortKey.value]
    
    if (sortKey.value === 'size') {
      aVal = a.size || 0
      bVal = b.size || 0
    } else if (sortKey.value === 'modified') {
      aVal = new Date(a.modified || 0)
      bVal = new Date(b.modified || 0)
    } else {
      // 名称排序使用自然排序
      if (sortKey.value === 'name') {
        const result = naturalSort(aVal || '', bVal || '')
        return sortOrder.value === 'asc' ? result : -result
      }
      // 其他字段使用普通字符串比较
      aVal = String(aVal || '').toLowerCase()
      bVal = String(bVal || '').toLowerCase()
    }
    
    if (aVal < bVal) return sortOrder.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })
  return sorted
})

// 监听选中文件列表变化
watch(selectedFilesList, (newVal) => {
  selectedFiles.value = new Set(newVal)
}, { deep: true })

// 方法
const toggleDropdown = () => {
  dropdownOpen.value = !dropdownOpen.value
}

const getFloatingAccountText = (account) => {
  const cardName = String(account?.driver_card_name || '').trim()
  if (cardName) {
    return cardName
  }
  const driverType = String(account?.driver_type || '').trim()
  return driverType ? driverType.slice(0, 2).toUpperCase() : '盘'
}

const getFloatingAccountColor = (account) => {
  return account?.driver_card_color || '#6366f1'
}

// 获取账号的根目录 ID
const getRootId = (config) => {
  // 所有实际驱动都使用 root_folder_id 字段
  const rootId = config.root_folder_id || '0'
  return rootId
}

const selectAccount = async (account) => {
  // 保存当前状态，用于失败时回滚
  const previousAccountId = selectedAccountId.value
  const previousAccountName = selectedAccountName.value
  const previousPath = currentPath.value
  const previousBreadcrumb = [...breadcrumbItems.value]
  
  if (account) {
    selectedAccountId.value = account.id
    selectedAccountName.value = account.name
    
    // 获取账号的根目录 ID
    const config = account.config || {}
    const rootId = getRootId(config)
    currentPath.value = rootId
    breadcrumbItems.value = [{ name: '根目录', path: rootId }]
  } else {
    selectedAccountId.value = null
    selectedAccountName.value = ''
    currentPath.value = '0'
    breadcrumbItems.value = [{ name: '根目录', path: '0' }]
  }
  dropdownOpen.value = false
  
  // 清除选中项（切换账号时）
  selectedFilesList.value = []
  
  if (selectedAccountId.value) {
    try {
      await loadFiles()
    } catch (error) {
      console.error('账号切换失败，开始回滚状态:', error)
      // 回滚到上一个状态
      selectedAccountId.value = previousAccountId
      selectedAccountName.value = previousAccountName
      currentPath.value = previousPath
      breadcrumbItems.value = previousBreadcrumb
      // 显示错误提示
      window.appNotification.error('账号切换失败，请检查账号状态')
    }
  } else {
    files.value = []
  }
}

const loadAccounts = async () => {
  try {
    const response = await axios.get('/api/public/accounts')
    if (response.data.success) {
      accounts.value = response.data.data || []
      
      // 使用 nextTick 确保计算属性已更新，再自动选择第一个启用账号
      await nextTick()
      if (!selectedAccountId.value && firstActiveAccount.value) {
        selectAccount(firstActiveAccount.value)
      }
    }
  } catch (error) {
    console.error('获取账号列表失败:', error)
    window.appNotification.error('获取账号列表失败')
  }
}

const loadPublicSystemConfig = async () => {
  try {
    const response = await axios.get('/api/public/system-config')
    if (response.data?.success) {
      const mode = response.data.data?.index_account_switch_mode
      accountSwitchMode.value = ['dropdown', 'floating'].includes(mode) ? mode : 'dropdown'
    }
  } catch (error) {
    accountSwitchMode.value = 'dropdown'
  }
}

// 监听账号列表变化，当账号列表更新时重新选择默认账号
watch(accounts, (newAccounts) => {
  if (newAccounts.length > 0 && !selectedAccountId.value) {
    const defaultAccount = newAccounts.find(acc => acc.is_default && (acc.is_active === 1 || acc.is_active === true || acc.enabled === 1 || acc.enabled === true))
    if (defaultAccount) {
      selectAccount(defaultAccount)
    }
  }
}, { deep: true })

const loadFiles = async (forceRefresh = false) => {
  if (!selectedAccountId.value) return

  loading.value = true
  const startTime = Date.now()
  
  try {
    const params = {
      account_id: selectedAccountId.value,
      path: currentPath.value
    }
    
    // 如果需要强制刷新，添加参数
    if (forceRefresh) {
      params.force_refresh = true
    }
    
    const response = await axios.get('/api/files/list', { params })
    
    if (response.data.success) {
      files.value = response.data.data
      const endTime = Date.now()
      responseTime.value = `${endTime - startTime}ms`
      await applyCachedFolderSizes(selectedAccountId.value, currentPath.value)
      
      // 获取缓存命中率（异步，不阻塞文件列表显示）
      setTimeout(async () => {
        try {
          const hitRateResponse = await axios.get('/api/public/cache/hit-rate')
          if (hitRateResponse.data.success) {
            cacheRate.value = `${hitRateResponse.data.data.hit_rate}%`
          } else {
            cacheRate.value = '-'
          }
        } catch (hitRateError) {
          cacheRate.value = '-'
        }
      }, 0) // 使用 setTimeout 让命中率获取不阻塞主流程
    } else {
      // 抛出错误，让调用方处理
      throw new Error(response.data.message || '获取文件列表失败')
    }
  } catch (error) {
    console.error('获取文件列表失败:', error)
    // 重新抛出错误，让调用方处理
    throw error
  } finally {
    loading.value = false
  }
}

const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const refreshAfterCreateFolder = async (folderName) => {
  const normalizedFolderName = folderName.trim().toLowerCase()

  await loadFiles(true)

  const folderExists = files.value.some(file =>
    file.is_dir && file.name.trim().toLowerCase() === normalizedFolderName
  )

  if (!folderExists) {
    await wait(800)
    await loadFiles(true)
  }
}

const refreshFiles = async (silent = false) => {
  if (!selectedAccountId.value) {
    if (!silent) {
      window.appNotification.warning('请先选择一个账号')
    }
    return
  }
  
  const refreshAccountId = selectedAccountId.value
  const refreshPath = currentPath.value

  try {
    if (!silent) {
      operationLoading.value = true
      operationMessage.value = '正在强制刷新...'
    }
    
    const response = await axios.post('/api/files/refresh', {
      account_id: selectedAccountId.value,
      parent_id: currentPath.value
    })
    
    if (response.data.success) {
      files.value = response.data.data
      await applyCachedFolderSizes(refreshAccountId, refreshPath)
      if (!silent) {
        window.appNotification.success(response.data.message || '刷新成功')
      }
    } else {
      if (!silent) {
        window.appNotification.error(response.data.message || '刷新失败')
      }
      console.error('刷新失败:', response.data.message)
    }
  } catch (error) {
    console.error('刷新异常:', error)
    if (!silent) {
      window.appNotification.error('刷新失败: ' + (error.response?.data?.message || error.message))
    }
  } finally {
    if (!silent) {
      operationLoading.value = false
      operationMessage.value = ''
    }
  }
}

const handleRefreshClick = async () => {
  await refreshFiles()
}

const generateCurrentDirectoryStrm = async () => {
  if (!selectedAccountId.value) {
    window.appNotification.warning('请先选择一个账号')
    return
  }

  operationLoading.value = true
  operationMessage.value = '正在生成当前目录 STRM...'
  try {
    await loadFiles(true)
    const response = await axios.post('/api/admin/strm/generate-current-directory', {
      account_id: selectedAccountId.value,
      path: getCurrentDisplayPath(),
      items: files.value || []
    })

    if (!response.data?.success) {
      window.appNotification.error(response.data?.message || '当前目录 STRM 生成失败')
      return
    }

    const result = response.data.data || {}
    if ((result.media_count || 0) <= 0 && (result.deleted || 0) <= 0) {
      window.appNotification.info('当前目录没有需要同步的 STRM')
      return
    }
    const conflictText = (result.skipped_conflict || 0) > 0 ? `，冲突跳过 ${result.skipped_conflict}` : ''
    window.appNotification.success(
      `STRM同步完成：新增 ${result.created || 0}，更新 ${result.updated || 0}，删除 ${result.deleted || 0}，已存在 ${result.skipped_existing || 0}${conflictText}`
    )
  } catch (error) {
    console.error('当前目录 STRM 生成失败:', error)
    window.appNotification.error('当前目录 STRM 生成失败: ' + (error.response?.data?.message || error.message))
  } finally {
    operationLoading.value = false
    operationMessage.value = ''
  }
}

const applyRemoteUploadTasks = async (serverTasks = []) => {
  const previousStatusMap = new Map(uploadTasks.value.map(task => [task.task_id, task.status]))
  const allTasks = (serverTasks || []).map(task => {
    const meta = getUploadTaskMeta(task)
    if (!meta) {
      return task
    }

    const serverPathDepth = String(task?.target_display_path || '')
      .replace(/\\/g, '/')
      .split('/')
      .filter(Boolean)
      .length
    const cachedPathDepth = String(meta?.targetDisplayPath || '')
      .replace(/\\/g, '/')
      .split('/')
      .filter(Boolean)
      .length

    if (cachedPathDepth > serverPathDepth) {
      return {
        ...task,
        target_display_path: meta.targetDisplayPath || task.target_display_path
      }
    }

    return task
  })

  allTasks.forEach(task => ensureUploadTaskDisplayOrder(task))
  const canceledRemoteTasks = allTasks.filter(task => isRemoteUploadTaskCanceledFromLocal(task))
  const existingTaskKeySet = new Set([
    ...localUploadTasks.value.map(task => getUploadTaskStableKey(task)),
    ...allTasks.map(task => getUploadTaskStableKey(task))
  ])

  if (canceledRemoteTasks.length > 0) {
    const deleteResults = await Promise.allSettled(
      canceledRemoteTasks.map(task => axios.delete(`/api/files/upload/tasks/${task.task_id}`))
    )
    canceledRemoteTasks.forEach((task, index) => {
      if (deleteResults[index]?.status === 'fulfilled' && task.client_task_id) {
        clearLocalUploadTaskCanceledState(task.client_task_id)
      }
    })
  }

  Array.from(hiddenUploadTaskKeys).forEach(taskKey => {
    if (!existingTaskKeySet.has(taskKey)) {
      hiddenUploadTaskKeys.delete(taskKey)
    }
  })

  uploadTasks.value = allTasks.filter(task =>
    !isRemoteUploadTaskCanceledFromLocal(task) &&
    !hiddenUploadTaskKeys.has(getUploadTaskStableKey(task))
  )

  const hasNewSuccessInCurrentPath = uploadTasks.value.some(task => {
    if (task.status !== 'success') {
      return false
    }
    if (previousStatusMap.get(task.task_id) === 'success') {
      return false
    }
    return String(task.account_id) === String(selectedAccountId.value) && task.target_path === currentPath.value
  })

  if (hasNewSuccessInCurrentPath) {
    refreshFiles(true)
  }

  if (activeUploadTasks.value.length === 0 && !uploadTaskPanelOpen.value) {
    stopUploadTaskPolling()
  }

  startUploadTaskScheduler()
}

const fetchUploadTasks = async (silent = true) => {
  try {
    const response = await axios.get('/api/files/upload/tasks')
    if (response.data?.success) {
      await applyRemoteUploadTasks(response.data.data || [])
    }
  } catch (error) {
    console.error('获取上传任务失败:', error)
  }
}

const refreshUploadTaskServerConcurrency = async () => {
  try {
    const response = await axios.get('/api/admin/system-config')
    if (response.data?.success) {
      const limit = Number(response.data?.data?.upload_task_concurrency || 3)
      uploadTaskServerConcurrency.value = Number.isFinite(limit) && limit > 0 ? limit : 3
    }
  } catch {
    uploadTaskServerConcurrency.value = 3
  }
}

const getNextUploadTaskCandidate = () => {
  return displayUploadTasks.value.find(task => {
    if (hiddenUploadTaskKeys.has(getUploadTaskStableKey(task))) {
      return false
    }

    if (isLocalUploadTask(task)) {
      return String(task?.status || '') === 'pending' &&
        !localDispatchingTaskIds.has(task.task_id) &&
        !isLocalUploadTaskCanceled(task.task_id) &&
        !isLocalUploadTaskPaused(task.task_id) &&
        Boolean(getLocalUploadTaskPayload(task.task_id)?.file)
    }

    const status = String(task?.status || '')
    return isRemoteTaskWaitingResume(task) && ['paused', 'failed', 'canceled'].includes(status)
  }) || null
}

const activateQueuedUploadTask = async (task) => {
  if (!task) {
    return false
  }

  if (isLocalUploadTask(task)) {
    const payload = getLocalUploadTaskPayload(task.task_id)
    if (!payload?.file) {
      return false
    }
    localDispatchingTaskIds.add(task.task_id)
    createSingleUploadTask(payload.file, payload.conflictPolicy, task, payload)
      .finally(() => {
        localDispatchingTaskIds.delete(task.task_id)
        startUploadTaskScheduler()
      })
    return true
  }

  clearPendingRemoteResumeTask(task.task_id)
  axios.post(`/api/files/upload/tasks/${task.task_id}/resume`)
    .then(async (response) => {
      if (!response.data?.success) {
        pendingRemoteResumeTaskIds.add(String(task.task_id))
        patchRemoteUploadTask(task.task_id, {
          message: response.data?.message || '继续上传任务失败'
        })
      }
      await fetchUploadTasks()
    })
    .catch((error) => {
      pendingRemoteResumeTaskIds.add(String(task.task_id))
      patchRemoteUploadTask(task.task_id, {
        message: error.response?.data?.message || '继续上传任务失败'
      })
    })
    .finally(() => {
      startUploadTaskScheduler()
    })

  return true
}

const startUploadTaskScheduler = async () => {
  if (uploadTaskSchedulerRunning) {
    return
  }

  uploadTaskSchedulerRunning = true
  try {
    await refreshUploadTaskServerConcurrency()
    while (true) {
      const capacity = Math.max(0, uploadTaskServerConcurrency.value - getActiveUploadSlotUsage())
      if (capacity <= 0) {
        break
      }

      const nextTask = getNextUploadTaskCandidate()
      if (!nextTask) {
        break
      }

      const activated = await activateQueuedUploadTask(nextTask)
      if (!activated) {
        break
      }
    }
  } finally {
    uploadTaskSchedulerRunning = false
  }
}

const clearUploadTaskSseReconnectTimer = () => {
  if (uploadTaskSseReconnectTimer) {
    clearTimeout(uploadTaskSseReconnectTimer)
    uploadTaskSseReconnectTimer = null
  }
}

const disconnectUploadTaskStream = () => {
  clearUploadTaskSseReconnectTimer()
  if (uploadTaskEventSource) {
    uploadTaskEventSource.close()
    uploadTaskEventSource = null
  }
}

const scheduleUploadTaskStreamReconnect = () => {
  if (!uploadTaskPanelOpen.value || uploadTaskSseReconnectTimer) {
    return
  }
  uploadTaskSseReconnectTimer = window.setTimeout(() => {
    uploadTaskSseReconnectTimer = null
    connectUploadTaskStream()
  }, 3000)
}

const connectUploadTaskStream = () => {
  if (!uploadTaskPanelOpen.value || uploadTaskEventSource) {
    return
  }
  if (typeof window === 'undefined' || !window.EventSource) {
    startUploadTaskPolling()
    return
  }

  try {
    const eventSource = new window.EventSource('/api/files/upload/tasks/stream')
    uploadTaskEventSource = eventSource

    eventSource.addEventListener('tasks', async (event) => {
      try {
        const payload = JSON.parse(event.data || '{}')
        await applyRemoteUploadTasks(payload.tasks || [])
      } catch (error) {
        console.error('处理上传任务SSE消息失败:', error)
      }
    })

    eventSource.addEventListener('ping', () => {})

    eventSource.onopen = () => {
      stopUploadTaskPolling()
      clearUploadTaskSseReconnectTimer()
    }

    eventSource.onerror = () => {
      disconnectUploadTaskStream()
      startUploadTaskPolling()
      scheduleUploadTaskStreamReconnect()
    }
  } catch (error) {
    console.error('建立上传任务SSE连接失败:', error)
    startUploadTaskPolling()
    scheduleUploadTaskStreamReconnect()
  }
}

const startUploadTaskPolling = () => {
  if (uploadTaskPollingTimer) {
    return
  }
  uploadTaskPollingTimer = window.setInterval(() => {
    fetchUploadTasks()
  }, 400)
}

const stopUploadTaskPolling = () => {
  if (uploadTaskPollingTimer) {
    clearInterval(uploadTaskPollingTimer)
    uploadTaskPollingTimer = null
  }
}

const openUploadTaskPanel = async () => {
  uploadTaskPanelOpen.value = true
  await fetchUploadTasks(false)
  uploadTaskView.value = runningUploadTasks.value.length > 0 ? 'running' : 'completed'
  connectUploadTaskStream()
  if (!uploadTaskEventSource) {
    startUploadTaskPolling()
  }
}

const closeUploadTaskPanel = () => {
  uploadTaskPanelOpen.value = false
  disconnectUploadTaskStream()
  if (activeUploadTasks.value.length === 0) {
    stopUploadTaskPolling()
  }
}

const handleUploadFile = async () => {
  if (!selectedAccountId.value) {
    window.appNotification.warning('请先选择账号')
    return
  }
  const confirmed = await ensureUploadNoticeConfirmed()
  if (!confirmed) {
    return
  }
  uploadFileInput.value?.click()
}

const handleUploadFolder = async () => {
  if (!selectedAccountId.value) {
    window.appNotification.warning('请先选择账号')
    return
  }
  const confirmed = await ensureUploadNoticeConfirmed()
  if (!confirmed) {
    return
  }
  uploadFolderInput.value?.click()
}

const createLocalUploadTask = (file, options = {}) => ({
  task_id: `local-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  account_id: selectedAccountId.value,
  account_name: selectedAccountName.value,
  file_name: options.displayName || file.name,
  target_path: options.targetPath || currentPath.value,
  target_display_path: options.targetDisplayPath || '',
  status: 'pending',
  progress: 0,
  message: '等待发送到 LitePan 服务器',
  error: ''
})

const addLocalUploadTask = (task) => {
  ensureUploadTaskDisplayOrder(task)
  localUploadTasks.value = [task, ...localUploadTasks.value]
}

const updateLocalUploadTask = (taskId, patch) => {
  localUploadTasks.value = localUploadTasks.value.map(task => (
    task.task_id === taskId ? { ...task, ...patch } : task
  ))
}

const removeLocalUploadTask = (taskId) => {
  localUploadTasks.value = localUploadTasks.value.filter(task => task.task_id !== taskId)
}

const isRemoteUploadTaskCanceledFromLocal = (task) => {
  const clientTaskId = String(task?.client_task_id || '')
  return Boolean(clientTaskId) && canceledLocalUploadTaskIds.has(clientTaskId)
}

const isLocalUploadTaskCanceled = (taskId) => canceledLocalUploadTaskIds.has(taskId)
const isLocalUploadTaskPaused = (taskId) => pausedLocalUploadTaskIds.has(taskId)

const releaseLocalUploadTaskController = (taskId) => {
  localUploadTaskControllers.delete(taskId)
}

const setLocalUploadTaskPayload = (taskId, payload) => {
  localUploadTaskPayloads.set(taskId, payload)
}

const getLocalUploadTaskPayload = (taskId) => localUploadTaskPayloads.get(taskId)

const clearLocalUploadTaskPayload = (taskId) => {
  localUploadTaskPayloads.delete(taskId)
}

const setUploadTaskMeta = (taskId, meta) => {
  if (!taskId) {
    return
  }
  uploadTaskMetaCache.set(String(taskId), {
    displayName: String(meta?.displayName || ''),
    targetDisplayPath: String(meta?.targetDisplayPath || '')
  })
}

const getUploadTaskMeta = (task) => {
  const clientTaskId = String(task?.client_task_id || '')
  if (clientTaskId && uploadTaskMetaCache.has(clientTaskId)) {
    return uploadTaskMetaCache.get(clientTaskId)
  }

  const taskId = String(task?.task_id || '')
  if (taskId && uploadTaskMetaCache.has(taskId)) {
    return uploadTaskMetaCache.get(taskId)
  }

  return null
}

const clearUploadTaskMeta = (taskOrId) => {
  if (!taskOrId) {
    return
  }

  if (typeof taskOrId === 'string') {
    uploadTaskMetaCache.delete(String(taskOrId))
    return
  }

  const clientTaskId = String(taskOrId?.client_task_id || '')
  if (clientTaskId) {
    uploadTaskMetaCache.delete(clientTaskId)
  }

  const taskId = String(taskOrId?.task_id || '')
  if (taskId) {
    uploadTaskMetaCache.delete(taskId)
  }
}

const clearLocalUploadTaskCanceledState = (taskId) => {
  canceledLocalUploadTaskIds.delete(taskId)
}

const clearLocalUploadTaskPausedState = (taskId) => {
  pausedLocalUploadTaskIds.delete(taskId)
}

const clearPendingRemoteResumeTask = (taskId) => {
  pendingRemoteResumeTaskIds.delete(String(taskId || ''))
}

const cancelLocalUploadTask = (taskId) => {
  canceledLocalUploadTaskIds.add(taskId)
  clearLocalUploadTaskPausedState(taskId)
  const controller = localUploadTaskControllers.get(taskId)
  if (controller) {
    controller.abort()
  }
  removeLocalUploadTask(taskId)
  removeUploadTaskDisplayOrder(taskId)
  clearLocalUploadTaskPayload(taskId)
  clearUploadTaskMeta(taskId)
}

const pauseLocalUploadTask = (taskId) => {
  pausedLocalUploadTaskIds.add(taskId)
  clearLocalUploadTaskCanceledState(taskId)
  const controller = localUploadTaskControllers.get(taskId)
  if (controller) {
    controller.abort()
  }
  updateLocalUploadTask(taskId, {
    status: 'paused',
    message: '上传已暂停',
    error: ''
  })
}

const isLocalPauseRequested = (taskId) => batchPauseInProgress.value || isLocalUploadTaskPaused(taskId)

const patchRemoteUploadTask = (taskId, patch) => {
  uploadTasks.value = uploadTasks.value.map(task => (
    task.task_id === taskId ? { ...task, ...patch } : task
  ))
}

const removeRemoteUploadTask = (taskId) => {
  const removedTask = uploadTasks.value.find(task => task.task_id === taskId)
  uploadTasks.value = uploadTasks.value.filter(task => task.task_id !== taskId)
  if (removedTask) {
    clearUploadTaskMeta(removedTask)
  } else {
    clearUploadTaskMeta(taskId)
  }
}

const hideUploadTask = (taskOrKey) => {
  const taskKey = typeof taskOrKey === 'string' ? taskOrKey : getUploadTaskStableKey(taskOrKey)
  if (taskKey) {
    hiddenUploadTaskKeys.add(String(taskKey))
  }
}

const showUploadTask = (taskOrKey) => {
  const taskKey = typeof taskOrKey === 'string' ? taskOrKey : getUploadTaskStableKey(taskOrKey)
  if (taskKey) {
    hiddenUploadTaskKeys.delete(String(taskKey))
  }
}

const createSingleUploadTask = async (selectedFile, conflictPolicy = 'fail', localTask = null, options = {}) => {
  const task = localTask || createLocalUploadTask(selectedFile, options)
  const targetPath = options.targetPath || task.target_path || currentPath.value
  const displayName = options.displayName || task.file_name || selectedFile.name
  const targetDisplayPath = options.targetDisplayPath || task.target_display_path || buildUploadTargetDisplayPath()
  if (!localTask) {
    addLocalUploadTask(task)
  }
  setLocalUploadTaskPayload(task.task_id, {
    file: selectedFile,
    conflictPolicy,
    targetPath,
    displayName,
    targetDisplayPath
  })
  setUploadTaskMeta(task.task_id, {
    displayName,
    targetDisplayPath
  })
  if (isLocalUploadTaskCanceled(task.task_id)) {
    removeLocalUploadTask(task.task_id)
    clearLocalUploadTaskCanceledState(task.task_id)
    clearLocalUploadTaskPayload(task.task_id)
    return { success: false, canceled: true, message: '任务已取消' }
  }
  if (isLocalPauseRequested(task.task_id)) {
    updateLocalUploadTask(task.task_id, {
      status: 'paused',
      message: '上传已暂停',
      error: ''
    })
    return { success: false, paused: true, message: '任务已暂停' }
  }
  const formData = new FormData()
  formData.append('account_id', selectedAccountId.value)
  formData.append('path', targetPath)
  formData.append('file', selectedFile)
  formData.append('conflict_policy', conflictPolicy)
  formData.append('client_task_id', task.task_id)
  formData.append('display_name', displayName)
  formData.append('target_display_path', targetDisplayPath)
  const controller = new AbortController()
  localUploadTaskControllers.set(task.task_id, controller)

  try {
    const response = await axios.post('/api/files/upload-task', formData, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (isLocalUploadTaskCanceled(task.task_id)) {
          return
        }
        const loaded = progressEvent.loaded || 0
        const total = progressEvent.total || selectedFile.size || 0
        const progress = total > 0
          ? Math.min(99, Math.round((loaded / total) * 100))
          : 0
        const message = total > 0 && loaded >= total
          ? '文件已发送到 LitePan 服务器，正在创建上传任务'
          : `正在将文件发送给 LitePan 服务器 ${progress}%`
        updateLocalUploadTask(task.task_id, {
          status: 'pending',
          progress,
          message
        })
      }
    })

    if (response.data?.success) {
      const createdTaskId = response.data?.data?.task_id
      if (isLocalUploadTaskCanceled(task.task_id)) {
        if (createdTaskId) {
          try {
            await axios.delete(`/api/files/upload/tasks/${createdTaskId}`)
            clearLocalUploadTaskCanceledState(task.task_id)
          } catch (cleanupError) {
            console.error('清理已取消的上传任务失败:', cleanupError)
          }
        }
        removeLocalUploadTask(task.task_id)
        clearLocalUploadTaskPayload(task.task_id)
        return { success: false, canceled: true, message: '任务已取消' }
      }
      if (isLocalPauseRequested(task.task_id)) {
        if (createdTaskId) {
          try {
            await axios.post(`/api/files/upload/tasks/${createdTaskId}/pause`)
          } catch (pauseError) {
            console.error('同步暂停已创建的上传任务失败:', pauseError)
          }
          await fetchUploadTasks()
          startUploadTaskPolling()
          removeLocalUploadTask(task.task_id)
          clearLocalUploadTaskPayload(task.task_id)
          clearLocalUploadTaskPausedState(task.task_id)
          clearLocalUploadTaskCanceledState(task.task_id)
          return { success: false, paused: true, message: '任务已暂停' }
        }

        updateLocalUploadTask(task.task_id, {
          status: 'paused',
          message: '上传已暂停',
          error: ''
        })
        return { success: false, paused: true, message: '任务已暂停' }
      }
      updateLocalUploadTask(task.task_id, {
        status: 'pending',
        progress: 0,
        message: '上传任务已创建'
      })
      await fetchUploadTasks()
      removeLocalUploadTask(task.task_id)
      clearLocalUploadTaskPayload(task.task_id)
      clearLocalUploadTaskPausedState(task.task_id)
      clearLocalUploadTaskCanceledState(task.task_id)
      startUploadTaskPolling()
      return { success: true, message: response.data.message || '上传任务已创建' }
    }

    updateLocalUploadTask(task.task_id, {
      status: 'failed',
      message: '创建上传任务失败',
      error: translateUploadErrorMessage(response.data?.message || '创建上传任务失败')
    })
    return { success: false, message: response.data?.message || '创建上传任务失败' }
  } catch (error) {
    if (isLocalPauseRequested(task.task_id)) {
      updateLocalUploadTask(task.task_id, {
        status: 'paused',
        message: '上传已暂停',
        error: ''
      })
      return { success: false, paused: true, message: '任务已暂停' }
    }
    if (error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError' || isLocalUploadTaskCanceled(task.task_id)) {
      removeLocalUploadTask(task.task_id)
      clearLocalUploadTaskPayload(task.task_id)
      return { success: false, canceled: true, message: '任务已取消' }
    }
    const errorMessage = error.response?.data?.message || error.message
    updateLocalUploadTask(task.task_id, {
      status: 'failed',
      message: '创建上传任务失败',
      error: translateUploadErrorMessage(errorMessage)
    })
    return { success: false, message: `创建上传任务失败: ${errorMessage}` }
  } finally {
    releaseLocalUploadTaskController(task.task_id)
  }
}

const resolveRemoteFolderByName = async (parentId, folderName, forceRefresh = false) => {
  const params = {
    account_id: selectedAccountId.value,
    path: parentId
  }

  if (forceRefresh) {
    params.force_refresh = true
  }

  const response = await axios.get('/api/files/list', { params })

  if (!response.data?.success) {
    throw new Error(response.data?.message || `获取目录 "${folderName}" 失败`)
  }

  const entries = Array.isArray(response.data?.data) ? response.data.data : []
  const existingFolder = entries.find(item => item?.is_dir && item?.name === folderName)
  if (existingFolder?.id) {
    return existingFolder.id
  }

  const existingFile = entries.find(item => !item?.is_dir && item?.name === folderName)
  if (existingFile) {
    throw new Error(`当前目录已存在同名文件：${folderName}`)
  }

  return null
}

const listRemoteEntries = async (path, forceRefresh = false) => {
  const params = {
    account_id: selectedAccountId.value,
    path
  }

  if (forceRefresh) {
    params.force_refresh = true
  }

  const response = await axios.get('/api/files/list', { params })

  if (!response.data?.success) {
    throw new Error(response.data?.message || '获取目录内容失败')
  }

  return Array.isArray(response.data?.data) ? response.data.data : []
}

const ensureRemoteFolder = async (parentId, folderName) => {
  if (!folderName) {
    return parentId
  }

  const formData = new FormData()
  formData.append('account_id', selectedAccountId.value)
  formData.append('path', parentId)
  formData.append('name', folderName)

  try {
    const response = await axios.post('/api/files/create-folder', formData)
    if (response.data?.success) {
      return (
        response.data?.data?.folder_id ||
        response.data?.data?.folder_path ||
        await resolveRemoteFolderByName(parentId, folderName)
      )
    }
  } catch (error) {
    await wait(800)
    const fallbackFolderId = await resolveRemoteFolderByName(parentId, folderName, true)
    if (fallbackFolderId) {
      return fallbackFolderId
    }
    const errorMessage = error.response?.data?.message || error.message
    throw new Error(errorMessage || `创建文件夹 "${folderName}" 失败`)
  }

  await wait(800)
  const fallbackFolderId = await resolveRemoteFolderByName(parentId, folderName, true)
  if (fallbackFolderId) {
    return fallbackFolderId
  }

  throw new Error(`创建文件夹 "${folderName}" 失败`)
}

const buildFolderUploadTaskPlans = async (selectedFiles) => {
  const normalizedFiles = selectedFiles
    .map(file => ({
      file,
      relativePath: normalizeUploadRelativePath(file)
    }))
    .filter(item => item.relativePath)

  if (normalizedFiles.length === 0) {
    throw new Error('未读取到可上传的文件，空文件夹暂不支持')
  }

  const rootFolderNames = [...new Set(normalizedFiles.map(item => getUploadFolderRootName(item.relativePath)).filter(Boolean))]
  if (rootFolderNames.length !== 1) {
    throw new Error('当前仅支持一次上传一个文件夹')
  }

  const rootFolderName = rootFolderNames[0]
  const folderIdMap = new Map()
  folderIdMap.set('', currentPath.value)
  const skippedTasks = []

  const relativeDirectories = new Set()
  for (const item of normalizedFiles) {
    const directoryPath = getUploadRelativeDirectory(item.relativePath)
    if (!directoryPath) {
      continue
    }
    const parts = splitUploadRelativePath(directoryPath)
    const currentParts = []
    for (const part of parts) {
      currentParts.push(part)
      relativeDirectories.add(currentParts.join('/'))
    }
  }

  const sortedDirectories = [...relativeDirectories].sort((a, b) => {
    return splitUploadRelativePath(a).length - splitUploadRelativePath(b).length
  })

  for (const relativeDirectory of sortedDirectories) {
    const parts = splitUploadRelativePath(relativeDirectory)
    const folderName = parts[parts.length - 1]
    const parentRelativeDirectory = parts.slice(0, -1).join('/')
    const parentId = folderIdMap.get(parentRelativeDirectory)
    if (!parentId) {
      throw new Error(`未找到上级目录：${parentRelativeDirectory || '根目录'}`)
    }
    const folderId = await ensureRemoteFolder(parentId, folderName)
    folderIdMap.set(relativeDirectory, folderId)
  }

  const remoteNameSetMap = new Map()
  const getRemoteNameSet = async (targetPath) => {
    if (!remoteNameSetMap.has(targetPath)) {
      const entries = await listRemoteEntries(targetPath)
      remoteNameSetMap.set(
        targetPath,
        new Set(entries.map(entry => String(entry?.name || '').toLowerCase()))
      )
    }
    return remoteNameSetMap.get(targetPath)
  }

  const taskPlans = []
  let batchConflictPolicy = null

  for (const item of normalizedFiles) {
    const relativeDirectory = getUploadRelativeDirectory(item.relativePath)
    const targetPath = folderIdMap.get(relativeDirectory) || currentPath.value
    const targetDisplayPath = buildUploadTargetDisplayPath(relativeDirectory)
    const remoteNameSet = await getRemoteNameSet(targetPath)
    let conflictPolicy = 'overwrite'

    if (remoteNameSet.has(String(item.file.name || '').toLowerCase())) {
      if (!batchConflictPolicy) {
        const conflictResult = await showUploadConflictDialog(item.relativePath)
        if (!conflictResult) {
          break
        }
        if (conflictResult.applyAll) {
          batchConflictPolicy = conflictResult.policy
        }
        conflictPolicy = conflictResult.policy
      } else {
        conflictPolicy = batchConflictPolicy
      }

      if (conflictPolicy === 'skip') {
        skippedTasks.push(createSkippedUploadTask(item.file, '检测到同名文件，已跳过', {
          displayName: item.relativePath,
          targetPath,
          targetDisplayPath
        }))
        continue
      }
    }

    taskPlans.push({
      file: item.file,
      conflictPolicy,
      targetPath,
      targetDisplayPath,
      displayName: item.relativePath,
      localTask: createLocalUploadTask(item.file, {
        displayName: item.relativePath,
        targetPath,
        targetDisplayPath
      })
    })
  }

  return {
    rootFolderName,
    taskPlans,
    skippedTasks
  }
}

const handleUploadFileChange = async (event) => {
  const target = event.target
  const selectedFiles = Array.from(target?.files || [])
  if (selectedFiles.length === 0) {
    return
  }

  try {
    uploadTaskPanelOpen.value = true
    uploadTaskView.value = 'running'
    await refreshUploadTaskServerConcurrency()
    let failedCount = 0
    let batchConflictPolicy = null
    const existingNameSet = new Set(files.value.map(file => String(file.name || '').toLowerCase()))
    const taskPlans = []

    for (const selectedFile of selectedFiles) {
      let conflictPolicy = 'overwrite'
      if (existingNameSet.has(selectedFile.name.toLowerCase())) {
        if (!batchConflictPolicy) {
          const conflictResult = await showUploadConflictDialog(selectedFile.name)
          if (!conflictResult) {
            break
          }
          if (conflictResult.applyAll) {
            batchConflictPolicy = conflictResult.policy
          }
          conflictPolicy = conflictResult.policy
        } else {
          conflictPolicy = batchConflictPolicy
        }

        if (conflictPolicy === 'skip') {
          addLocalUploadTask(createSkippedUploadTask(selectedFile, '检测到同名文件，已跳过'))
          failedCount += 1
          continue
        }
      }

      taskPlans.push({
        file: selectedFile,
        conflictPolicy,
        localTask: createLocalUploadTask(selectedFile)
      })
    }

    if (taskPlans.length > 0) {
      taskPlans.forEach(item => {
        setLocalUploadTaskPayload(item.localTask.task_id, {
          file: item.file,
          conflictPolicy: item.conflictPolicy
        })
      })
      taskPlans.forEach(item => ensureUploadTaskDisplayOrder(item.localTask))
      localUploadTasks.value = [...taskPlans.map(item => item.localTask), ...localUploadTasks.value]
      startUploadTaskScheduler()
    }

  } finally {
    if (target) {
      target.value = ''
    }
  }
}

const handleUploadFolderChange = async (event) => {
  const target = event.target
  const selectedFiles = Array.from(target?.files || [])
  if (selectedFiles.length === 0) {
    return
  }

  try {
    uploadTaskPanelOpen.value = true
    uploadTaskView.value = 'running'
    await refreshUploadTaskServerConcurrency()
    uploadTaskPanelLoading.value = true
    uploadTaskPanelLoadingText.value = '正在准备上传文件夹任务...'
    const folderPlan = await buildFolderUploadTaskPlans(selectedFiles)
    const taskPlans = folderPlan.taskPlans
    uploadTaskPanelLoadingText.value = folderPlan.rootFolderName
      ? `正在载入 ${folderPlan.rootFolderName} 的上传任务...`
      : '正在载入上传任务...'
    if (Array.isArray(folderPlan.skippedTasks) && folderPlan.skippedTasks.length > 0) {
      folderPlan.skippedTasks.forEach(task => addLocalUploadTask(task))
    }

    if (folderPlan.rootFolderName) {
      await refreshFiles(true)
    }

    if (taskPlans.length === 0) {
      return
    }

    taskPlans.forEach(item => {
      setLocalUploadTaskPayload(item.localTask.task_id, {
        file: item.file,
        conflictPolicy: item.conflictPolicy,
        targetPath: item.targetPath,
        displayName: item.displayName
      })
    })
    taskPlans.forEach(item => ensureUploadTaskDisplayOrder(item.localTask))
    localUploadTasks.value = [...taskPlans.map(item => item.localTask), ...localUploadTasks.value]
    uploadTaskPanelLoading.value = false
    startUploadTaskScheduler()
  } catch (error) {
    console.error('上传文件夹准备失败:', error)
    window.appNotification.error(error.message || '准备上传文件夹失败')
  } finally {
    uploadTaskPanelLoading.value = false
    uploadTaskPanelLoadingText.value = '正在准备上传任务...'
    if (target) {
      target.value = ''
    }
  }
}

const handleFileClick = (file) => {
  if (file.is_dir) {
    navigateToFolder(file)
  } else {
    if (!isAdmin.value) {
      return
    }

    if (canPreviewFile(file)) {
      openFilePreview(file)
      return
    }

    showFileActionModal(file)
  }
}

const openFilePreview = file => {
  const previewKind = getPreviewKind(file)
  const relatedFiles = getPreviewableFiles(sortedFiles.value, [previewKind])
  if (relatedFiles.length === 0) return

  const index = relatedFiles.findIndex(item => String(item.id || item.name) === String(file.id || file.name))
  previewFiles.value = relatedFiles
  previewIndex.value = index >= 0 ? index : 0
  previewVisible.value = true
}

const closeFilePreview = () => {
  previewVisible.value = false
}

const showPreviousPreview = () => {
  if (previewFiles.value.length <= 1) return
  previewIndex.value = (previewIndex.value - 1 + previewFiles.value.length) % previewFiles.value.length
}

const showNextPreview = () => {
  if (previewFiles.value.length <= 1) return
  previewIndex.value = (previewIndex.value + 1) % previewFiles.value.length
}


// 文件夹导航防抖
let folderNavigateTimer = null
const navigateToFolder = (folder) => {
  // 如果正在加载中，忽略点击
  if (loading.value) {
    return
  }
  
  // 如果点击的是当前路径，忽略
  if (folder.id === currentPath.value) {
    return
  }
  
  // 检查是否已经存在相同路径 ID，避免重复添加
  const existingIndex = breadcrumbItems.value.findIndex(item => item.path === folder.id)
  if (existingIndex !== -1) {
    navigateToPath(folder.id)
    return
  }
  
  // 防抖，避免快速重复点击
  if (folderNavigateTimer) {
    clearTimeout(folderNavigateTimer)
  }
  
  folderNavigateTimer = setTimeout(async () => {
    // 再次检查是否正在加载
    if (loading.value) {
      return
    }

    const previousPath = currentPath.value
    const previousBreadcrumb = [...breadcrumbItems.value]
    const previousSelectedFiles = [...selectedFilesList.value]

    void fetchFolderSizeOnEnter(selectedAccountId.value, previousPath, folder.id)

    currentPath.value = folder.id

    // 更新面包屑，添加新的文件夹路径
    breadcrumbItems.value.push({
      name: folder.name,
      path: folder.id
    })

    // 立即同步更新 maxBreadcrumbItems，避免闪烁
    updateBreadcrumbLayoutSync()

    // 清除选中项（切换目录时）
    selectedFilesList.value = []

    try {
      await loadFiles()
    } catch (error) {
      currentPath.value = previousPath
      breadcrumbItems.value = previousBreadcrumb
      selectedFilesList.value = previousSelectedFiles
      updateBreadcrumbLayoutSync()
      window.appNotification.error(error?.message || '目录打开失败，路径已恢复')
    }
  }, 50) // 50ms 防抖，提升响应速度
}

// 面包屑导航防抖
let navigateTimer = null
const navigateToPath = (path) => {
  // 如果正在加载中，忽略点击
  if (loading.value) {
    return
  }
  
  if (path === currentPath.value) return

  // 防抖，避免快速重复点击
  if (navigateTimer) {
    clearTimeout(navigateTimer)
  }

  navigateTimer = setTimeout(async () => {
    // 再次检查是否正在加载
    if (loading.value) {
      return
    }

    const previousPath = currentPath.value
    const previousBreadcrumb = [...breadcrumbItems.value]
    const previousSelectedFiles = [...selectedFilesList.value]

    currentPath.value = path

    // 更新面包屑，找到对应路径索引并删除后面的项目
    const targetIndex = breadcrumbItems.value.findIndex(item => item.path === path)
    if (targetIndex !== -1) {
      // 确保面包屑长度正确，删除目标位置之后的所有项目
      const newLength = targetIndex + 1
      if (breadcrumbItems.value.length > newLength) {
        breadcrumbItems.value.splice(newLength)
      }
    } else {
      console.warn('面包屑中未找到目标路径:', path)
    }

    // 立即同步更新 maxBreadcrumbItems，避免闪烁
    updateBreadcrumbLayoutSync()

    // 清除选中项（切换目录时）
    selectedFilesList.value = []

    try {
      await loadFiles()
    } catch (error) {
      currentPath.value = previousPath
      breadcrumbItems.value = previousBreadcrumb
      selectedFilesList.value = previousSelectedFiles
      updateBreadcrumbLayoutSync()
      window.appNotification.error(error?.message || '目录打开失败，路径已恢复')
    }
  }, 50) // 50ms 防抖，提升响应速度
}

// 隐藏的面包屑项目（用于下拉菜单）
const hiddenBreadcrumbItems = computed(() => {
  if (breadcrumbItems.value.length <= maxBreadcrumbItems.value) {
    return []
  }

  // 简化逻辑：显示第一个 + ... + 最后若干项
  // 确保总显示数量等于 maxBreadcrumbItems
  const lastItemsCount = maxBreadcrumbItems.value - 2 // 减去第一个和 "..."

  // 返回中间被隐藏的项目
  return breadcrumbItems.value.slice(1, breadcrumbItems.value.length - lastItemsCount)
})

// 可见的最后几个项目
const visibleLastItems = computed(() => {
  if (breadcrumbItems.value.length <= maxBreadcrumbItems.value) {
    return []
  }

  // 简化逻辑：显示最后若干项目
  // 确保总显示数量等于 maxBreadcrumbItems
  const lastItemsCount = maxBreadcrumbItems.value - 2 // 减去第一个和 "..."

  // 返回最后几个项目
  return breadcrumbItems.value.slice(-lastItemsCount)
})

// 同步更新面包屑布局（无防抖，立即执行）
const updateBreadcrumbLayoutSync = () => {
  const screenWidth = window.innerWidth
  const itemCount = breadcrumbItems.value.length

  // 根据屏幕宽度设定开始收缩的阈值
  let startCollapseThreshold
  if (screenWidth >= 1400) {
    startCollapseThreshold = 7   // 超大屏超过 7 个开始收缩
  } else if (screenWidth >= 1200) {
    startCollapseThreshold = 6   // 大屏超过 6 个开始收缩
  } else if (screenWidth >= 1000) {
    startCollapseThreshold = 5   // 中屏超过 5 个开始收缩
  } else if (screenWidth >= 800) {
    startCollapseThreshold = 4   // 小屏超过 4 个开始收缩
  } else {
    startCollapseThreshold = 3   // 窄屏超过 3 个开始收缩
  }

  // 渐进式收缩：保持固定显示数量，逐步隐藏中间项目
  if (itemCount <= startCollapseThreshold) {
    // 未达到收缩阈值，显示全部
    maxBreadcrumbItems.value = itemCount
  } else {
    // 达到收缩阈值后，保持固定显示数量
    maxBreadcrumbItems.value = startCollapseThreshold + 1
  }
}

// 渐进式面包屑布局策略（带防抖，用于窗口大小变化）
let updateBreadcrumbLayoutTimer = null
const updateBreadcrumbLayout = () => {
  // 防抖，避免频繁调用
  if (updateBreadcrumbLayoutTimer) {
    clearTimeout(updateBreadcrumbLayoutTimer)
  }

  updateBreadcrumbLayoutTimer = setTimeout(() => {
    updateBreadcrumbLayoutSync()
  }, 50) // 缩短防抖时间，提升响应速度
}

const sortBy = (key, order = null) => {
  if (order === 'asc' || order === 'desc') {
    sortKey.value = key
    sortOrder.value = order
    return
  }

  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const handleSetSort = ({ key, order }) => {
  sortBy(key, order)
}

const {
  createFolder,
  showFileActionModal,
  handleFileDownload,
  renameFile,
  deleteFile,
  moveFile,
  batchMove,
  batchDelete,
  copyFile,
  batchCopy
} = useIndexFileActions({
  accounts,
  files,
  selectedAccountId,
  selectedFilesList,
  currentPath,
  operationLoading,
  setOperationLoading,
  loadFiles,
  refreshFiles,
  refreshAfterCreateFolder,
  naturalSort,
  confirm,
  form,
  custom,
  closeModal
})

const renameFileInline = (file, newName) => renameFile(file, newName, {
  showGlobalLoading: false,
  refresh: loadFiles
})

const createFolderInline = folderName => createFolder(folderName, {
  showGlobalLoading: false,
  refresh: refreshAfterCreateFolder
})

const deleteFileInline = (file, callbacks = {}) => deleteFile(file, {
  showGlobalLoading: false,
  refresh: loadFiles,
  ...callbacks
})

const moveFileInline = (file, callbacks = {}) => moveFile(file, {
  showGlobalLoading: false,
  ...callbacks
})

const copyFileInline = (file, callbacks = {}) => copyFile(file, {
  showGlobalLoading: false,
  ...callbacks
})

const startInlineCreateFolder = () => {
  if (!selectedAccountId.value) {
    window.appNotification.warning('请先选择一个账号')
    return
  }
  createFolderRequest.value += 1
}

const handleLogout = async () => {
  try {
    const response = await axios.post('/api/auth/logout')
    if (response.data.success) {
      window.appNotification.success('退出登录成功')
      // 更新状态
      isAdmin.value = false
      mustChangePassword.value = false
      document.body.classList.remove('admin-mode')
      // 重新检查认证状态
      checkAuthStatus()
    } else {
      window.appNotification.error('退出登录失败')
    }
  } catch (error) {
    console.error('退出登录错误:', error)
    window.appNotification.error('退出登录失败')
  }
}

// 检查管理员状态
const checkAuthStatus = async () => {
  try {
    const response = await axios.get('/api/auth/status')
    if (response.data.success) {
      const authData = response.data.data || {}
      publicIndexEnabled.value = authData.public_index_enabled !== false
      mustChangePassword.value = Boolean(authData.must_change_password)
      isAdmin.value = Boolean(authData.is_admin) && !mustChangePassword.value
      
      // 根据管理员状态添加或移除 body 类
      if (isAdmin.value) {
        document.body.classList.add('admin-mode')
      } else {
        document.body.classList.remove('admin-mode')
      }

      if (mustChangePassword.value) {
        window.appNotification.warning('检测到管理员密码仍需升级，请先进入后台修改密码')
      }

      if (!publicIndexEnabled.value && !Boolean(authData.is_admin)) {
        router.replace('/login')
        return false
      }
    }
  } catch (error) {
    console.error('获取认证状态失败:', error)
    isAdmin.value = false
    mustChangePassword.value = false
    publicIndexEnabled.value = true
    document.body.classList.remove('admin-mode')
  }
  return true
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event) => {
  if (!event.target.closest('.custom-select')) {
    dropdownOpen.value = false
  }
}

const restoreFileViewMode = () => {
  try {
    const savedViewMode = localStorage.getItem(FILE_VIEW_MODE_STORAGE_KEY)
    fileViewMode.value = ['list', 'grid'].includes(savedViewMode) ? savedViewMode : 'list'
  } catch {
    fileViewMode.value = 'list'
  }
}

const handleViewModeChange = (nextMode) => {
  if (!['list', 'grid'].includes(nextMode) || fileViewMode.value === nextMode) {
    return
  }

  fileViewMode.value = nextMode
  try {
    localStorage.setItem(FILE_VIEW_MODE_STORAGE_KEY, nextMode)
  } catch {
    // 本地存储不可用时静默降级
  }
}

// 监听面包屑变化（导航函数中已同步更新，这里主要兜底）
watch(breadcrumbItems, () => {
  // 使用防抖版本，避免重复更新
  updateBreadcrumbLayout()
}, { deep: true })

const initializePage = async () => {
  const allowPublicAccess = await checkAuthStatus()
  if (!allowPublicAccess) {
    return
  }
  await loadPublicSystemConfig()
  await loadAccounts()
  await fetchUploadTasks()
  if (activeUploadTasks.value.length > 0) {
    startUploadTaskPolling()
  }
}

onMounted(() => {
  restoreFileViewMode()
  initializePage()
  document.addEventListener('click', handleClickOutside)

  // 初始化面包屑布局
  nextTick(() => {
    updateBreadcrumbLayout()
  })

  // 监听窗口大小变化
  window.addEventListener('resize', updateBreadcrumbLayout)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateBreadcrumbLayout)
  document.removeEventListener('click', handleClickOutside)
  
  // 清理定时器
  if (navigateTimer) {
    clearTimeout(navigateTimer)
  }
  if (folderNavigateTimer) {
    clearTimeout(folderNavigateTimer)
  }
  localUploadTaskControllers.forEach(controller => controller.abort())
  localUploadTaskControllers.clear()
  localUploadTaskPayloads.clear()
  uploadTaskMetaCache.clear()
  pausedLocalUploadTaskIds.clear()
  canceledLocalUploadTaskIds.clear()
  disconnectUploadTaskStream()
  stopUploadTaskPolling()
})
</script>

<style scoped>
/* 页面作用域样式，仅补充当前页面所需样式 */

.index-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.admin-only {
  display: none;
}

.floating-account-switcher {
  position: fixed;
  left: 14px;
  top: 170px;
  z-index: 80;
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.floating-account-btn {
  position: relative;
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 10px;
  background: #fff;
  color: var(--driver-color, #6366f1);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.10);
  transition: all 0.18s ease;
}

.floating-account-btn:hover {
  transform: translateX(2px) scale(1.03);
  box-shadow:
    0 0 0 2px color-mix(in srgb, var(--driver-color, #6366f1) 28%, transparent),
    0 10px 22px rgba(15, 23, 42, 0.16);
}

.floating-account-btn.active {
  border-color: transparent;
  background: var(--driver-color, #6366f1);
  color: #fff;
  transform: scale(1.06);
  box-shadow:
    0 0 0 2px #fff,
    0 0 0 5px color-mix(in srgb, var(--driver-color, #6366f1) 35%, transparent),
    0 10px 24px color-mix(in srgb, var(--driver-color, #6366f1) 36%, transparent);
}

.floating-account-icon {
  max-width: 30px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
}

.floating-account-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  border-radius: 10px;
  background: #fff;
}

.floating-account-btn.has-logo {
  padding: 0;
  background: #fff;
  border: 0;
  overflow: visible;
}

.floating-account-btn.has-logo:hover .floating-account-logo {
  box-shadow: none;
}

.floating-account-btn.has-logo.active .floating-account-logo {
  box-shadow: none;
}

.floating-account-tooltip {
  position: absolute;
  left: calc(100% + 10px);
  top: 50%;
  transform: translateY(-50%) translateX(-4px);
  max-width: 180px;
  padding: 7px 10px;
  border-radius: 8px;
  background: #111827;
  color: #fff;
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: all 0.18s ease;
}

.floating-account-tooltip::before {
  content: '';
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  border: 5px solid transparent;
  border-right-color: #111827;
}

.floating-account-btn:hover .floating-account-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(-50%) translateX(0);
}

@media (max-width: 768px) {
  .floating-account-switcher {
    left: 50%;
    top: auto;
    bottom: calc(74px + env(safe-area-inset-bottom));
    transform: translateX(-50%);
    flex-direction: row;
    align-items: center;
    gap: 8px;
    padding: 8px;
    max-width: calc(100vw - 32px);
    overflow-x: auto;
    border: 1px solid rgba(226, 232, 240, 0.86);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.14);
    backdrop-filter: blur(10px);
  }

  .floating-account-btn {
    flex: 0 0 38px;
  }

  .floating-account-btn.active {
    transform: none;
  }

  .floating-account-btn:hover {
    transform: none;
  }

  .floating-account-tooltip {
    display: none;
  }
}

/* 当 body 带 admin-mode 类时显示管理员功能 */
:global(body.admin-mode) .admin-only {
  display: table-cell !important;
}

:global(body.admin-mode) .admin-only.btn {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

:global(body.admin-mode) .admin-only.batch-actions {
  display: flex !important;
}

.loading {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
}

.file-name {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.file-icon {
  margin-right: 8px;
  font-size: 16px;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.action-btn {
  border: none;
  background: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  font-size: 14px;
}

.action-btn:hover {
  background-color: #f0f0f0;
}

/* 移除选中账号的蓝色样式 */





.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 移动弹窗居中加载动画 */
:global(.loading-center) {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 40px 20px !important;
  text-align: center !important;
}

:global(.loading-center .loading-spinner) {
  width: 32px !important;
  height: 32px !important;
  border: 3px solid #f3f3f3 !important;
  border-top: 3px solid #3498db !important;
  border-radius: 50% !important;
  animation: spin 1s linear infinite !important;
  margin-bottom: 15px !important;
}

:global(.loading-center .loading-text) {
  color: #666 !important;
  font-size: 14px !important;
  font-weight: normal !important;
}

:global(.error-message) {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 40px 20px !important;
  text-align: center !important;
  color: #dc3545 !important;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 面包屑下拉菜单样式，使用全局样式确保动态 HTML 也能应用 */
:global(.breadcrumb-ellipsis-dropdown) {
  position: relative !important;
  display: inline-block !important;
  z-index: 6 !important;
}

:global(.breadcrumb-ellipsis) {
  color: #666 !important;
  cursor: pointer !important;
  padding: 4px 8px !important;
  border-radius: 4px !important;
  transition: all 0.2s !important;
  user-select: none !important;
}

:global(.breadcrumb-ellipsis:hover) {
  background-color: #f0f0f0 !important;
  color: #007bff !important;
}

:global(.breadcrumb-dropdown) {
  position: absolute !important;
  top: 100% !important;
  left: 50% !important;
  transform: translateX(-50%) translateY(-5px) !important;
  background: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 8px !important;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
  z-index: 10020 !important;
  min-width: 120px !important;
  opacity: 0 !important;
  visibility: hidden !important;
  transition: all 0.2s ease !important;
  padding: 4px 0 !important;
}

:global(.breadcrumb-ellipsis-dropdown:hover .breadcrumb-dropdown) {
  opacity: 1 !important;
  visibility: visible !important;
  transform: translateX(-50%) translateY(0) !important;
}

:global(.breadcrumb-dropdown-item) {
  display: block !important;
  max-width: min(240px, 28vw) !important;
  padding: 8px 16px !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  font-size: 14px !important;
  color: #374151 !important;
  margin: 2px 4px !important;
  border-radius: 6px !important;
  overflow: hidden !important;
}

:global(.breadcrumb-dropdown-item:hover) {
  background-color: #f3f4f6 !important;
  color: #111827 !important;
}

:global(.breadcrumb-dropdown-item-label) {
  display: block !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

/* 恢复备份9验证通过的首页/目录选择器滚动条样式 */
:global(*::-webkit-scrollbar) {
  width: 6px !important;
  height: 6px !important;
}

:global(*::-webkit-scrollbar-track) {
  background: transparent !important;
}

:global(*::-webkit-scrollbar-thumb) {
  background: rgba(0, 0, 0, 0.2) !important;
  border-radius: 3px !important;
  transition: all 0.2s ease !important;
}

:global(*::-webkit-scrollbar-thumb:hover) {
  background: rgba(0, 0, 0, 0.4) !important;
}

:global(*::-webkit-scrollbar-corner) {
  background: transparent !important;
}

.file-list::-webkit-scrollbar {
  width: 6px !important;
}

.file-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2) !important;
  border-radius: 3px !important;
}

:global(.file-action-modal) {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

:global(.file-action-modal-btn) {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 14px;
  background: #fff;
  color: #1e293b;
  cursor: pointer;
  font-size: 14px;
}

:global(.file-action-modal-btn.primary) {
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  border-color: transparent;
  color: #fff;
}

:global(.file-action-modal-btn.secondary) {
  background: #f8fafc;
}

:global(.file-action-modal-btn.danger) {
  color: #dc2626;
}

:global(.move-dialog-panel) {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

:global(.move-breadcrumb) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

:global(.move-breadcrumb-btn) {
  border: none;
  background: transparent;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
}

:global(.move-breadcrumb-sep) {
  color: #94a3b8;
}

:global(.move-current-path) {
  color: #475569;
  font-size: 13px;
}

:global(.move-create-row) {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

:global(.move-create-input) {
  flex: 1;
  min-width: 180px;
  border: 1px solid #dbe4ee;
  border-radius: 10px;
  padding: 10px 12px;
}

:global(.move-inline-btn),
:global(.move-footer-btn) {
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
}

:global(.move-inline-btn) {
  background: #eff6ff;
  color: #2563eb;
}

:global(.move-inline-btn.secondary),
:global(.move-footer-btn.secondary) {
  background: #f8fafc;
  color: #334155;
}

:global(.move-footer-btn.primary) {
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  color: #fff;
}

:global(.move-folder-list) {
  max-height: 320px;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px;
}

:global(.move-folder-row) {
  margin-bottom: 8px;
}

:global(.move-folder-row:last-child) {
  margin-bottom: 0;
}

:global(.move-folder-enter) {
  width: 100%;
  text-align: left;
  border: none;
  background: #fff;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
}

:global(.move-folder-enter:hover) {
  background: #f8fafc;
}

:global(.move-empty) {
  padding: 30px 12px;
  text-align: center;
  color: #94a3b8;
}

:global(.move-footer) {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}


/* 管理员标识 */
.admin-indicator {
  background: #10b981;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 400;
  letter-spacing: 0.5px;
  /* 定位在 logo 右上角 */
  position: absolute;
  top: 2px;
  right: -4px;
  display: inline-block;
  line-height: 1.2;
  text-transform: uppercase;
  opacity: 0.9;
  transition: opacity 0.2s ease;
  z-index: 10;
}

.admin-indicator:hover {
  opacity: 1;
}

.admin-indicator.warning {
  background: #f59e0b;
}

/* 退出登录按钮样式 */
.btn-logout {
  background: #ef4444 !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3) !important;
  appearance: none;
  font-family: inherit;
}

.btn-warning {
  background: #f59e0b !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3) !important;
}

#auth-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

#auth-buttons .btn {
  min-height: 40px;
  line-height: 1;
}

/* 上传任务面板 */
.upload-task-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(780px, calc(100vw - 48px));
  height: min(70vh, 720px);
  max-height: min(70vh, 720px);
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
  z-index: 121;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.upload-task-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #eef2f7;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.upload-task-panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-task-close-btn {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
}

.upload-task-close-btn:hover {
  color: #64748b;
}

.upload-task-header-info-btn {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dbe4ee;
  border-radius: 999px;
  background: #fff;
  color: #94a3b8;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 0;
  flex-shrink: 0;
}

.upload-task-header-info-btn:hover {
  color: #64748b;
  border-color: #cbd5e1;
  background: #f8fafc;
}

.upload-task-panel-body {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.upload-task-layout {
  display: flex;
  height: 100%;
  min-height: 0;
}

.upload-task-sidebar {
  width: 144px;
  flex-shrink: 0;
  border-right: 1px solid #eef2f7;
  padding: 18px 12px;
  background: #fbfcfe;
}

.upload-task-nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  background: transparent;
  color: #1f2937;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: default;
  font-size: 14px;
  font-weight: 600;
}

.upload-task-nav-item.active {
  background: #f3f6fb;
}

.upload-task-nav-icon {
  display: inline-flex;
  align-items: center;
  line-height: 0;
}

.upload-task-content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 18px 20px 20px;
  display: flex;
  flex-direction: column;
}

.upload-task-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.upload-task-batch-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-toolbar-btn {
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid #dbe4ee;
  border-radius: 10px;
  background: #fff;
  color: #475569;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.task-toolbar-btn:hover:not(:disabled) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.task-toolbar-btn.primary {
  border-color: transparent;
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  color: #fff;
  box-shadow: 0 8px 20px rgba(2, 166, 240, 0.18);
}

.task-toolbar-btn.primary:hover:not(:disabled) {
  border-color: transparent;
  background: linear-gradient(135deg, #4167d1 0%, #0295d8 100%);
}

.task-toolbar-btn:disabled {
  cursor: not-allowed;
  color: #cbd5e1;
  background: #f8fafc;
  border-color: #e5e7eb;
  box-shadow: none;
}

.task-toolbar-btn.danger {
  border-color: transparent;
  background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
  color: #fff;
}

.task-toolbar-btn.danger:hover:not(:disabled) {
  border-color: transparent;
  background: linear-gradient(135deg, #dc2626 0%, #ea580c 100%);
}

.task-toolbar-btn.danger:not(:disabled) {
  color: #fff;
}

.upload-task-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-task-tab {
  height: 32px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  background: #fff;
  color: #64748b;
  cursor: pointer;
  font-size: 13px;
}

.upload-task-tab.active {
  color: #2563eb;
  border-color: #bfdbfe;
  background: #eff6ff;
}

.upload-task-tab-count {
  min-width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
  font-size: 12px;
}

.upload-task-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.upload-task-loading-state {
  flex: 1;
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: #64748b;
}

.upload-task-loading-text {
  font-size: 14px;
  color: #64748b;
}

.upload-task-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 4px;
  border-top: 1px solid #eef2f7;
}

.upload-task-item:first-child {
  border-top: 1px solid #eef2f7;
}

.upload-task-item.completed {
  align-items: center;
}

.upload-task-item-main {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.upload-task-item.completed .upload-task-item-main {
  align-items: center;
}

.upload-task-item.completed .upload-task-title-row {
  align-items: center;
}

.upload-task-file-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  font-size: 18px;
}

.upload-task-driver-badge {
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  box-shadow: none;
}

.upload-task-file-info {
  min-width: 0;
  flex: 1;
}

.upload-task-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.upload-task-name {
  flex: 1;
  font-size: 14px;
  color: #111827;
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.upload-task-status {
  flex-shrink: 0;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #e5e7eb;
  color: #4b5563;
}

.upload-task-status.status-running,
.upload-task-status.status-pending {
  background: #dbeafe;
  color: #1d4ed8;
}

.upload-task-status.status-paused {
  background: #e0e7ff;
  color: #4338ca;
}

.upload-task-status.status-success {
  background: #dcfce7;
  color: #15803d;
}

.upload-task-status.status-skipped {
  background: #fef3c7;
  color: #b45309;
}

.upload-task-status.status-failed,
.upload-task-status.status-canceled {
  background: #fee2e2;
  color: #b91c1c;
}

.upload-task-path {
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.upload-task-progress-bar {
  margin-top: 10px;
  height: 8px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}

.upload-task-progress-inner {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  border-radius: 999px;
  transition: width 0.25s ease;
}

.upload-task-meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  color: #475569;
}

.upload-task-error {
  margin-top: 8px;
  font-size: 12px;
  color: #b91c1c;
  line-height: 1.5;
  word-break: break-all;
}

.upload-task-item-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  align-self: center;
}

.task-row-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #9ca3af;
  cursor: not-allowed;
  font-size: 13px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.task-row-btn:not(:disabled) {
  color: #94a3b8;
  cursor: pointer;
}

.task-row-btn:not(:disabled):hover {
  color: #64748b;
  background: #f1f5f9;
}

.task-row-btn.danger {
  color: #cbd5e1;
}

.task-row-btn.danger:not(:disabled) {
  color: #94a3b8;
}

.task-row-btn.danger:not(:disabled):hover {
  color: #64748b;
  background: #f1f5f9;
}

.task-btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
}

.task-btn-icon.font-icon {
  font-size: 13px;
  line-height: 1;
}

.upload-task-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
  color: #94a3b8;
  font-size: 14px;
}
/* 退出按钮不需要 hover 效果 */

</style> 
