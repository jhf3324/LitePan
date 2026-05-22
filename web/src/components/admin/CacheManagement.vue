<template>
  <div class="cache-management">
    <!-- 缓存统计卡片 -->
    <div class="stats-cards">
      <div class="stats-card with-actions">
        <div class="stats-icon">
          <i class="fas fa-database"></i>
        </div>
        <div class="stats-content">
          <div class="stats-number">{{ cacheStats.totalKeys }}</div>
          <div class="stats-label">缓存条目</div>
        </div>
        <div class="stats-actions">
          <button 
            type="button" 
            @click="refreshStats" 
            class="mini-action-btn refresh" 
            :disabled="refreshing"
            :title="refreshing ? '刷新中...' : '刷新统计'"
          >
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
          </button>
          <button 
            type="button" 
            @click="clearCache" 
            class="mini-action-btn clear" 
            :disabled="clearing"
            title="清空缓存"
          >
            <i class="fas fa-trash-alt"></i>
          </button>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon">
          <i class="fas fa-hdd"></i>
        </div>
        <div class="stats-content">
          <div class="stats-number">{{ formatFileSize(cacheStats.totalSize) }}</div>
          <div class="stats-label">缓存大小</div>
        </div>
      </div>
      <div class="stats-card">
        <div class="stats-icon">
          <i class="fas fa-bullseye"></i>
        </div>
        <div class="stats-content">
          <div class="stats-number">{{ cacheStats.hitRate }}%</div>
          <div class="stats-label">命中率</div>
        </div>
      </div>
    </div>

    <!-- 缓存设置 -->
    <form @submit.prevent="saveSettings">
      <div class="settings-group">
        <div class="group-title-row">
          <div class="group-title"><i class="fas fa-cog"></i> 缓存设置</div>
          <button v-if="!hideInlineSave" type="submit" class="save-cache-btn">
            <i class="fas fa-save"></i>
            <span>保存设置</span>
          </button>
        </div>
        <div class="group-item">
          <div class="group-label">启用缓存
            <span class="help-icon" @mouseover="showCacheEnabledTooltip" @mouseleave="hideCacheEnabledTooltip">
              <i class="fas fa-question-circle"></i>
              <div class="tooltip" v-show="cacheEnabledTooltipVisible">
                <div class="tooltip-content">
                  <div class="tooltip-title">全局缓存开关</div>
                  <div class="tooltip-body">
                    <p>控制整个系统的缓存功能。关闭后，所有账号都将跳过缓存，直接从云盘获取最新数据。</p>
                    <div class="section-title">优先级说明</div>
                    <div class="priority-item">
                      <span class="priority-dot off"></span>
                      <span class="priority-text">关闭：所有账号都不缓存，每次都请求云盘API</span>
                    </div>
                    <div class="priority-item">
                      <span class="priority-dot on"></span>
                      <span class="priority-text">开启：各账号按自己的TTL设置进行缓存</span>
                    </div>
                  </div>
                </div>
              </div>
            </span>
          </div>
          <label class="inline-switch" for="cache_enabled">
            <input
              id="cache_enabled"
              v-model="settings.cache_enabled"
              type="checkbox"
            >
            <span class="inline-switch-slider"></span>
          </label>
        </div>
        <div class="group-item">
          <div class="group-label">默认缓存过期时间（分钟）
            <span class="help-icon" @mouseover="showCacheTtlTooltip" @mouseleave="hideCacheTtlTooltip">
              <i class="fas fa-question-circle"></i>
              <div class="tooltip" v-show="cacheTtlTooltipVisible">
                <div class="tooltip-content">
                  <div class="tooltip-title">默认缓存时间</div>
                  <div class="tooltip-body">
                    <p>当账号未设置缓存时间时，系统将使用此时间作为默认值。每个账号可以在账号管理中单独设置缓存时间。</p>
                    <div class="section-title">优先级说明</div>
                    <div class="priority-item">
                      <span class="priority-dot custom"></span>
                      <span class="priority-text">账号设置 > 全局默认值</span>
                    </div>
                    <div class="priority-item">
                      <span class="priority-dot zero"></span>
                      <span class="priority-text">账号TTL=0：完全禁用该账号缓存</span>
                    </div>
                    <div class="priority-item">
                      <span class="priority-dot custom"></span>
                      <span class="priority-text">账号TTL>0：使用账号设置的时间</span>
                    </div>
                    <div class="priority-item">
                      <span class="priority-dot default"></span>
                      <span class="priority-text">账号未设置：使用此全局默认值</span>
                    </div>
                  </div>
                </div>
              </div>
            </span>
          </div>
          <input type="number" id="cache_ttl" v-model.number="settings.cache_ttl" class="group-input" min="1" max="1440" required>
        </div>
        <div class="group-item">
          <div class="group-label">缓存条目最大数量
            <span class="help-icon" @mouseover="showCacheMaxItemsTooltip" @mouseleave="hideCacheMaxItemsTooltip">
              <i class="fas fa-question-circle"></i>
              <div class="tooltip" v-show="cacheMaxItemsTooltipVisible">
                <div class="tooltip-content">
                  <div class="tooltip-title">缓存条目上限</div>
                  <div class="tooltip-body">
                    <p>限制缓存中允许保留的最大条目数。每条目对应一个目录列表、文件信息或下载地址等。</p>
                    <p>达到上限时，按 LRU（最近最少使用）淘汰旧条目。</p>
                    <p>账号数较多或目录庞大时可适当调高（如 30000-100000）；建议保留默认 10000 即可满足绝大部分场景。</p>
                    <p class="warn-line">提示：调小该值后，多余的旧条目会立即被淘汰。</p>
                  </div>
                </div>
              </div>
            </span>
          </div>
          <input
            type="number"
            id="cache_max_items"
            v-model.number="settings.cache_max_items"
            class="group-input"
            min="1000"
            max="1000000"
            step="1000"
            required
          >
        </div>
        <div class="group-item">
          <div class="group-label">缓存内存上限 (MB)
            <span class="help-icon" @mouseover="showMemoryLimitTooltip" @mouseleave="hideMemoryLimitTooltip">
              <i class="fas fa-question-circle"></i>
              <div class="tooltip" v-show="memoryLimitTooltipVisible">
                <div class="tooltip-content">
                  <div class="tooltip-title">缓存内存上限</div>
                  <div class="tooltip-body">
                    <p>限制缓存占用的最大内存。达到 80% 时触发预防性 LRU 淘汰，达到 100% 时紧急清理至 70%。</p>
                    <p>默认 512MB，宿主机内存充裕（16G+）可调至 1024-2048MB 以缓存更多条目。</p>
                    <p>范围：64-16384MB。</p>
                  </div>
                </div>
              </div>
            </span>
          </div>
          <input
            type="number"
            id="cache_memory_limit_mb"
            v-model.number="settings.cache_memory_limit_mb"
            class="group-input"
            min="64"
            max="16384"
            step="64"
            required
          >
        </div>
        <template v-if="settings.cache_enabled">
          <div class="group-item">
            <div class="group-label">启用缓存持久化
              <span class="help-icon" @mouseover="showCachePersistenceTooltip" @mouseleave="hideCachePersistenceTooltip">
                <i class="fas fa-question-circle"></i>
                <div class="tooltip" v-show="cachePersistenceTooltipVisible">
                  <div class="tooltip-content">
                    <div class="tooltip-title">缓存持久化说明</div>
                    <div class="tooltip-body">
                      <p>将未过期缓存定期保存到磁盘，程序重启后可恢复。</p>
                      <p>仅在全局缓存开启时生效。</p>
                    </div>
                  </div>
                </div>
              </span>
            </div>
            <label class="inline-switch" for="cache_persistence_enabled">
              <input
                id="cache_persistence_enabled"
                v-model="settings.cache_persistence_enabled"
                type="checkbox"
              >
              <span class="inline-switch-slider"></span>
            </label>
          </div>
          <div class="group-item">
            <div class="group-label">缓存持久化快照间隔（分钟）
              <span class="help-icon" @mouseover="showCachePersistenceIntervalTooltip" @mouseleave="hideCachePersistenceIntervalTooltip">
                <i class="fas fa-question-circle"></i>
                <div class="tooltip" v-show="cachePersistenceIntervalTooltipVisible">
                  <div class="tooltip-content">
                    <div class="tooltip-title">快照保存间隔</div>
                    <div class="tooltip-body">
                      <p>系统会按此间隔将未过期缓存保存到磁盘。</p>
                      <p>间隔越短，重启后可恢复的缓存越新；间隔越长，磁盘写入越少。</p>
                    </div>
                  </div>
                </div>
              </span>
            </div>
            <input
              type="number"
              id="cache_persistence_interval_minutes"
              v-model.number="settings.cache_persistence_interval_minutes"
              class="group-input"
              min="1"
              max="1440"
              step="1"
              :disabled="!settings.cache_persistence_enabled"
              required
            >
          </div>
        </template>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { formatFileSize } from '../../utils/format.js'

