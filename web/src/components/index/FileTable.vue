<template>
  <div class="file-list" :class="`view-${viewMode}`" @contextmenu.prevent="openDirectoryContextMenu">
    <table v-if="viewMode === 'list'" class="file-table">
      <thead>
        <tr>
          <th v-if="isAdmin" class="checkbox-col admin-only">
            <label for="select-all-checkbox" class="sr-only">全选</label>
            <input
              id="select-all-checkbox"
              name="select-all"
              type="checkbox"
              :checked="selectAll"
              :disabled="files.length === 0"
              title="全选 / 取消全选"
              @change="toggleSelectAll($event.target.checked)"
            >
          </th>
          <th class="name-col" style="cursor: pointer;" @click="$emit('sort-by', 'name')">
            <template v-if="selectedFilesCount > 0">
              已选中 {{ selectedFilesCount }} 项
            </template>
            <template v-else>
              名称<span class="sort-indicator" :class="getSortClass('name')"></span>
            </template>
          </th>
          <th class="size-col" style="cursor: pointer;" @click="$emit('sort-by', 'size')">
            大小<span class="sort-indicator" :class="getSortClass('size')"></span>
          </th>
          <th class="time-col" style="cursor: pointer;" @click="$emit('sort-by', 'modified')">
            修改时间<span class="sort-indicator" :class="getSortClass('modified')"></span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="inlineCreatingFolder" class="inline-create-row">
          <td v-if="isAdmin" class="checkbox-col admin-only"></td>
          <td class="name-col">
            <div class="inline-rename-wrap inline-create-wrap" @click.stop @contextmenu.stop>
              <span class="file-icon">
                <SvgIcon name="folder" :size="18" />
              </span>
              <input
                ref="createFolderInputRef"
                v-model="createFolderDraft"
                class="inline-rename-input"
                :disabled="createFolderSaving"
                placeholder="输入文件夹名称"
                maxlength="100"
                @compositionstart="handleCreateFolderCompositionStart"
                @compositionend="handleCreateFolderCompositionEnd"
                @keydown.enter="handleCreateFolderEnter"
                @keydown.esc.prevent="cancelInlineCreateFolder"
                @blur="submitInlineCreateFolder"
              >
              <button
                type="button"
                class="folder-inline-btn confirm"
                :disabled="createFolderSaving"
                title="确认"
                @mousedown.prevent
                @click="submitInlineCreateFolder"
              >
                <i class="fas fa-check"></i>
              </button>
              <button
                type="button"
                class="folder-inline-btn cancel"
                :disabled="createFolderSaving"
                title="取消"
                @mousedown.prevent
                @click="cancelInlineCreateFolder"
              >
                <i class="fas fa-times"></i>
              </button>
              <span v-if="createFolderSaving" class="inline-rename-spinner" aria-label="正在创建"></span>
            </div>
          </td>
          <td class="size-col">-</td>
          <td class="time-col">-</td>
        </tr>
        <tr v-if="emptyStateText">
          <td :colspan="emptyColSpan" class="loading">{{ emptyStateText }}</td>
        </tr>
        <tr
          v-for="(file, index) in sortedFiles"
          v-else
          :key="file.id || file.name"
          :class="{ deleting: isInlineProcessing(file) }"
          @click="handleRowClick($event, file)"
          @contextmenu.prevent="openContextMenu($event, file)"
        >
          <td v-if="isAdmin" class="checkbox-col admin-only">
            <input
              :id="`file-checkbox-${index}`"
              :name="`file-checkbox-${index}`"
              type="checkbox"
              :value="file.id || file.name"
              :checked="selectedIdSet.has(file.id || file.name)"
              @change="toggleSelection(file.id || file.name, $event.target.checked)"
            >
          </td>
          <td class="name-col">
            <div
              v-if="isInlineRenaming(file)"
              class="inline-rename-wrap"
              @click.stop
              @contextmenu.stop
            >
              <span class="file-icon">
                <SvgIcon :name="getFileIconKind(file)" :size="18" />
              </span>
              <input
                ref="renameInputRef"
                v-model="renameDraft"
                class="inline-rename-input"
                :disabled="renameSaving"
                @compositionstart="handleRenameCompositionStart"
                @compositionend="handleRenameCompositionEnd"
                @keydown.enter="handleRenameEnter"
                @keydown.esc.prevent="cancelInlineRename"
                @blur="submitInlineRename"
              >
              <span v-if="renameSaving" class="inline-rename-spinner" aria-label="正在重命名"></span>
            </div>
            <div v-else class="file-name list-file-name" @click="$emit('file-click', file)">
              <span class="file-icon">
                <SvgIcon :name="getFileIconKind(file)" :size="18" />
              </span>
              <span class="file-label" :title="file.name">{{ file.name }}</span>
              <span v-if="isInlineProcessing(file)" class="inline-delete-status">
                <span class="inline-rename-spinner" aria-label="正在删除"></span>
                {{ getInlineProcessingText(file) }}
              </span>
            </div>
          </td>
          <td class="size-col">
            {{ formatEntrySize(file) }}
          </td>
          <td class="time-col">
            {{ formatDateTime(file.modified) }}
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="file-grid-wrapper">
      <div v-if="emptyStateText" class="grid-state">{{ emptyStateText }}</div>
      <template v-else>
        <div class="file-grid-toolbar">
          <div class="file-grid-toolbar-left">
            <label v-if="isAdmin" class="grid-select-all">
              <input
                type="checkbox"
                :checked="selectAll"
                :disabled="files.length === 0"
                @change="toggleSelectAll($event.target.checked)"
              >
              <span>{{ selectedFilesCount > 0 ? `已选中 ${selectedFilesCount} 项` : '全选' }}</span>
            </label>
            <span v-else class="grid-count">共 {{ sortedFiles.length }} 项</span>
          </div>

          <div ref="sortMenuRef" class="grid-sort-menu">
            <button
              type="button"
              class="grid-sort-trigger"
              :title="currentSortLabel"
              :aria-expanded="gridSortMenuOpen"
              @click="toggleGridSortMenu"
            >
              <svg
                class="grid-sort-icon"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                stroke-width="1.25"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M2 4h10" />
                <path d="M2 8h8" />
                <path d="M2 12h6" />
                <path d="m12 10 2 2 2-2" />
              </svg>
            </button>
            <div v-if="gridSortMenuOpen" class="grid-sort-dropdown">
              <div
                v-for="option in gridSortOptions"
                :key="option.key"
                class="grid-sort-row"
              >
                <span class="grid-sort-label">{{ option.label }}</span>
                <div class="grid-sort-actions">
                  <button
                    type="button"
                    class="grid-sort-order-btn"
                    :class="{ active: sortKey === option.key && sortOrder === 'asc' }"
                    @click="applyGridSort(option.key, 'asc')"
                  >
                    升序
                  </button>
                  <button
                    type="button"
                    class="grid-sort-order-btn"
                    :class="{ active: sortKey === option.key && sortOrder === 'desc' }"
                    @click="applyGridSort(option.key, 'desc')"
                  >
                    降序
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="file-grid">
          <article v-if="inlineCreatingFolder" class="file-card file-card-inline-create">
            <div class="file-card-main file-card-rename" @click.stop @contextmenu.stop>
              <span class="file-card-icon">
                <SvgIcon name="folder" :size="40" />
              </span>
              <input
                ref="createFolderInputRef"
                v-model="createFolderDraft"
                class="inline-rename-input grid-rename-input"
                :disabled="createFolderSaving"
                placeholder="文件夹名称"
                maxlength="100"
                @compositionstart="handleCreateFolderCompositionStart"
                @compositionend="handleCreateFolderCompositionEnd"
                @keydown.enter="handleCreateFolderEnter"
                @keydown.esc.prevent="cancelInlineCreateFolder"
                @blur="submitInlineCreateFolder"
              >
              <div class="grid-inline-actions">
                <button
                  type="button"
                  class="folder-inline-btn confirm"
                  :disabled="createFolderSaving"
                  title="确认"
                  @mousedown.prevent
                  @click="submitInlineCreateFolder"
                >
                  <i class="fas fa-check"></i>
                </button>
                <button
                  type="button"
                  class="folder-inline-btn cancel"
                  :disabled="createFolderSaving"
                  title="取消"
                  @mousedown.prevent
                  @click="cancelInlineCreateFolder"
                >
                  <i class="fas fa-times"></i>
                </button>
                <span v-if="createFolderSaving" class="inline-rename-spinner grid-rename-spinner" aria-label="正在创建"></span>
              </div>
            </div>
          </article>
          <article
            v-for="(file, index) in sortedFiles"
            :key="file.id || file.name"
            class="file-card"
            :class="{ selected: selectedIdSet.has(file.id || file.name), deleting: isInlineProcessing(file) }"
            @contextmenu.prevent="openContextMenu($event, file)"
          >
            <label
              v-if="isAdmin"
              class="file-card-checkbox"
              :for="`grid-file-checkbox-${index}`"
              @click.stop
            >
              <input
                :id="`grid-file-checkbox-${index}`"
                type="checkbox"
                :checked="selectedIdSet.has(file.id || file.name)"
                @change="toggleSelection(file.id || file.name, $event.target.checked)"
              >
            </label>

            <button
              v-if="!isInlineRenaming(file)"
              type="button"
              class="file-card-main"
              @click="$emit('file-click', file)"
            >
              <span class="file-card-icon">
                <SvgIcon :name="getFileIconKind(file)" :size="40" />
              </span>
              <span class="file-card-name" :title="file.name">{{ file.name }}</span>
              <span v-if="isInlineProcessing(file)" class="inline-delete-status grid-delete-status">
                <span class="inline-rename-spinner" aria-label="正在删除"></span>
                {{ getInlineProcessingText(file) }}
              </span>
              <span class="file-card-time">{{ formatDate(file.modified) }}</span>
            </button>
            <div
              v-else
              class="file-card-main file-card-rename"
              @click.stop
              @contextmenu.stop
            >
              <span class="file-card-icon">
                <SvgIcon :name="getFileIconKind(file)" :size="40" />
              </span>
              <input
                ref="renameInputRef"
                v-model="renameDraft"
                class="inline-rename-input grid-rename-input"
                :disabled="renameSaving"
                @compositionstart="handleRenameCompositionStart"
                @compositionend="handleRenameCompositionEnd"
                @keydown.enter="handleRenameEnter"
                @keydown.esc.prevent="cancelInlineRename"
                @blur="submitInlineRename"
              >
              <span v-if="renameSaving" class="inline-rename-spinner grid-rename-spinner" aria-label="正在重命名"></span>
            </div>
          </article>
        </div>
      </template>
    </div>

    <Teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="file-context-menu"
        :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
        @click.stop
      >
        <button
          v-for="item in contextMenuItems"
          :key="item.action"
          type="button"
          class="file-context-menu-item"
          :class="{ danger: item.danger }"
          @click="handleContextAction(item.action)"
        >
          <span>{{ item.label }}</span>
        </button>
      </div>

      <div
        v-if="directoryContextMenu.visible"
        class="file-context-menu"
        :style="{ left: `${directoryContextMenu.x}px`, top: `${directoryContextMenu.y}px` }"
        @click.stop
      >
        <button
          type="button"
          class="file-context-menu-item"
          @click="handleDirectoryContextAction('generate-current-strm')"
        >
          <span>生成当前目录 STRM</span>
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import SvgIcon from '../icons/SvgIcon.vue'
import { getFileIconKind } from '../../utils/fileIconKind.js'
import { formatDate, formatDateTime, formatEntrySize } from '../../utils/format.js'
import { canPreviewFile } from '../../utils/fileTypes.js'

