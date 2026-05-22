<template>
  <div class="cache-center">
    <div class="cache-center-header">
      <div class="tab-nav cache-center-tabs" role="tablist" aria-label="缓存管理视图切换">
        <button
          type="button"
          class="tab-btn cache-tab-btn"
          :class="{ active: activeTab === 'retention' }"
          @click="activeTab = 'retention'"
        >
          <i class="fas fa-fire"></i>
          <span>缓存保持任务</span>
        </button>
        <button
          type="button"
          class="tab-btn cache-tab-btn"
          :class="{ active: activeTab === 'settings' }"
          @click="activeTab = 'settings'"
        >
          <i class="fas fa-sliders-h"></i>
          <span>全局缓存设置</span>
        </button>
      </div>

      <div class="cache-center-action">
        <button
          v-if="activeTab === 'settings'"
          type="button"
          class="btn btn-primary"
          @click="handleSaveSettings"
        >
          <i class="fas fa-save"></i>
          <span>保存设置</span>
        </button>
        <button
          v-else
          type="button"
          class="btn btn-primary"
          @click="handleAddRetentionDirectory"
        >
          <i class="fas fa-plus"></i>
          <span>添加任务</span>
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'settings'" class="cache-center-panel">
      <CacheManagement ref="cacheManagementRef" hide-inline-save />
    </div>

    <div v-else class="cache-center-panel">
      <CacheRetention ref="cacheRetentionRef" hide-header-add />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CacheManagement from './CacheManagement.vue'
import CacheRetention from './CacheRetention.vue'

const activeTab = ref('retention')
const cacheManagementRef = ref(null)
const cacheRetentionRef = ref(null)

const handleSaveSettings = async () => {
  if (cacheManagementRef.value?.saveSettings) {
    await cacheManagementRef.value.saveSettings()
  }
}

const handleAddRetentionDirectory = async () => {
  if (cacheRetentionRef.value?.showAddDialog) {
    await cacheRetentionRef.value.showAddDialog()
  }
}
</script>

<style scoped>
.cache-center {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.cache-center-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.cache-center-header .tab-nav {
  flex: 1;
}

.cache-center-header .btn {
  margin-left: 20px;
}

.cache-center-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  background: #f8fafc;
  padding: 4px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.cache-center-tabs .tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  position: relative;
}

.cache-center-tabs .tab-btn:hover {
  background: linear-gradient(135deg, #3b5bdb, #1e88e5);
  color: #fff;
}

.cache-center-tabs .tab-btn.active {
  background: linear-gradient(135deg, #4c74df, #02a6f0);
  color: #fff;
  box-shadow: 0 2px 4px rgba(76, 116, 223, 0.3);
}

.cache-tab-btn {
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.cache-center-action {
  width: 118px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-shrink: 0;
}

.cache-center-panel {
  min-width: 0;
}

@media (max-width: 900px) {
  .cache-center-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .cache-center-action {
    justify-content: center;
    width: auto;
  }

  .cache-center-header .btn {
    margin-left: 0;
    align-self: center;
  }
}

@media (max-width: 640px) {
  .cache-center-tabs {
    flex-direction: column;
    gap: 2px;
  }

  .cache-tab-btn {
    justify-content: center;
    padding: 10px 16px;
  }
}
</style>
