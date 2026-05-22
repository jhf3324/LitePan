<template>
  <div class="batch-delete-dialog">
    <div class="dialog-head">
      <div class="dialog-title">批量删除任务</div>
      <button type="button" class="dialog-close" @click="$emit('cancel')">×</button>
    </div>
    <div class="dialog-body">
      <div>确定要删除 {{ taskCount }} 个任务吗？</div>
    </div>
    <label v-if="successCount > 0" class="dialog-checkbox">
      <input v-model="deleteUploadedFile" type="checkbox">
      <span>同时删除文件</span>
    </label>
    <div class="dialog-actions">
      <button type="button" class="dialog-btn danger" @click="emit('resolve', { deleteUploadedFile })">删除</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  taskCount: {
    type: Number,
    default: 0
  },
  successCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['resolve', 'cancel'])
const deleteUploadedFile = ref(false)
</script>

<style scoped>
.batch-delete-dialog {
  min-width: min(540px, calc(100vw - 48px));
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
  padding: 0 22px 22px;
}

.dialog-btn.danger {
  min-width: 96px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
  color: #fff;
  cursor: pointer;
}
</style>
