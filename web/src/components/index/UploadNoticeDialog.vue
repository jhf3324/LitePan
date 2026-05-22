<template>
  <div class="notice-dialog">
    <div class="notice-title-row">
      <div class="notice-title">上传功能受浏览器影响，流程为：</div>
      <button type="button" class="notice-close" @click="$emit('cancel')">×</button>
    </div>

    <div class="notice-card">
      <div class="notice-flow">
        <div class="notice-node">
          <div class="notice-icon"><SvgIcon name="user" :size="26" /></div>
          <span>用户</span>
        </div>
        <div class="notice-arrow">→</div>
        <div class="notice-node wide">
          <div class="notice-icon"><SvgIcon name="monitor" :size="26" /></div>
          <span>LitePan服务器</span>
        </div>
        <div class="notice-arrow">→</div>
        <div class="notice-node">
          <div class="notice-icon"><SvgIcon name="cloud" :size="26" /></div>
          <span>网盘</span>
        </div>
      </div>
    </div>

    <div class="notice-tips">
      <div class="notice-tip">建议电脑和服务器在同一内网，否则请使用网盘官方客户端上传。</div>
      <div class="notice-tip">上传速度会受服务器网络带宽影响。</div>
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
  position: relative;
  padding-left: 14px;
}

.notice-tip::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 4px;
  height: 18px;
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
  .notice-dialog {
    width: 100%;
    max-width: 100%;
  }

  .notice-flow {
    grid-template-columns: 1fr;
  }

  .notice-arrow {
    justify-self: center;
    transform: rotate(90deg);
  }
}
</style>