defineProps({
  hideInlineSave: {
    type: Boolean,
    default: false
  }
})

// 响应式数据
const cacheEnabledTooltipVisible = ref(false)
const cacheTtlTooltipVisible = ref(false)
const cacheMaxItemsTooltipVisible = ref(false)
const cachePersistenceTooltipVisible = ref(false)
const cachePersistenceIntervalTooltipVisible = ref(false)
const memoryLimitTooltipVisible = ref(false)
const refreshing = ref(false)
const clearing = ref(false)

const settings = reactive({
  cache_enabled: true,
  cache_ttl: 30,
  cache_max_items: 10000,
  cache_persistence_enabled: true,
  cache_persistence_interval_minutes: 10,
  cache_memory_limit_mb: 512
})

const cacheStats = reactive({
  totalKeys: 0,
  totalSize: 0,
  hitRate: 0
})

// Tooltip 显示/隐藏方法
const showCacheEnabledTooltip = () => {
  cacheEnabledTooltipVisible.value = true
}

const hideCacheEnabledTooltip = () => {
  cacheEnabledTooltipVisible.value = false
}

const showCacheTtlTooltip = () => {
  cacheTtlTooltipVisible.value = true
}

const hideCacheTtlTooltip = () => {
  cacheTtlTooltipVisible.value = false
}