const props = defineProps({
  isAdmin: {
    type: Boolean,
    default: false
  },
  selectedAccountId: {
    type: [Number, String],
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  files: {
    type: Array,
    default: () => []
  },
  sortedFiles: {
    type: Array,
    default: () => []
  },
  selectedFilesCount: {
    type: Number,
    default: 0
  },
  selectedFilesList: {
    type: Array,
    default: () => []
  },
  sortKey: {
    type: String,
    default: 'name'
  },
  sortOrder: {
    type: String,
    default: 'asc'
  },
  viewMode: {
    type: String,
    default: 'list'
  },
  renameFileInline: {
    type: Function,
    default: null
  },
  createFolderRequest: {
    type: Number,
    default: 0
  },
  createFolderInline: {
    type: Function,
    default: null
  },
  deleteFileInline: {
    type: Function,
    default: null
  },
  moveFileInline: {
    type: Function,
    default: null
  },
  copyFileInline: {
    type: Function,
    default: null
  }
})

const emit = defineEmits([
  'update:selected-files-list',
  'sort-by',
  'set-sort',
  'file-click',
  'download-file',
  'rename-file',
  'delete-file',
  'move-file',
  'copy-file',
  'generate-current-strm'
])

const selectedIdSet = computed(() => new Set(props.selectedFilesList))
const selectAll = computed(() => props.files.length > 0 && props.selectedFilesList.length === props.files.length)
const emptyColSpan = computed(() => (props.isAdmin ? 4 : 3))
const gridSortMenuOpen = ref(false)
const sortMenuRef = ref(null)
const renameInputRef = ref(null)
const createFolderInputRef = ref(null)
const renamingId = ref(null)
const renameDraft = ref('')
const renameSaving = ref(false)
const renameComposing = ref(false)
const inlineCreatingFolder = ref(false)
const createFolderDraft = ref('')
const createFolderSaving = ref(false)
const createFolderComposing = ref(false)
const deletingId = ref(null)
const deleteSaving = ref(false)
const movingId = ref(null)
const moveSaving = ref(false)
const copyingId = ref(null)
const copySaving = ref(false)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  file: null
})
const directoryContextMenu = ref({
  visible: false,
  x: 0,
  y: 0
})

