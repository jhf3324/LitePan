<template>
  <div class="conflict-dialog">
    <div class="dialog-head">
      <div class="dialog-title">提示</div>
      <button type="button" class="dialog-close" @click="$emit('cancel')">×</button>
    </div>
    <div class="dialog-body">
      <div>检测到同名文件，文件名</div>
      <div class="file-name">{{ fileName }}</div>
      <div class="body-subtitle">已存在，请选择处理方式：</div>
    </div>
    <label class="dialog-checkbox">
      <input v-model="applyAll" type="checkbox">
      <span>应用到本次全部</span>
    </label>
    <div class="dialog-actions">
      <button type="button" class="dialog-btn secondary" @click="resolveAction('skip')">跳过</button>
      <button type="button" class="dialog-btn secondary" @click="resolveAction('overwrite')">覆盖</button>
      <button type="button" class="dialog-btn primary" @click="resolveAction('rename')">保留两者</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  fileName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['resolve', 'cancel'])
const applyAll = ref(false)

const resolveAction = (policy) => {
  emit('resolve', {
    policy,
    applyAll: applyAll.value
  })
}
</script>

<style scoped>
.conflict-dialog {
  min-width: min(520px, calc(100vw - 48px));
}

.dialog-head,
.dialog-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-title {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.dialog-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.dialog-body {
  margin-top: 18px;
  color: #475569;
  font-size: 15px;
  line-height: 1.8;
}

.file-name {
  margin-top: 4px;
  color: #111827;
  word-break: break-all;
}

.body-subtitle {
  margin-top: 4px;
}

.dialog-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
}

.dialog-actions {
  justify-content: flex-end;
  gap: 10px;
  margin-top: 22px;
}

.dialog-btn {
  min-width: 88px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid #dbe3ee;
}

.dialog-btn.secondary {
  background: #fff;
  color: #475569;
}

.dialog-btn.primary {
  min-width: 100px;
  border: none;
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  color: #fff;
}
</style>
