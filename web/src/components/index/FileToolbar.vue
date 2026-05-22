<template>
  <div class="toolbar">
    <div class="toolbar-left">
      <div
        v-if="isAdmin"
        ref="createMenuRef"
        class="create-menu"
        @mouseenter="openMenu"
        @mouseleave="closeMenu"
        @focusin="openMenu"
        @focusout="handleFocusOut"
      >
        <button
          class="btn btn-primary admin-only create-menu-trigger"
          type="button"
          :aria-expanded="menuOpen"
          @click="handleTriggerClick"
        >
          <span class="create-menu-main">
            <i class="icon create-menu-icon"><SvgIcon name="folder" :size="17" /></i>
            <span class="create-menu-label">新建</span>
          </span>
          <span class="create-menu-arrow" :class="{ open: menuOpen }">
            <SvgIcon name="chevron-down" :size="14" />
          </span>
        </button>

        <div v-if="menuOpen" class="create-menu-dropdown">
          <button class="create-menu-item" type="button" @click="handleMenuAction('create-folder')">
            <span class="icon"><SvgIcon name="folder" :size="17" /></span>
            <span>新建文件夹</span>
          </button>
          <button class="create-menu-item" type="button" @click="handleMenuAction('upload-file')">
            <span class="icon"><SvgIcon name="file" :size="17" /></span>
            <span>上传文件</span>
          </button>
          <button class="create-menu-item" type="button" @click="handleMenuAction('upload-folder')">
            <span class="icon"><SvgIcon name="folder-open" :size="17" /></span>
            <span>上传文件夹</span>
          </button>
        </div>
      </div>

      <button class="btn" type="button" @click="$emit('refresh')">
        <i class="icon"><SvgIcon name="refresh" :size="17" /></i>
        <span>刷新</span>
      </button>

      <div v-if="isAdmin && selectedFilesCount > 0" class="batch-actions">
        <div
          ref="transferMenuRef"
          class="transfer-menu"
          @mouseenter="openTransferMenu"
          @mouseleave="closeTransferMenu"
          @focusin="openTransferMenu"
          @focusout="handleTransferFocusOut"
        >
          <button
            class="btn transfer-menu-trigger"
            type="button"
            :aria-expanded="transferMenuOpen"
            @click="handleTransferTriggerClick"
          >
            <i class="icon"><SvgIcon name="package" :size="17" /></i>
            <span>转移/复制</span>
            <span class="transfer-menu-arrow" :class="{ open: transferMenuOpen }">
              <SvgIcon name="chevron-down" :size="14" />
            </span>
          </button>

          <div v-if="transferMenuOpen" class="transfer-menu-dropdown">
            <button class="transfer-menu-item" type="button" @click="handleTransferAction('batch-move')">
              <span class="icon"><SvgIcon name="package" :size="17" /></span>
              <span>批量移动</span>
            </button>
            <button class="transfer-menu-item" type="button" @click="handleTransferAction('batch-copy')">
              <span class="icon"><SvgIcon name="copy" :size="17" /></span>
              <span>批量复制</span>
            </button>
          </div>
        </div>
        <button class="btn btn-danger" type="button" @click="$emit('batch-delete')">
          <i class="icon"><SvgIcon name="trash-button" :size="17" /></i>
          <span>批量删除</span>
        </button>
      </div>
    </div>

    <div class="toolbar-right">
      <button
        v-if="isAdmin"
        type="button"
        class="transfer-status-chip"
        :class="{
          active: uploadTaskActive,
          failed: uploadTaskFailed && !uploadTaskActive,
          success: uploadTaskSuccess && !uploadTaskActive && !uploadTaskFailed
        }"
        :title="uploadTaskTitle"
        @click="$emit('open-upload-tasks')"
      >
        <span class="transfer-status-icon-wrap">
          <svg
            v-if="uploadTaskSuccess && !uploadTaskActive && !uploadTaskFailed"
            class="transfer-status-icon success"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="m3.5 8.5 3 3 6-7" />
          </svg>
          <span v-else class="transfer-status-icon transfer-status-icon-svg">
            <SvgIcon name="upload" :size="14" />
          </span>
        </span>
        <span class="transfer-status-text">{{ uploadTaskLabel }}</span>
      </button>

      <div class="performance-panel" :class="{ expanded: performanceExpanded }">
        <div class="performance-metrics" :aria-hidden="!performanceExpanded">
          <span class="performance-metric">
            <span class="performance-label">响应时间</span>
            <span class="performance-value">{{ responseTime }}</span>
          </span>
          <span class="performance-divider"></span>
          <span class="performance-metric">
            <span class="performance-label">缓存命中率</span>
            <span class="performance-value">{{ cacheRate }}</span>
          </span>
        </div>
        <button
          type="button"
          class="performance-toggle"
          :aria-expanded="performanceExpanded"
          :title="performanceExpanded ? '收起性能信息' : '展开性能信息'"
          @click="togglePerformancePanel"
        >
          <span class="icon"><SvgIcon name="lightning" :size="17" /></span>
        </button>
      </div>

      <div class="view-mode-switch" role="group" aria-label="文件视图切换">
        <button
          type="button"
          class="view-mode-btn"
          :class="{ active: viewMode === 'list' }"
          title="列表视图"
          @click="$emit('update:view-mode', 'list')"
        >
          <span class="view-icon list"></span>
        </button>
        <button
          type="button"
          class="view-mode-btn"
          :class="{ active: viewMode === 'grid' }"
          title="网格视图"
          @click="$emit('update:view-mode', 'grid')"
        >
          <span class="view-icon grid"></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import SvgIcon from '../icons/SvgIcon.vue'