const gridSortOptions = [
  { key: 'name', label: '文件名' },
  { key: 'modified', label: '修改时间' },
  { key: 'size', label: '文件大小' }
]

const currentSortLabel = computed(() => {
  const currentOption = gridSortOptions.find(option => option.key === props.sortKey)
  const label = currentOption?.label || '排序'
  return `${label} ${props.sortOrder === 'asc' ? '升序' : '降序'}`
})

const renamingFile = computed(() => {
  if (!renamingId.value) return null
  return props.sortedFiles.find(file => String(file.id || file.name) === String(renamingId.value)) || null
})

const emptyStateText = computed(() => {
  if (inlineCreatingFolder.value) return ''
  if (!props.selectedAccountId) return '请选择一个账号'
  if (props.loading) return '加载中...'
  if (props.files.length === 0) return '暂无文件'
  return ''
})

const contextMenuItems = computed(() => {
  const file = contextMenu.value.file
  if (!file) return []

  const items = []
  if (props.isAdmin && canPreviewFile(file)) {
    items.push({ action: 'preview', label: '预览' })
  }

  if (props.isAdmin && !file.is_dir) {
    items.push({ action: 'download', label: '下载' })
  }

  if (props.isAdmin) {
    items.push(
      { action: 'rename', label: '重命名' },
      { action: 'delete', label: '删除', danger: true },
      { action: 'move', label: '移动到' },
      { action: 'copy', label: '复制到' }
    )
  }

  return items
})

