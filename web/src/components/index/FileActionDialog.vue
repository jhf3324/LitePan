<template>
  <div class="file-action-dialog">
    <div class="file-block">
      <div class="file-icon-wrap" aria-hidden="true">
        <SvgIcon :name="iconName" :size="30" />
      </div>
      <p class="file-name" :title="fileName">{{ fileName }}</p>
    </div>
    <button type="button" class="download-btn" @click="emit('resolve', { action: 'download' })">
      <svg class="download-svg" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
        <path fill="currentColor" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" />
      </svg>
      <span>下载</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SvgIcon from '../icons/SvgIcon.vue'
import { getFileIconKind } from '../../utils/fileIconKind.js'

const props = defineProps({
  fileName: {
    type: String,
    default: ''
  },
  file: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['resolve', 'cancel'])

const iconName = computed(() => {
  const f = props.file || { name: props.fileName, is_dir: false }
  return getFileIconKind(f)
})
</script>

<style scoped>
.file-action-dialog {
  padding: 14px 20px 16px;
  min-width: 260px;
  max-width: min(380px, 92vw);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 14px;
}

.file-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.file-icon-wrap {
  line-height: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.file-name {
  margin: 0;
  width: 100%;
  text-align: center;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #334155;
  line-height: 1.5;
  word-break: break-word;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.download-btn {
  align-self: center;
  width: 100%;
  max-width: 200px;
  background: linear-gradient(135deg, #4c74df 0%, #2563eb 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 9px 20px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  transition: filter 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.22);
}

.download-btn:hover {
  filter: brightness(1.05);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.download-svg {
  flex-shrink: 0;
  opacity: 0.95;
}
</style>
