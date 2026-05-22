<template>
  <div class="ldb-overlay" @click.self="$emit('cancel')">
    <div class="ldb-modal" @click.stop>
      <div class="ldb-header">
        <h3>选择容器内目录</h3>
        <button class="ldb-close" type="button" @click="$emit('cancel')">×</button>
      </div>

      <div class="ldb-pathbar">
        <input
          v-model="pathInput"
          class="ldb-path-input"
          placeholder="直接输入或浏览选择"
          @keyup.enter="go(pathInput)"
        >
        <button class="ldb-btn" type="button" @click="go(pathInput)">前往</button>
        <button class="ldb-btn" type="button" :disabled="!parent" @click="go(parent)">
          ← 上一级
        </button>
      </div>

      <div v-if="error" class="ldb-error">{{ error }}</div>

      <div class="ldb-quick">
        <span class="ldb-quick-label">常用：</span>
        <button v-for="p in quickPaths" :key="p" class="ldb-chip" type="button" @click="go(p)">
          {{ p }}
        </button>
      </div>

      <div class="ldb-list">
        <div v-if="loading" class="ldb-state">加载中...</div>
        <div v-else-if="dirs.length === 0 && !error" class="ldb-state">该目录下没有子目录</div>
        <button
          v-for="d in dirs"
          :key="d.path"
          type="button"
          class="ldb-row"
          @click="go(d.path)"
          @dblclick="confirm(d.path)"
        >
          <i class="fas fa-folder"></i>
          <span class="ldb-row-name">{{ d.name }}</span>
        </button>
      </div>

      <div class="ldb-footer">
        <span class="ldb-footer-current">当前：<code>{{ currentPath || '-' }}</code></span>
        <div class="ldb-actions">
          <button class="ldb-btn" type="button" @click="$emit('cancel')">取消</button>
          <button class="ldb-btn primary" type="button" :disabled="!currentPath" @click="confirm()">
            选择该目录
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  initialPath: { type: String, default: '' },
})
const emit = defineEmits(['resolve', 'cancel'])

const loading = ref(false)
const error = ref('')
const dirs = ref([])
const currentPath = ref('')
const parent = ref(null)
const pathInput = ref('')

const quickPaths = ['/app/strm', '/app', '/data', '/mnt', '/media', '/']

const load = async (path) => {
  loading.value = true
  error.value = ''
  try {
    const resp = await axios.get('/api/admin/local-fs/browse', {
      params: path ? { path } : {},
    })
    const data = resp.data?.data
    if (resp.data?.success && data) {
      currentPath.value = data.path
      parent.value = data.parent
      dirs.value = data.dirs || []
      pathInput.value = data.path
    } else {
      error.value = resp.data?.message || '加载失败'
      if (data) {
        currentPath.value = data.path || ''
        parent.value = data.parent
        dirs.value = []
        pathInput.value = currentPath.value
      }
    }
  } catch (e) {
    error.value = e?.response?.data?.message || e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

const go = (path) => {
  if (!path) return
  load(path.trim())
}

const confirm = (overridePath = null) => {
  const finalPath = overridePath || currentPath.value
  if (finalPath) {
    emit('resolve', finalPath)
  }
}

onMounted(() => {
  load(props.initialPath || '')
})
</script>

<style scoped>
.ldb-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 200000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.ldb-modal {
  background: #fff;
  border-radius: 12px;
  width: 560px;
  max-width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
}

.ldb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.ldb-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.ldb-close {
  background: none;
  border: 0;
  font-size: 22px;
  color: #6b7280;
  cursor: pointer;
  line-height: 1;
}

.ldb-pathbar {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
}

.ldb-path-input {
  flex: 1;
  height: 34px;
  padding: 0 10px;
  font-size: 13px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.ldb-path-input:focus {
  border-color: #3b82f6;
}

.ldb-btn {
  height: 34px;
  padding: 0 12px;
  font-size: 13px;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  color: #374151;
}

.ldb-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.ldb-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ldb-btn.primary {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

.ldb-btn.primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.ldb-btn.ghost {
  background: transparent;
}

.ldb-error {
  margin: 0 20px 8px;
  padding: 6px 10px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #b91c1c;
  font-size: 12px;
}

.ldb-quick {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 20px 8px;
  align-items: center;
}

.ldb-quick-label {
  font-size: 12px;
  color: #6b7280;
  margin-right: 2px;
}

.ldb-chip {
  font-size: 12px;
  padding: 2px 10px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  color: #374151;
  cursor: pointer;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.ldb-chip:hover {
  background: #e5e7eb;
}

.ldb-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 12px;
  margin: 0 8px;
  min-height: 200px;
}

.ldb-state {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}

.ldb-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
  text-align: left;
}

.ldb-row:hover {
  background: #f3f4f6;
}

.ldb-row i {
  color: #fbbf24;
  width: 16px;
}

.ldb-row-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ldb-footer {
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.ldb-footer-current {
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.ldb-footer-current code {
  background: #f3f4f6;
  padding: 1px 6px;
  border-radius: 4px;
  color: #374151;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.ldb-actions {
  display: flex;
  gap: 8px;
}
</style>