const toggleSelection = (fileId, checked) => {
  const next = new Set(props.selectedFilesList)
  if (checked) {
    next.add(fileId)
  } else {
    next.delete(fileId)
  }
  emit('update:selected-files-list', Array.from(next))
}

const toggleSelectAll = checked => {
  emit(
    'update:selected-files-list',
    checked ? props.files.map(file => file.id || file.name) : []
  )
}

const getRenameSelectionEnd = file => {
  if (file.is_dir) return file.name.length
  const dotIndex = file.name.lastIndexOf('.')
  if (dotIndex <= 0) return file.name.length
  return dotIndex
}

const focusRenameInput = async file => {
  await nextTick()
  const input = Array.isArray(renameInputRef.value) ? renameInputRef.value[0] : renameInputRef.value
  if (!input) return

  input.focus()
  const selectionEnd = getRenameSelectionEnd(file)
  input.setSelectionRange(0, selectionEnd)
}

const focusCreateFolderInput = async () => {
  await nextTick()
  const input = Array.isArray(createFolderInputRef.value) ? createFolderInputRef.value[0] : createFolderInputRef.value
  input?.focus()
}

const isInlineRenaming = file => String(file.id || file.name) === String(renamingId.value)
const isInlineDeleting = file => String(file.id || file.name) === String(deletingId.value)
const isInlineMoving = file => String(file.id || file.name) === String(movingId.value)
const isInlineCopying = file => String(file.id || file.name) === String(copyingId.value)
const isInlineProcessing = file => isInlineDeleting(file) || isInlineMoving(file) || isInlineCopying(file)
const getInlineProcessingText = file => {
  if (isInlineMoving(file)) return '移动中'
  if (isInlineCopying(file)) return '复制中'
  return '删除中'
}

