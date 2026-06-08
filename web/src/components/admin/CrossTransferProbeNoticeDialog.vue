<template>
  <div class="notice-dialog">
    <div class="notice-title-row">
      <div class="notice-title">试探秒传流程：</div>
      <button type="button" class="notice-close" @click="$emit('cancel')">×</button>
    </div>

    <div class="notice-card">
      <div class="notice-flow">
        <div class="notice-node">
          <div class="notice-icon"><SvgIcon name="folder" :size="26" /></div>
          <span>源文件指纹</span>
        </div>
        <div class="notice-arrow">→</div>
        <div class="notice-node wide">
          <div class="notice-icon"><SvgIcon name="monitor" :size="26" /></div>
          <span>LitePan 试探</span>
        </div>
        <div class="notice-arrow">→</div>
        <div class="notice-node">
          <div class="notice-icon"><SvgIcon name="cloud" :size="26" /></div>
          <span>目标盘临时目录</span>
        </div>
      </div>
    </div>

    <div class="notice-tips">
      <div class="notice-tip">
        <span class="notice-tip-bar" aria-hidden="true"></span>
        <span>先试探可确认哪些文件能秒传；若直接传输且选了「覆盖」，误覆盖后无法撤销。</span>
      </div>
      <div class="notice-tip">
        <span class="notice-tip-bar" aria-hidden="true"></span>
        <span>部分网盘（如 123）无法预检秒传，试探在临时目录进行，不影响目标目录。</span>
      </div>
      <div class="notice-tip">
        <span class="notice-tip-bar" aria-hidden="true"></span>
        <span>试探结束后自动删除临时目录，删除后可能留在回收站，请用官方客户端清空。</span>
      </div>
    </div>

    <label class="notice-checkbox">
      <input v-model="skipNextTime" type="checkbox">
      <span>不再提示</span>
    </label>

    <div class="notice-actions">
      <button type="button" class="notice-confirm" @click="confirmNotice">我知道了，继续</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SvgIcon from '../icons/SvgIcon.vue'

const props = defineProps({
  skipChecked: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['resolve', 'cancel'])

const skipNextTime = ref(props.skipChecked)

const confirmNotice = () => {
  emit('resolve', {
    confirmed: true,
    skipNextTime: skipNextTime.value
  })
}
</script>

<style scoped>
.notice-dialog {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.notice-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.notice-title {
  font-size: 17px;
  font-weight: 700;
  color: #111827;
  line-height: 1.5;
}

.notice-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.notice-card {
  padding: 14px 16px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.notice-flow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1.2fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
}

.notice-node {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 8px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #334155;
  font-size: 13px;
  text-align: center;
}

.notice-node.wide {
  min-width: 0;
}

.notice-icon {
  line-height: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.notice-arrow {
  color: #94a3b8;
  font-size: 20px;
}

.notice-tips {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #475569;
  font-size: 14px;
  line-height: 1.8;
}

.notice-tip {
  display: flex;
  align-items: stretch;
  gap: 10px;
}

.notice-tip-bar {
  flex-shrink: 0;
  width: 4px;
  border-radius: 999px;
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
}

.notice-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 18px;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
}

.notice-actions {
  display: flex;
  justify-content: center;
  margin-top: 18px;
}

.notice-confirm {
  min-width: 168px;
  height: 38px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #4c74df 0%, #02a6f0 100%);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

@media (max-width: 640px) {
  .notice-flow {
    grid-template-columns: 1fr;
  }

  .notice-arrow {
    justify-self: center;
    transform: rotate(90deg);
  }
}
</style>
