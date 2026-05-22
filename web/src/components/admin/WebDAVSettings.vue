<template>
  <div class="webdav-settings">
    <form @submit.prevent="saveSettings">
      <div class="settings-group">
        <div class="group-title"><i class="fas fa-power-off"></i> 服务开关</div>
        <div class="group-item">
          <div class="group-label">
            启用 WebDAV 服务
            <span class="help-icon" @mouseover="showWebdavEnabledTooltip" @mouseleave="hideWebdavEnabledTooltip">
              <i class="fas fa-question-circle"></i>
              <div class="tooltip" v-show="webdavEnabledTooltipVisible">
                <div class="tooltip-content">
                  <div class="tooltip-title">WebDAV 服务开关说明</div>
                  <div class="tooltip-body">
                    <p>开启后，外部客户端可以通过 WebDAV 地址访问 LitePan。</p>
                    <p>关闭后，WebDAV 入口会直接拒绝访问，下面的传输设置也不会生效。</p>
                    <p>访问地址为当前浏览器打开后台所用的「协议 + 主机 + 端口」后接 <code>/dav</code>，见下方「WebDAV 地址」。</p>
                  </div>
                </div>
              </div>
            </span>
          </div>
          <label class="inline-switch" for="webdav_enabled">
            <input
              id="webdav_enabled"
              v-model="settings.webdav_enabled"
              type="checkbox"
            >
            <span class="inline-switch-slider"></span>
          </label>
        </div>

        <div class="group-item webdav-url-item">
          <div class="group-label">
            WebDAV 地址
            <span class="help-icon" @mouseover="showWebdavUrlTooltip" @mouseleave="hideWebdavUrlTooltip">
              <i class="fas fa-question-circle"></i>
              <div class="tooltip" v-show="webdavUrlTooltipVisible">
                <div class="tooltip-content">
                  <div class="tooltip-title">WebDAV 地址说明</div>
                  <div class="tooltip-body">
                    <p>地址由当前页面自动填写：浏览器打开本后台所用的「协议 + 主机 + 端口」后接 <code>/dav</code>。</p>
                    <p>与 Web 管理后台<strong>共用同一端口</strong>；用户名、密码与「账号与安全」中的<strong>管理员账号</strong>相同。</p>
                  </div>
                </div>
              </div>
            </span>
          </div>
          <div class="webdav-url-field">
            <input
              type="text"
              class="webdav-url-input"
              readonly
              :value="webdavServerUrl"
            >
            <button
              type="button"
              class="btn-copy-webdav"
              title="复制地址"
              @click="copyWebdavUrl"
            >
              <i class="fas fa-copy"></i>
            </button>
          </div>
        </div>
      </div>

      <div class="settings-group" v-show="settings.webdav_enabled">
        <div class="group-title"><i class="fas fa-database"></i> 缓存优化</div>

        <div class="group-item">
          <div class="group-label">
            WebDAV 缓存优化
            <span class="help-icon" @mouseover="showWebdavCacheTooltip" @mouseleave="hideWebdavCacheTooltip">
              <i class="fas fa-question-circle"></i>
              <div class="tooltip" v-show="webdavCacheTooltipVisible">
                <div class="tooltip-content">
                  <div class="tooltip-title">WebDAV 缓存优化说明</div>
                  <div class="tooltip-body">
                    <p>开启后，系统会启用 WebDAV 的缓存优化（包含目录属性结果与路径解析结果缓存），减少重复查询与逐级查找。</p>
                    <p>如果你经常在官方客户端或其他客户端改动同目录内容、覆盖同名文件或移动文件，建议关闭或改动后使用“强制刷新”。</p>
                  </div>
                </div>
              </div>
            </span>
          </div>
          <label class="inline-switch" for="webdav_cache_enabled">
            <input
              id="webdav_cache_enabled"
              v-model="settings.webdav_cache_enabled"
              type="checkbox"
            >
            <span class="inline-switch-slider"></span>
          </label>
        </div>
      </div>
      
      </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  saving: Boolean
})

const emit = defineEmits(['save'])

const settings = reactive({
  webdav_enabled: true,
  webdav_cache_enabled: true
})

const webdavEnabledTooltipVisible = ref(false)
const webdavUrlTooltipVisible = ref(false)
const webdavCacheTooltipVisible = ref(false)

const showWebdavEnabledTooltip = () => {
  webdavEnabledTooltipVisible.value = true
}

const hideWebdavEnabledTooltip = () => {
  webdavEnabledTooltipVisible.value = false
}

const showWebdavUrlTooltip = () => {
  webdavUrlTooltipVisible.value = true
}

const hideWebdavUrlTooltip = () => {
  webdavUrlTooltipVisible.value = false
}

const showWebdavCacheTooltip = () => {
  webdavCacheTooltipVisible.value = true
}

const hideWebdavCacheTooltip = () => {
  webdavCacheTooltipVisible.value = false
}

/** 与当前访问后台一致：origin + /dav（与 WebDAV 服务同端口） */
const webdavServerUrl = computed(() => {
  if (typeof window === 'undefined') {
    return ''
  }
  const base = window.location.origin.replace(/\/$/, '')
  return `${base}/dav`
})

const copyWebdavUrl = async () => {
  const text = webdavServerUrl.value
  if (!text) {
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    if (window.appNotification) {
      window.appNotification.success('已复制 WebDAV 地址')
    }
  } catch (e) {
    try {
      const el = document.createElement('textarea')
      el.value = text
      el.style.position = 'fixed'
      el.style.left = '-9999px'
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      if (window.appNotification) {
        window.appNotification.success('已复制 WebDAV 地址')
      }
    } catch (err) {
      console.error(err)
      if (window.appNotification) {
        window.appNotification.error('复制失败，请手动选择地址复制')
      }
    }
  }
}

const loadSettings = async () => {
  try {
    const response = await axios.get('/api/admin/system-config')
    if (response.data.success) {
      const data = response.data.data
      settings.webdav_enabled = data.webdav_enabled !== false
      settings.webdav_cache_enabled = data.webdav_cache_enabled !== false
    }
  } catch (error) {
    console.error('加载WebDAV设置失败:', error)
  }
}

const saveSettings = async () => {
  try {
    await axios.post('/api/admin/webdav-config', {
      webdav_enabled: settings.webdav_enabled,
      webdav_cache_enabled: settings.webdav_cache_enabled
    })
    window.appNotification.success('WebDAV设置保存成功')
  } catch (error) {
    console.error('保存WebDAV设置失败:', error)
    window.appNotification.error('保存失败: ' + error.message)
  }
}

onMounted(() => {
  loadSettings()
})

defineExpose({ saveSettings })
</script>

<style scoped>
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
  color: #4a5568;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

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

.tooltip-body p:last-child {
  margin-bottom: 0;
}

.tooltip-body code {
  padding: 1px 6px;
  font-size: 12px;
  background: #f1f5f9;
  border-radius: 4px;
  color: #475569;
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

.webdav-url-item {
  align-items: center;
}

.webdav-url-field {
  display: flex;
  align-items: stretch;
  gap: 10px;
  min-width: 0;
  max-width: 100%;
}

.webdav-url-input {
  flex: 1;
  min-width: 0;
  padding: 10px 14px;
  font-size: 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #1e293b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.btn-copy-webdav {
  flex-shrink: 0;
  padding: 0 16px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #4C74DF;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.btn-copy-webdav:hover {
  background: #eff6ff;
  border-color: #4C74DF;
}
</style>