const startInlineRename = async file => {
  if (!props.isAdmin || renameSaving.value) return

  renamingId.value = file.id || file.name
  renameDraft.value = file.name
  closeContextMenu()
  await focusRenameInput(file)
}

const cancelInlineRename = () => {
  if (renameSaving.value) return
  renamingId.value = null
  renameDraft.value = ''
  renameComposing.value = false
}

const handleRenameCompositionStart = () => {
  renameComposing.value = true
}

const handleRenameCompositionEnd = () => {
  renameComposing.value = false
}

const handleRenameEnter = event => {
  if (event.isComposing || renameComposing.value) return

  event.preventDefault()
  submitInlineRename()
}

const startInlineCreateFolder = async () => {
  if (!props.isAdmin || createFolderSaving.value) return

  cancelInlineRename()
  closeContextMenu()
  inlineCreatingFolder.value = true
  createFolderDraft.value = ''
  await focusCreateFolderInput()
}

const cancelInlineCreateFolder = () => {
  if (createFolderSaving.value) return
  inlineCreatingFolder.value = false
  createFolderDraft.value = ''
  createFolderComposing.value = false
}

const handleCreateFolderCompositionStart = () => {
  createFolderComposing.value = true
}

const handleCreateFolderCompositionEnd = () => {
  createFolderComposing.value = false
}

const handleCreateFolderEnter = event => {
  if (event.isComposing || createFolderComposing.value) return

  event.preventDefault()
  submitInlineCreateFolder()
}

const submitInlineCreateFolder = async () => {
  if (!inlineCreatingFolder.value || createFolderSaving.value) return

  const folderName = createFolderDraft.value
  if (!folderName.trim()) {
    cancelInlineCreateFolder()
    return
  }

  if (!props.createFolderInline) {
    cancelInlineCreateFolder()
    return
  }

  createFolderSaving.value = true
  const success = await props.createFolderInline(folderName)
  createFolderSaving.value = false

  if (success) {
    cancelInlineCreateFolder()
    return
  }

  await focusCreateFolderInput()
}

const startInlineDelete = async file => {
  if (!props.isAdmin || deleteSaving.value) return

  closeContextMenu()
  cancelInlineRename()
  if (!props.deleteFileInline) {
    emit('delete-file', file)
    return
  }

  await props.deleteFileInline(file, {
    onRequestStart: () => {
      deletingId.value = file.id || file.name
      deleteSaving.value = true
    },
    onRequestEnd: () => {
      deleteSaving.value = false
      deletingId.value = null
    }
  })
}

const startInlineMove = async file => {
  if (!props.isAdmin || moveSaving.value) return

  closeContextMenu()
  cancelInlineRename()
  if (!props.moveFileInline) {
    emit('move-file', file)
    return
  }

  await props.moveFileInline(file, {
    onRequestStart: () => {
      movingId.value = file.id || file.name
      moveSaving.value = true
    },
    onRequestEnd: () => {
      moveSaving.value = false
      movingId.value = null
    }
  })
}

const startInlineCopy = async file => {
  if (!props.isAdmin || copySaving.value) return

  closeContextMenu()
  cancelInlineRename()
  if (!props.copyFileInline) {
    emit('copy-file', file)
    return
  }

  await props.copyFileInline(file, {
    onRequestStart: () => {
      copyingId.value = file.id || file.name
      copySaving.value = true
    },
    onRequestEnd: () => {
      copySaving.value = false
      copyingId.value = null
    }
  })
}