const showCacheMaxItemsTooltip = () => {
  cacheMaxItemsTooltipVisible.value = true
}

const hideCacheMaxItemsTooltip = () => {
  cacheMaxItemsTooltipVisible.value = false
}

const showCachePersistenceTooltip = () => {
  cachePersistenceTooltipVisible.value = true
}

const hideCachePersistenceTooltip = () => {
  cachePersistenceTooltipVisible.value = false
}

const showCachePersistenceIntervalTooltip = () => {
  cachePersistenceIntervalTooltipVisible.value = true
}

const hideCachePersistenceIntervalTooltip = () => {
  cachePersistenceIntervalTooltipVisible.value = false
}

const showMemoryLimitTooltip = () => {
  memoryLimitTooltipVisible.value = true
}

const hideMemoryLimitTooltip = () => {
  memoryLimitTooltipVisible.value = false
}

// 加载缓存设置
const loadCacheSettings = async () => {
  try {
    const response = await axios.get('/api/admin/cache-config')
    if (response.data.success) {
      const data = response.data.data || {}
      settings.cache_enabled = data.cache_enabled ?? true
      settings.cache_ttl = data.cache_ttl ?? 30
      settings.cache_max_items = data.cache_max_items ?? 10000
      settings.cache_persistence_enabled = data.cache_persistence_enabled ?? true
      settings.cache_persistence_interval_minutes = data.cache_persistence_interval_minutes ?? 10
      settings.cache_memory_limit_mb = data.cache_memory_limit_mb ?? 512
    } else {
      console.error('加载缓存设置失败:', response.data.message)
      window.appNotification.error('加载缓存设置失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('加载缓存设置失败:', error)
    window.appNotification.error('加载缓存设置失败: ' + error.message)
  }
}

// 保存设置
const saveSettings = async () => {
  try {
    const response = await axios.post('/api/admin/update-cache-config', {
      cache_enabled: settings.cache_enabled,
      cache_ttl: settings.cache_ttl,
      cache_max_items: settings.cache_max_items,
      cache_persistence_enabled: settings.cache_persistence_enabled,
      cache_persistence_interval_minutes: settings.cache_persistence_interval_minutes,
      cache_memory_limit_mb: settings.cache_memory_limit_mb
    })
    
    if (response.data.success) {
      window.appNotification.success('缓存设置保存成功！')
    } else {
      window.appNotification.error('保存失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('保存缓存设置失败:', error)
    window.appNotification.error('保存失败: ' + error.message)
  }
}




// 加载缓存统计
const loadCacheStats = async () => {
  try {
    const response = await axios.get('/api/admin/cache/stats')
    if (response.data.success) {
      const data = response.data.data
      cacheStats.totalKeys = data.total_keys || 0
      cacheStats.totalSize = data.total_size_bytes || 0
      cacheStats.hitRate = data.hit_rate || 0
    }
  } catch (error) {
    console.error('加载缓存统计失败:', error)
  }
}

// 刷新统计
const refreshStats = async () => {
  refreshing.value = true
  try {
    await loadCacheStats()
    window.appNotification.success('缓存统计已刷新')
  } catch (error) {
    window.appNotification.error('刷新失败: ' + error.message)
  } finally {
    refreshing.value = false
  }
}

// 清空缓存
const clearCache = async () => {
  clearing.value = true
  try {
    const response = await axios.post('/api/admin/clear-cache')
    if (response.data.success) {
      window.appNotification.success('缓存已清空')
      await loadCacheStats() // 刷新统计
    } else {
      window.appNotification.error('清空失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('清空缓存失败:', error)
    window.appNotification.error('清空失败: ' + error.message)
  } finally {
    clearing.value = false
  }
}

// 组件挂载时初始化
onMounted(() => {
  loadCacheSettings()
  loadCacheStats()
})

// 暴露保存方法给父组件
defineExpose({
  saveSettings
})
</script>

<style scoped>
/* 使用与 SystemSettings.vue 完全一致的样式 */

/* 设置分组样式 */
.settings-group {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #4C74DF;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.group-title {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.group-title i {
  margin-right: 12px;
  color: #4C74DF;
}

.group-item {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 20px;
  align-items: center;
  padding: 12px 0;
  position: relative;
}

.group-item:not(:last-child)::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 33.33%;
  height: 1px;
  background: linear-gradient(to right, 
    #e2e8f0 0%, 
    rgba(226, 232, 240, 0.8) 25%, 
    rgba(226, 232, 240, 0.6) 50%, 
    rgba(226, 232, 240, 0.4) 75%, 
    transparent 100%
  );
}

.group-label {
  font-weight: 500;
  color: #4a5568;
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-input {
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.group-input:focus {
  outline: none;
  border-color: #4C74DF;
  box-shadow: 0 0 0 2px rgba(76, 116, 223, 0.1);
}

/* 帮助提示样式 */
.help-icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: help;
}

.help-icon i {
  color: #94a3b8;
  font-size: 14px;
  transition: color 0.2s ease;
}

.help-icon:hover i {
  color: #4C74DF;
}

.tooltip {
  position: absolute;
  top: 50%;
  left: 25px;
  transform: translateY(-50%);
  z-index: 1000;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
  padding: 0;
  min-width: 380px;
  max-width: 480px;
  color: #2d3748;
  overflow: hidden;
}

/* 提示框箭头 */
.tooltip::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -7px;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 7px solid transparent;
  border-bottom: 7px solid transparent;
  border-right: 7px solid #e1e8ed;
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 50%;
  left: -6px;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
  border-right: 6px solid #ffffff;
}

.tooltip-content {
  padding: 0;
}

.tooltip-title {
  background: #f8fafc;
  color: #4C74DF;
  padding: 16px 20px;
  font-weight: 600;
  font-size: 15px;
  border-bottom: 1px solid #e2e8f0;
}

.tooltip-body {
  padding: 20px;
}

.tooltip-body p {
  margin: 0 0 16px 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
}

.section-title {
  color: #4C74DF;
  font-weight: 600;
  font-size: 14px;
  margin: 20px 0 12px 0;
}

.priority-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  padding: 4px 0;
}

.priority-item:last-child {
  margin-bottom: 0;
}

.priority-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.priority-dot.on {
  background: #10b981;
}

.priority-dot.off {
  background: #ef4444;
}

.priority-dot.custom {
  background: #f59e0b;
}

.priority-dot.zero {
  background: #6b7280;
}

.priority-dot.default {
  background: #8b5cf6;
}

.priority-text {
  color: #475569;
  font-size: 13px;
  line-height: 1.5;
  flex: 1;
}

.inline-switch {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.inline-switch input {
  display: none;
}

.inline-switch-slider {
  position: relative;
  width: 48px;
  height: 26px;
  border-radius: 999px;
  background: #cbd5e1;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.inline-switch-slider::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s ease;
}

.inline-switch input:checked + .inline-switch-slider {
  background: linear-gradient(135deg, #4C74DF, #02A6F0);
}

.inline-switch input:checked + .inline-switch-slider::after {
  transform: translateX(22px);
}

/* 统计卡片样式 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stats-card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.2s ease;
  position: relative;
}



.stats-card.with-actions {
  padding-right: 80px;
}

.group-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.save-cache-btn {
  height: 34px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  border: 1px solid #d7e3f4;
  border-radius: 8px;
  background: #f8fbff;
  color: #3f5f9a;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.save-cache-btn:hover {
  background: #eef4ff;
  border-color: #bfd3f2;
  color: #2f5fd0;
}

@media (max-width: 768px) {
  .group-title-row {
    flex-direction: column;
    align-items: stretch;
  }

  .save-cache-btn {
    justify-content: center;
  }
}

.stats-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #4C74DF 0%, #02A6F0 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.stats-content {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

/* 统计卡片操作按钮 */
.stats-actions {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  gap: 8px;
}

.mini-action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.mini-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mini-action-btn.refresh {
  background: #f8fafc;
  color: #4C74DF;
  border: 1px solid #e2e8f0;
}

.mini-action-btn.refresh:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #4C74DF;
  transform: scale(1.05);
}

.mini-action-btn.clear {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.mini-action-btn.clear:hover:not(:disabled) {
  background: #fee2e2;
  border-color: #dc2626;
  transform: scale(1.05);
}



/* 响应式设计 */
@media (max-width: 768px) {
  .group-item {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .tooltip {
    max-width: 340px;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    min-width: 320px;
  }
  
  .tooltip-title {
    padding: 14px 16px;
    font-size: 14px;
  }
  
  .tooltip-body {
    padding: 16px;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .stats-actions {
    position: static;
    transform: none;
    margin-top: 12px;
    justify-content: center;
  }
  
  .priority-item {
    gap: 8px;
    margin-bottom: 8px;
  }
  
  .priority-dot {
    width: 6px;
    height: 6px;
  }
  
  .priority-text {
    font-size: 12px;
  }
  
  .tooltip::before {
    top: -7px;
    left: 20px;
    border-left: 7px solid transparent;
    border-right: 7px solid transparent;
    border-bottom: 7px solid #e1e8ed;
    border-top: none;
    transform: none;
  }
  
  .tooltip::after {
    top: -6px;
    left: 21px;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-bottom: 6px solid #ffffff;
    border-top: none;
    transform: none;
  }
}
</style>
