<template>
  <div class="cross-pick-shell">
    <div class="cross-pick-accounts">
      <div class="cpa-title">选择账号</div>
      <div class="cpa-list">
        <div v-if="!accounts.length" class="cpa-empty">
          没有可用的{{ panName }}账号<br>请先到「存储管理」添加
        </div>
        <div
          v-for="a in accounts"
          :key="a.id"
          class="cpa-item"
          :class="{ active: a.id === selAcc }"
          @click="selAcc = a.id"
        >
          <span class="cpa-name">{{ a.name }}</span>
          <span class="cpa-sub">{{ panName }}</span>
        </div>
      </div>
    </div>

    <div class="cross-pick-folder">
      <FolderSelectorModal
        v-if="selAcc"
        :key="selAcc"
        :account-id="selAcc"
        :title="folderTitle"
        :initial-path="selAcc === initialAccId ? initialPath : ''"
        :show-refresh-button="true"
        @resolve="onResolve"
        @cancel="$emit('cancel')"
      />
      <div v-else class="cpa-empty cpa-empty-folder">请选择左侧账号</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FolderSelectorModal from '../common/FolderSelectorModal.vue'

const props = defineProps({
  mode: { type: String, default: 'src' },
  panName: { type: String, default: '' },
  accounts: { type: Array, default: () => [] },
  initialAccId: { type: [Number, String], default: '' },
  initialPath: { type: String, default: '' }
})

const emit = defineEmits(['resolve', 'cancel'])

const selAcc = ref(props.initialAccId || props.accounts[0]?.id || '')
const folderTitle = computed(() => `选择${props.mode === 'src' ? '源' : '目标'}目录`)

const onResolve = (folder) => {
  const acc = props.accounts.find(a => a.id === selAcc.value)
  emit('resolve', {
    accId: selAcc.value,
    accName: acc?.name || '账号',
    parentId: folder.id,
    path: folder.path
  })
}
</script>

<style scoped>
.cross-pick-shell {
  display: flex;
  width: min(94vw, 900px);
  height: min(86vh, 570px);
  min-height: 0;
}

.cross-pick-accounts {
  width: 220px;
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 18px 12px 18px 18px;
  border-right: 1px solid var(--border-color);
}

.cpa-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0 6px 10px;
}

.cpa-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cpa-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.cpa-item:hover {
  background: rgba(127, 127, 127, 0.1);
}

.cpa-item.active {
  background: rgba(76, 116, 223, 0.12);
}

.cpa-name {
  font-weight: 600;
  color: var(--text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cpa-item.active .cpa-name {
  color: var(--primary-color);
}

.cpa-sub {
  font-size: 12px;
  color: var(--text-secondary);
}

.cpa-empty {
  padding: 22px 14px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.cross-pick-folder {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 嵌入 FolderSelectorModal 时未挂 modal-folder-selector，需覆盖全局 .breadcrumb { flex:1 } */
.cross-pick-folder :deep(.folder-selector-shell) {
  height: 100%;
}

.cross-pick-folder :deep(.folder-selector-content) {
  padding-top: 12px;
}

.cross-pick-folder :deep(.breadcrumb) {
  flex: none !important;
  margin-top: -6px !important;
  margin-bottom: 2px !important;
}

.cross-pick-folder :deep(.file-list) {
  flex: none !important;
  height: 345px;
  max-height: 345px;
  min-height: 345px;
  margin-top: 2px !important;
  overflow-y: auto;
}

.cpa-empty-folder {
  margin: auto;
}

@media (max-width: 640px) {
  .cross-pick-shell {
    flex-direction: column;
    height: min(86vh, 570px);
  }
  .cross-pick-accounts {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    max-height: 160px;
  }
}
</style>