const submitInlineRename = async () => {
  const file = renamingFile.value
  if (!file || renameSaving.value) return

  const newName = renameDraft.value
  if (newName.trim() === file.name) {
    cancelInlineRename()
    return
  }

  if (!props.renameFileInline) {
    emit('rename-file', file)
    cancelInlineRename()
    return
  }

  renameSaving.value = true
  const success = await props.renameFileInline(file, newName)
  renameSaving.value = false

  if (success) {
    cancelInlineRename()
    return
  }

  await focusRenameInput(file)
}

const handleRowClick = (event, file) => {
  if (!props.isAdmin) return

  const target = event.target
  if (target?.type === 'checkbox') return
  if (target?.closest('.file-name')) return
  if (target?.closest('.inline-rename-wrap')) return
  if (target?.closest('.action-buttons')) return

  const row = event.currentTarget
  if (!row) return

  const rowRect = row.getBoundingClientRect()
  const clickX = event.clientX - rowRect.left
  if (clickX > 70) return

  const fileId = file.id || file.name
  toggleSelection(fileId, !selectedIdSet.value.has(fileId))
}

const getSortClass = key => {
  if (props.sortKey !== key) return ''
  return props.sortOrder
}




const toggleGridSortMenu = () => {
  gridSortMenuOpen.value = !gridSortMenuOpen.value
}

const applyGridSort = (key, order) => {
  emit('set-sort', { key, order })
  gridSortMenuOpen.value = false
}

const closeContextMenu = () => {
  contextMenu.value.visible = false
  directoryContextMenu.value.visible = false
}

const openContextMenu = (event, file) => {
  if (renameSaving.value || deleteSaving.value || moveSaving.value || isInlineRenaming(file)) return

  directoryContextMenu.value.visible = false
  contextMenu.value.file = file

  const itemCount = file.is_dir && !props.isAdmin ? 0 : contextMenuItems.value.length
  if (itemCount === 0) {
    closeContextMenu()
    return
  }

  const menuWidth = 156
  const menuHeight = itemCount * 38 + 14
  contextMenu.value.x = Math.max(8, Math.min(event.clientX, window.innerWidth - menuWidth - 8))
  contextMenu.value.y = Math.max(8, Math.min(event.clientY, window.innerHeight - menuHeight - 8))
  contextMenu.value.visible = true
  gridSortMenuOpen.value = false
}

const openDirectoryContextMenu = event => {
  if (!props.isAdmin || props.loading || renameSaving.value || deleteSaving.value || moveSaving.value) return
  const target = event.target
  if (
    target?.closest('tbody tr') ||
    target?.closest('.file-card') ||
    target?.closest('.inline-rename-wrap') ||
    target?.closest('button') ||
    target?.closest('input') ||
    target?.closest('.file-context-menu')
  ) {
    return
  }

  const menuWidth = 188
  const menuHeight = 52
  directoryContextMenu.value.x = Math.max(8, Math.min(event.clientX, window.innerWidth - menuWidth - 8))
  directoryContextMenu.value.y = Math.max(8, Math.min(event.clientY, window.innerHeight - menuHeight - 8))
  directoryContextMenu.value.visible = true
  contextMenu.value.visible = false
  gridSortMenuOpen.value = false
}

const handleContextAction = action => {
  const file = contextMenu.value.file
  closeContextMenu()
  if (!file) return

  if (action === 'download') emit('download-file', file)
  if (action === 'preview') emit('file-click', file)
  if (action === 'rename') startInlineRename(file)
  if (action === 'delete') startInlineDelete(file)
  if (action === 'move') startInlineMove(file)
  if (action === 'copy') startInlineCopy(file)
}

const handleDirectoryContextAction = action => {
  closeContextMenu()
  if (action === 'generate-current-strm') emit('generate-current-strm')
}

const handleClickOutside = event => {
  if (!sortMenuRef.value?.contains(event.target)) {
    gridSortMenuOpen.value = false
  }
  closeContextMenu()
}

const handleContextKeydown = event => {
  if (event.key === 'Escape') {
    closeContextMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleContextKeydown)
  window.addEventListener('resize', closeContextMenu)
  window.addEventListener('scroll', closeContextMenu, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleContextKeydown)
  window.removeEventListener('resize', closeContextMenu)
  window.removeEventListener('scroll', closeContextMenu, true)
})