defineProps({
  isAdmin: {
    type: Boolean,
    default: false
  },
  selectedFilesCount: {
    type: Number,
    default: 0
  },
  viewMode: {
    type: String,
    default: 'list'
  },
  responseTime: {
    type: String,
    default: '-'
  },
  cacheRate: {
    type: String,
    default: '-'
  },
  uploadTaskCount: {
    type: Number,
    default: 0
  },
  uploadTaskActive: {
    type: Boolean,
    default: false
  },
  uploadTaskFailed: {
    type: Boolean,
    default: false
  },
  uploadTaskSuccess: {
    type: Boolean,
    default: false
  },
  uploadTaskTitle: {
    type: String,
    default: '传输列表'
  },
  uploadTaskLabel: {
    type: String,
    default: '暂无传输任务'
  }
})

const emit = defineEmits([
  'create-folder',
  'upload-file',
  'upload-folder',
  'refresh',
  'batch-move',
  'batch-copy',
  'batch-delete',
  'update:view-mode',
  'open-upload-tasks'
])

const PERFORMANCE_PANEL_STORAGE_KEY = 'litepan:index:toolbar-performance-expanded'

const menuOpen = ref(false)
const createMenuRef = ref(null)
const transferMenuOpen = ref(false)
const transferMenuRef = ref(null)
const performanceExpanded = ref(false)

const openMenu = () => {
  menuOpen.value = true
}

const closeMenu = () => {
  menuOpen.value = false
}

const handleTriggerClick = () => {
  if (window.matchMedia?.('(hover: hover)').matches) {
    menuOpen.value = true
    return
  }

  menuOpen.value = !menuOpen.value
}

const handleMenuAction = action => {
  closeMenu()
  emit(action)
}

const handleFocusOut = event => {
  if (!createMenuRef.value?.contains(event.relatedTarget)) {
    closeMenu()
  }
}

const openTransferMenu = () => {
  transferMenuOpen.value = true
}

const closeTransferMenu = () => {
  transferMenuOpen.value = false
}

const handleTransferTriggerClick = () => {
  if (window.matchMedia?.('(hover: hover)').matches) {
    transferMenuOpen.value = true
    return
  }

  transferMenuOpen.value = !transferMenuOpen.value
}

const handleTransferAction = action => {
  closeTransferMenu()
  emit(action)
}

const handleTransferFocusOut = event => {
  if (!transferMenuRef.value?.contains(event.relatedTarget)) {
    closeTransferMenu()
  }
}

const handleClickOutside = event => {
  if (!createMenuRef.value?.contains(event.target)) {
    closeMenu()
  }
  if (!transferMenuRef.value?.contains(event.target)) {
    closeTransferMenu()
  }
}

const restorePerformancePanelState = () => {
  try {
    performanceExpanded.value = localStorage.getItem(PERFORMANCE_PANEL_STORAGE_KEY) === 'true'
  } catch {
    performanceExpanded.value = false
  }
}

const persistPerformancePanelState = () => {
  try {
    localStorage.setItem(PERFORMANCE_PANEL_STORAGE_KEY, String(performanceExpanded.value))
  } catch {
    // 本地存储不可用时静默降级，不影响页面交互
  }
}

const togglePerformancePanel = () => {
  performanceExpanded.value = !performanceExpanded.value
  persistPerformancePanelState()
}

onMounted(() => {
  restorePerformancePanelState()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  min-width: 0;
}

.create-menu {
  position: relative;
}

.create-menu::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  height: 8px;
}

.create-menu-trigger {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 96px;
}

.create-menu-main {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  line-height: 1;
}

.create-menu-icon {
  transform: translateY(1px);
}

.create-menu-label {
  display: inline-flex;
  align-items: center;
  line-height: 1;
  transform: translateY(2px);
}

.create-menu-arrow {
  margin-left: 0;
  transition: transform 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.92);
  line-height: 0;
  flex-shrink: 0;
}

.create-menu-arrow.open {
  transform: rotate(180deg);
}

.create-menu-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  min-width: 160px;
  padding: 6px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
  z-index: 20;
}

.create-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: #334155;
  cursor: pointer;
  font-size: 14px;
  text-align: left;
}

.create-menu-item:hover {
  background: #f8fafc;
}

.batch-actions {
  display: flex;
  gap: 10px;
  margin-left: 20px;
  padding-left: 20px;
  border-left: 1px solid #ddd;
}

