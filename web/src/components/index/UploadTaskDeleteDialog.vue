<template>
  <div class="task-delete-dialog">
    <div class="dialog-head">
      <div class="dialog-title">删除任务</div>
      <button type="button" class="dialog-close" @click="$emit('cancel')">×</button>
    </div>
    <div class="dialog-body">
      <div>确定要删除任务</div>
      <div class="dialog-name">{{ taskName }}</div>
      <div v-if="allowDeleteUploadedFile" class="dialog-tip">如需同时删除网盘中的文件，请勾选下方选项。</div>
    </div>
    <label v-if="allowDeleteUploadedFile" class="dialog-checkbox">
      <input v-model="deleteUploadedFile" type="checkbox">
      <span>同时删除文件</span>
    </label>
    <div class="dialog-actions">
      <button type="button" class="dialog-btn danger" @click="emitResolve()">删除</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  taskName: {
    type: String,
    default: ''
  },
  allowDeleteUploadedFile: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['resolve', 'cancel'])
const deleteUploadedFile = ref(false)

const emitResolve = () => {
  emit('resolve', { deleteUploadedFile: props.allowDeleteUploadedFile && deleteUploadedFile.value })
}
</script>

<style scoped>
.task-delete-dialog {
  min-width: min(520px, calc(100vw - 48px));
  width: 100%;
  box-sizing: border-box;
}

.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 22px 0;
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
  padding: 18px 22px 16px;
  color: #475569;
  font-size: 15px;
  line-height: 1.8;
}

.dialog-name {
  margin-top: 4px;
  color: #111827;
  word-break: break-all;
}

.dialog-tip {
  margin-top: 6px;
}

.dialog-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 22px 18px;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0 22px 22px;
}

.dialog-btn {
  min-width: 96px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
}

.dialog-btn.secondary {
  border: 1px solid #dbe3ee;
  background: #fff;
  color: #475569;
}

.dialog-btn.danger {
  border: none;
  background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
  color: #fff;
}
</style>