watch(() => props.createFolderRequest, (requestCount, previousCount) => {
  if (requestCount && requestCount !== previousCount) {
    startInlineCreateFolder()
  }
})
</script>

<style scoped>
.loading,
.grid-state {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
}

.file-list.view-grid {
  overflow: visible;
}

.file-table {
  width: 100%;
  border-radius: 0 0 12px 12px;
  box-shadow: none;
}

.list-file-name {
  min-width: 0;
}

.file-table th,
.file-table td {
  height: 54px;
  padding-top: 8px;
  padding-bottom: 8px;
  vertical-align: middle;
  box-sizing: border-box;
}

.file-table th {
  height: 52px;
  background: #fafbfc;
}

.file-table tr.deleting {
  color: #94a3b8;
}

.file-table tr.deleting .file-icon,
.file-card.deleting .file-card-icon,
.file-card.deleting .file-card-name,
.file-card.deleting .file-card-time {
  opacity: 0.55;
}

.checkbox-col {
  width: 44px;
  text-align: center;
  vertical-align: middle;
}

.checkbox-col input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin: 0;
  display: inline-grid;
  place-content: center;
  appearance: none;
  border: 1px solid #d6dde8;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  transition: all 0.16s ease;
}

.checkbox-col input[type="checkbox"]::before {
  content: "";
  width: 8px;
  height: 8px;
  transform: scale(0);
  clip-path: polygon(14% 44%, 0 58%, 39% 97%, 100% 19%, 86% 6%, 37% 68%);
  background: #fff;
  transition: transform 0.12s ease-in-out;
}

.checkbox-col input[type="checkbox"]:hover {
  border-color: #aeb9ca;
  background: #f8fafc;
}

.checkbox-col input[type="checkbox"]:checked {
  border-color: #3b82f6;
  background: #3b82f6;
}

.checkbox-col input[type="checkbox"]:checked::before {
  transform: scale(1);
}

.file-name {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.file-icon {
  margin-right: 8px;
  line-height: 0;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
}

.file-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.inline-rename-wrap {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
}

.inline-rename-input {
  width: min(520px, 100%);
  min-width: 120px;
  height: 36px;
  border: 1px solid #2196F3;
  border-radius: 8px;
  background: #fff;
  color: #0f172a;
  font-size: 14px;
  padding: 0 12px;
  outline: none;
  box-shadow: none;
}

.inline-rename-input:disabled {
  color: #64748b;
  background: #f8fafc;
}

.inline-create-row {
  background: #fff;
}

.inline-create-wrap {
  gap: 8px;
}

.inline-create-wrap .inline-rename-input {
  width: min(320px, 48vw);
  flex: 0 1 320px;
}

.folder-inline-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  font-size: 13px;
  flex: 0 0 auto;
}

.folder-inline-btn.confirm {
  background: #2196F3;
}

.folder-inline-btn.cancel {
  background: #d1d5db;
}

.folder-inline-btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.inline-rename-spinner {
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
  border: 2px solid #dbeafe;
  border-top-color: #3b82f6;
  border-radius: 999px;
  animation: inline-rename-spin 0.72s linear infinite;
}

.inline-delete-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 10px;
  color: #94a3b8;
  font-size: 12px;
  white-space: nowrap;
}

.grid-delete-status {
  margin-left: 0;
}

@keyframes inline-rename-spin {
  to {
    transform: rotate(360deg);
  }
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1;
  color: #475569;
  transition: all 0.18s ease;
}

.action-btn:hover {
  background: #f1f5f9;
}

.action-btn.rename:hover {
  color: #16a34a;
}

.action-btn.delete:hover {
  color: #dc2626;
}

.file-grid-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 16px 16px;
  min-height: clamp(340px, calc(100vh - 430px), 520px);
}

.file-grid-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.file-grid-toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
  font-size: 13px;
}

.grid-select-all {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.grid-count {
  color: #94a3b8;
}

.grid-sort-menu {
  position: relative;
}

.grid-sort-trigger {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.grid-sort-trigger:hover {
  color: #334155;
  background: #f1f5f9;
}

.grid-sort-icon {
  width: 16px;
  height: 16px;
  display: block;
  flex: 0 0 auto;
}

.grid-sort-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 188px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.12);
  z-index: 20;
}