.transfer-menu {
  position: relative;
}

.transfer-menu::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  height: 8px;
}

.transfer-menu-arrow {
  transition: transform 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-regular);
  line-height: 0;
  flex-shrink: 0;
}

.transfer-menu-arrow.open {
  transform: rotate(180deg);
}

.transfer-menu-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  min-width: 160px;
  padding: 6px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
  z-index: 20;
}

.transfer-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: #334155;
  cursor: pointer;
  font-size: 14px;
  text-align: left;
}

.transfer-menu-item:hover {
  background: #f8fafc;
}

.toolbar-rect {
  height: 40px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.transfer-status-chip {
  position: relative;
  height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px 0 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.transfer-status-chip:hover {
  color: #475569;
  border-color: #cbd5e1;
  background: #f8fafc;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.transfer-status-chip.active {
  color: #2563eb;
  border-color: #bfdbfe;
  background: #eff6ff;
}

.transfer-status-chip.failed {
  color: #dc2626;
  border-color: #fecaca;
  background: #fef2f2;
}

.transfer-status-chip.success {
  color: #475569;
  border-color: #e2e8f0;
  background: #fff;
}

.transfer-status-icon-wrap {
  position: relative;
  width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.transfer-status-icon {
  font-size: 14px;
  line-height: 1;
  transform: translateY(0);
  will-change: transform, opacity;
}

.transfer-status-icon-svg {
  font-size: 0;
  line-height: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.transfer-status-chip.active .transfer-status-icon {
  animation: transferArrowLift 1.15s ease-in-out infinite;
}

.transfer-status-icon.success {
  width: 14px;
  height: 14px;
  display: block;
  color: #16a34a;
  animation: none;
  transform: none;
  will-change: auto;
}

.transfer-status-text {
  font-size: 13px;
  line-height: 1;
}

.performance-panel {
  display: inline-flex;
  align-items: center;
  min-width: 0;
}

.performance-metrics {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: 0;
  margin-right: 0;
  overflow: hidden;
  opacity: 0;
  white-space: nowrap;
  pointer-events: none;
  transition: max-width 0.22s ease, margin-right 0.22s ease, opacity 0.18s ease;
}

.performance-panel.expanded .performance-metrics {
  max-width: 280px;
  margin-right: 10px;
  opacity: 1;
  pointer-events: auto;
}

.performance-metric {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 13px;
}

.performance-label {
  color: #94a3b8;
  font-size: 12px;
}

.performance-value {
  color: #334155;
  font-weight: 500;
}

.performance-divider {
  width: 1px;
  height: 14px;
  background: #e2e8f0;
  flex-shrink: 0;
}

.performance-toggle {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.performance-toggle:hover {
  color: #475569;
  border-color: #cbd5e1;
  background: #f8fafc;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.performance-panel.expanded .performance-toggle {
  color: #2563eb;
  border-color: #bfdbfe;
  background: #eff6ff;
}

.view-mode-switch {
  display: inline-flex;
  align-items: center;
  padding: 3px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.view-mode-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-mode-btn:hover {
  color: #334155;
  background: #f8fafc;
}

.view-mode-btn.active {
  background: #eef4ff;
  color: #2563eb;
}

.view-icon {
  position: relative;
  display: block;
  width: 16px;
  height: 16px;
}

.view-icon.list::before,
.view-icon.list::after,
.view-icon.grid::before,
.view-icon.grid::after {
  content: '';
  position: absolute;
}

.view-icon.list::before {
  inset: 1px 0 auto 0;
  height: 3px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 5px 0 currentColor, 0 10px 0 currentColor;
}

.view-icon.grid::before {
  inset: 0 auto auto 0;
  width: 6px;
  height: 6px;
  border-radius: 2px;
  background: currentColor;
  box-shadow: 10px 0 0 currentColor, 0 10px 0 currentColor, 10px 10px 0 currentColor;
}

.icon {
  font-style: normal;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
  flex-shrink: 0;
}

@keyframes transferArrowLift {
  0% {
    transform: translateY(2px);
    opacity: 0.7;
  }

  45% {
    transform: translateY(-2px);
    opacity: 1;
  }

  100% {
    transform: translateY(2px);
    opacity: 0.7;
  }
}

@media (max-width: 768px) {
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }

  .toolbar-right {
    gap: 8px;
  }

  .transfer-status-chip {
    height: 38px;
    max-width: 100%;
    padding: 0 12px 0 11px;
  }

  .transfer-status-text {
    max-width: 132px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .performance-panel.expanded {
    order: 3;
    flex: 0 0 100%;
    justify-content: center;
  }

  .performance-panel.expanded .performance-metrics {
    max-width: calc(100vw - 132px);
  }

  .performance-toggle {
    width: 38px;
    height: 38px;
  }

  .view-mode-switch {
    height: 38px;
  }

  .view-mode-btn {
    width: 32px;
    height: 32px;
  }
}
</style>