.grid-sort-row + .grid-sort-row {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.grid-sort-label {
  display: block;
  margin-bottom: 6px;
  color: #475569;
  font-size: 13px;
  font-weight: 500;
}

.grid-sort-actions {
  display: flex;
  gap: 8px;
}

.grid-sort-order-btn {
  flex: 1;
  height: 30px;
  border: none;
  border-radius: 8px;
  background: #f8fafc;
  color: #64748b;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.grid-sort-order-btn:hover {
  background: #eef2ff;
  color: #334155;
}

.grid-sort-order-btn.active {
  background: #eef4ff;
  color: #2563eb;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(142px, 1fr));
  gap: 14px 12px;
}

.file-card {
  position: relative;
  min-width: 0;
  border-radius: 14px;
}

.file-card-main {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 10px 14px;
  border: none;
  border-radius: 14px;
  background: transparent;
  cursor: pointer;
  text-align: center;
  transition: background-color 0.18s ease;
}

.file-card:hover .file-card-main,
.file-card.selected .file-card-main {
  background: #f3f4f6;
}

.file-card.selected .file-card-main {
  background: #edf2ff;
}

.file-card-icon {
  width: 56px;
  height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
}

.file-card-name {
  width: 100%;
  color: #0f172a;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.35;
  font-family: "Microsoft YaHei", "微软雅黑", "SimSun", "宋体", sans-serif;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-card-time {
  width: 100%;
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-card-rename {
  cursor: default;
}

.grid-rename-input {
  width: 100%;
  max-width: 132px;
  text-align: center;
  font-size: 13px;
}

.grid-rename-spinner {
  margin-top: 2px;
}

.file-card-inline-create .file-card-main {
  background: #f8fafc;
}

.grid-inline-actions {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
}

.file-card-checkbox,
.file-card-menu {
  position: absolute;
  top: 8px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease;
  z-index: 2;
}

.file-card-checkbox {
  left: 8px;
  display: inline-flex;
  align-items: center;
}

.file-card-menu {
  right: 8px;
}

.file-card:hover .file-card-checkbox,
.file-card:hover .file-card-menu,
.file-card.selected .file-card-checkbox,
.file-card.selected .file-card-menu {
  opacity: 1;
  pointer-events: auto;
}

.file-card-menu-trigger {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #475569;
  cursor: pointer;
  line-height: 0;
  padding: 0;
}

.file-card-menu-trigger:hover {
  background: #fff;
}

.file-card-menu-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 108px;
  padding: 6px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: all 0.18s ease;
}

.file-card-menu:hover .file-card-menu-dropdown,
.file-card-menu:focus-within .file-card-menu-dropdown {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.file-card-menu-item {
  width: 100%;
  border: none;
  background: transparent;
  padding: 8px 10px;
  border-radius: 8px;
  color: #334155;
  text-align: left;
  cursor: pointer;
  font-size: 13px;
}

.file-card-menu-item:hover {
  background: #f8fafc;
}

.file-card-menu-item.danger:hover {
  color: #dc2626;
}

.file-context-menu {
  position: fixed;
  z-index: 3000;
  min-width: 156px;
  padding: 8px;
  border: 1px solid rgba(226, 232, 240, 0.52);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.10);
  backdrop-filter: blur(12px);
}

.file-context-menu-item {
  width: 100%;
  height: 36px;
  display: flex;
  align-items: center;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: #334155;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
  padding: 0 20px;
  transition: all 0.16s ease;
}

.file-context-menu-item:hover {
  background: #f8fafc;
  color: #2563eb;
}

.file-context-menu-item.danger:hover {
  background: #fef2f2;
  color: #dc2626;
}

@media (max-width: 768px) {
  .file-grid {
    grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
    gap: 12px 10px;
  }

  .file-grid-wrapper {
    padding: 10px 12px 12px;
    min-height: clamp(300px, calc(100vh - 390px), 460px);
  }
}

@media (max-width: 480px) {
  .file-grid-toolbar {
    align-items: flex-start;
  }
}
</style>
