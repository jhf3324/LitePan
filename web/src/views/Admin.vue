<template>
  <div class="admin-container" :class="{ 'drawer-open': sidebarOpen }">
    <!-- 小屏抽屉遮罩 -->
    <div class="sidebar-backdrop" :class="{ visible: sidebarOpen }" @click="closeSidebar"></div>
    <!-- 左侧边栏 -->
    <div class="sidebar-container" :class="{ open: sidebarOpen }">
      <div class="sidebar">
        <div class="sidebar-header">
          <img src="/static/img/logo.png" alt="LitePan" class="sidebar-logo">
        </div>
        <nav class="sidebar-nav">
          <a class="nav-item" :class="{ active: currentPage === 'dashboard', disabled: isPageLocked('dashboard') }" @click="setCurrentPage('dashboard')">
            <i class="fas fa-tachometer-alt nav-icon"></i> 仪表盘
          </a>
          <a class="nav-item" :class="{ active: currentPage === 'accounts', disabled: isPageLocked('accounts') }" @click="setCurrentPage('accounts')">
            <i class="fas fa-hdd nav-icon"></i> 存储管理
          </a>
          <a class="nav-item" :class="{ active: currentPage === 'settings' }" @click="setCurrentPage('settings')">
            <i class="fas fa-cogs nav-icon"></i> 系统设置
          </a>
          <a class="nav-item" :class="{ active: currentPage === 'cache', disabled: isPageLocked('cache') }" @click="setCurrentPage('cache')">
            <i class="fas fa-database nav-icon"></i> 缓存管理
          </a>
          <a class="nav-item" :class="{ active: currentPage === 'strm', disabled: isPageLocked('strm') }" @click="setCurrentPage('strm')">
            <i class="fas fa-film nav-icon"></i> 媒体管理
          </a>
          <a class="nav-item" :class="{ active: currentPage === 'cross-transfer', disabled: isPageLocked('cross-transfer') }" @click="setCurrentPage('cross-transfer')">
            <i class="fas fa-bolt nav-icon"></i> 跨盘秒传
          </a>
          <a class="nav-item" :class="{ active: currentPage === 'logs', disabled: isPageLocked('logs') }" @click="setCurrentPage('logs')">
            <i class="fas fa-file-alt nav-icon"></i> 系统日志
          </a>
          <a class="nav-item" :class="{ active: currentPage === 'plugins', disabled: isPageLocked('plugins') }" @click="setCurrentPage('plugins')">
            <i class="fas fa-puzzle-piece nav-icon"></i> 插件中心
          </a>
          <a v-if="showSidebarHomeReturn" class="nav-item" href="/">
            <i class="fas fa-home nav-icon"></i> 返回首页
          </a>
        </nav>
        <div class="sidebar-footer">
          <div class="sidebar-version">{{ appVersion }}</div>
        </div>
      </div>
    </div>
    
    <!-- 主内容区域 -->
    <div class="main-content">
      <div class="navbar">
        <div class="navbar-left">
          <button
            class="hamburger-btn"
            :class="{ active: sidebarOpen }"
            type="button"
            :aria-label="sidebarOpen ? '关闭菜单' : '打开菜单'"
            :aria-expanded="sidebarOpen"
            @click="toggleSidebar"
          >
            <i :class="['fas', sidebarOpen ? 'fa-times' : 'fa-bars']"></i>
          </button>
          <div class="breadcrumb">{{ currentPageTitle }}</div>
        </div>
        <div class="navbar-right">
          <button
            class="nav-action theme-toggle-action"
            type="button"
            :title="themeToggleTitle"
            :aria-label="themeToggleTitle"
            :disabled="themeSaving"
            @click="toggleTheme"
          >
            <svg
              v-if="currentTheme === 'light'"
              class="theme-sun-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="4"></circle>
              <path d="M12 2v2"></path>
              <path d="M12 20v2"></path>
              <path d="m4.93 4.93 1.41 1.41"></path>
              <path d="m17.66 17.66 1.41 1.41"></path>
              <path d="M2 12h2"></path>
              <path d="M20 12h2"></path>
              <path d="m6.34 17.66-1.41 1.41"></path>
              <path d="m19.07 4.93-1.41 1.41"></path>
            </svg>
            <i v-else :class="themeIconClass"></i>
          </button>
          <div class="notification-bell-wrapper">
            <button class="nav-action notification-bell" title="通知" @click="toggleNotificationPanel">
              <i class="fas fa-bell"></i>
              <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </button>
            <div v-if="showNotificationPanel" class="notification-panel">
              <div class="notification-panel-header">
                <span>通知</span>
                <button v-if="unreadCount > 0" class="notification-mark-all" @click="markAllRead">全部已读</button>
              </div>
              <div class="notification-list">
                <div v-if="notifications.length === 0" class="notification-empty">暂无通知</div>
                <div
                  v-for="n in notifications"
                  :key="n.id"
                  class="notification-item"
                  :class="{ unread: !n.read, ['level-' + n.level]: true }"
                  @click="handleNotificationClick(n)"
                >
                  <div class="notification-item-icon">
                    <i v-if="n.level === 'error'" class="fas fa-circle-xmark"></i>
                    <i v-else-if="n.level === 'warning'" class="fas fa-triangle-exclamation"></i>
                    <i v-else class="fas fa-circle-info"></i>
                  </div>
                  <div class="notification-item-body">
                    <div class="notification-item-title">{{ n.title }}</div>
                    <div class="notification-item-message">{{ n.message }}</div>
                    <div class="notification-item-time">{{ formatNotificationTime(n.created_at) }}</div>
                  </div>
                  <button v-if="n.action_label" class="notification-item-action" @click.stop="handleNotificationAction(n)">
                    {{ n.action_label }}
                  </button>
                  <button class="notification-item-close" @click.stop="deleteNotification(n.id)" title="删除">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <a v-if="showTopHomeReturn" href="/" class="nav-action" title="返回首页"><i class="fas fa-home"></i></a>
          <button @click="handleLogout" class="nav-action logout-action" title="退出登录"><i class="fas fa-sign-out-alt"></i></button>
        </div>
      </div>
      <div v-if="mustChangePassword" class="security-warning-banner">
        <i class="fas fa-shield-alt"></i>
        <span>{{ passwordChangeMessage }}</span>
      </div>
      <div class="main-body">
        <!-- 仪表盘 -->
        <div v-if="currentPage === 'dashboard'" class="page-content">
          <div class="dash-shell">
            <!-- A. Hero 顶条 -->
            <div class="dash-hero" :class="{ 'has-issues': expiredCount > 0, 'has-warning': expiredCount === 0 && recentErrorCount > 0 }">
              <div class="dash-hero-left">
                <div class="dash-hero-status" :class="heroStatusClass">
                  <i :class="heroStatusIcon"></i>
                </div>
                <div class="dash-hero-text">
                  <h2 class="dash-hero-title">控制台</h2>
                  <p class="dash-hero-sub">
                    <template v-if="expiredCount > 0">{{ expiredCount }} 个账号需要重新授权</template>
                    <template v-else-if="recentErrorCount > 0">最近 24 小时发现 {{ recentErrorCount }} 条错误日志</template>
                    <template v-else-if="!accounts.length">尚未接入任何账号 · 请先到「存储管理」添加</template>
                    <template v-else>系统运行正常 · 所有账号在线</template>
                  </p>
                </div>
              </div>
              <div class="dash-hero-stats">
                <div class="dash-hero-stat">
                  <span class="dash-hero-stat-val">{{ accounts.length }}</span>
                  <span class="dash-hero-stat-key">接入</span>
                </div>
                <div class="dash-hero-stat">
                  <span class="dash-hero-stat-val" :class="heroOnlineClass">{{ connectedAccounts }}</span>
                  <span class="dash-hero-stat-key">在线</span>
                </div>
                <div class="dash-hero-stat">
                  <span class="dash-hero-stat-val">{{ runningTaskCount }}</span>
                  <span class="dash-hero-stat-key">运行任务</span>
                </div>
                <div class="dash-hero-stat">
                  <span class="dash-hero-stat-val" :class="recentErrorCount > 0 ? 'warn' : 'muted'">{{ recentErrorCount }}</span>
                  <span class="dash-hero-stat-key">最近错误</span>
                </div>
              </div>
            </div>

            <!-- 2x2 网格 -->
            <div class="dash-grid">
              <!-- 左列 -->
              <div class="dash-col">
                <!-- B. 存储账号 -->
                <div class="dash-panel">
                  <div class="dash-panel-head">
                    <div class="dash-panel-title">
                      <span class="dash-panel-title-dot" style="background: #4C74DF"></span>
                      存储账号
                      <span class="dash-panel-title-sub">{{ accountSummaryText }}</span>
                    </div>
                    <button class="dash-panel-action" @click="setCurrentPage('accounts')">管理 <i class="fas fa-chevron-right"></i></button>
                  </div>
                  <div class="dash-panel-body">
                    <div v-if="!accounts.length" class="dash-acc-empty">
                      <div class="dash-acc-empty-icon"><i class="fas fa-cloud-arrow-up"></i></div>
                      <p>尚未接入任何存储账号</p>
                      <button @click="setCurrentPage('accounts')">立即添加</button>
                    </div>
                    <div v-else class="dash-acc-list">
                      <div
                        v-for="a in accounts"
                        :key="a.id"
                        class="dash-acc-row"
                        :class="{ 'is-down': isAccountUnhealthy(a) }"
                        :style="getDriverCardStyle(a.driver_type)"
                        @click="setCurrentPage('accounts')"
                      >
                        <DriverIcon
                          class="dash-acc-badge-wrap"
                          :logo="getDriverLogo(a.driver_type)"
                          :color="getDriverColor(a.driver_type)"
                          :name="getDriverCardName(a.driver_type)"
                          size="badge"
                        />
                        <div class="dash-acc-info">
                          <div class="dash-acc-name">
                            {{ a.name }}
                            <span v-if="a.is_default" class="dash-acc-default-pill">默认</span>
                          </div>
                          <div class="dash-acc-driver">{{ getDriverLabel(a.driver_type) }}</div>
                        </div>
                        <div v-if="getDownloadModeLabel(a)" class="dash-acc-mode">
                          <i :class="getDownloadModeIcon(a)"></i>
                          <span>{{ getDownloadModeLabel(a) }}</span>
                        </div>
                        <div class="dash-acc-status" :class="{ warn: isAccountUnhealthy(a) }">
                          <span class="dash-acc-dot" :class="accountHealthClass(a)"></span>
                          <span>{{ accountHealthLabel(a) }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-if="accounts.length" class="dash-panel-foot">
                    <button class="dash-btn-ghost" @click="setCurrentPage('accounts')">
                      <i class="fas fa-plus"></i> 添加账号
                    </button>
                  </div>
                </div>

                <!-- D. 全局缓存 -->
                <div class="dash-panel">
                  <div class="dash-panel-head">
                    <div class="dash-panel-title">
                      <span class="dash-panel-title-dot" style="background: #f59e0b"></span>
                      全局缓存
                      <span class="dash-panel-title-sub">实时状态</span>
                    </div>
                    <button class="dash-panel-action" @click="setCurrentPage('cache')">缓存中心 <i class="fas fa-chevron-right"></i></button>
                  </div>
                  <div class="dash-panel-body">
                    <div class="dash-cache-grid">
                      <div class="dash-cache-cell">
                        <div class="dash-cache-cell-num">{{ totalCacheKeys }}</div>
                        <div class="dash-cache-cell-key">缓存条目</div>
                      </div>
                      <div class="dash-cache-cell">
                        <div class="dash-cache-cell-num">
                          {{ splitCacheSize.value }} <span class="dash-cache-cell-unit">{{ splitCacheSize.unit }}</span>
                        </div>
                        <div class="dash-cache-cell-key">占用空间</div>
                      </div>
                    </div>
                    <div class="dash-cache-hit">
                      <div class="dash-cache-hit-head">
                        <span class="dash-cache-hit-label">命中率</span>
                        <span class="dash-cache-hit-val">{{ cacheHitRate }}%</span>
                      </div>
                      <div class="dash-cache-hit-bar">
                        <div class="dash-cache-hit-bar-fill" :style="{ width: cacheHitRate + '%' }"></div>
                      </div>
                    </div>
                  </div>
                  <div class="dash-panel-foot">
                    <button class="dash-btn-danger" :disabled="dashboardCacheClearing || !totalCacheKeys" @click="clearDashboardCache">
                      <i class="fas fa-trash-alt"></i> 清空缓存
                    </button>
                  </div>
                </div>
              </div>

              <!-- 右列 -->
              <div class="dash-col">
                <!-- C. 后台任务 -->
                <div class="dash-panel">
                  <div class="dash-panel-head">
                    <div class="dash-panel-title">
                      <span class="dash-panel-title-dot" style="background: #6366f1"></span>
                      后台任务
                      <span class="dash-panel-title-sub">{{ runningTaskCount }}/{{ totalTaskCount }} 运行中</span>
                    </div>
                  </div>
                  <div class="dash-panel-body">
                    <div class="dash-job-list">
                      <div class="dash-job-row" @click="setCurrentPage('strm')">
                        <div class="dash-job-icon strm"><i class="fas fa-film"></i></div>
                        <div class="dash-job-info">
                          <div class="dash-job-name">
                            STRM 任务
                            <span v-if="pausedStrmTasks > 0" class="dash-job-tag warn">{{ pausedStrmTasks }} 暂停</span>
                          </div>
                          <div class="dash-job-meta">
                            <div class="dash-job-bar"><div class="dash-job-bar-fill strm" :style="{ width: jobBarWidth(runningStrmTasks, totalStrmTasks) }"></div></div>
                            <span>{{ runningStrmTasks }} 运行中</span>
                          </div>
                        </div>
                        <div class="dash-job-stat">
                          <div class="dash-job-stat-num">{{ runningStrmTasks }}<span class="frac">/{{ totalStrmTasks }}</span></div>
                        </div>
                      </div>

                      <div class="dash-job-row" @click="setCurrentPage('cache')">
                        <div class="dash-job-icon retention"><i class="fas fa-clock-rotate-left"></i></div>
                        <div class="dash-job-info">
                          <div class="dash-job-name">
                            缓存保持任务
                            <span v-if="pausedCacheRetentionTasks > 0" class="dash-job-tag warn">{{ pausedCacheRetentionTasks }} 暂停</span>
                          </div>
                          <div class="dash-job-meta">
                            <div class="dash-job-bar"><div class="dash-job-bar-fill retention" :style="{ width: jobBarWidth(runningCacheRetentionTasks, totalCacheRetentionTasks) }"></div></div>
                            <span>{{ runningCacheRetentionTasks }} 运行中</span>
                          </div>
                        </div>
                        <div class="dash-job-stat">
                          <div class="dash-job-stat-num">{{ runningCacheRetentionTasks }}<span class="frac">/{{ totalCacheRetentionTasks }}</span></div>
                        </div>
                      </div>

                      <div class="dash-job-row" @click="setCurrentPage('strm')">
                        <div class="dash-job-icon emby"><i class="fas fa-server"></i></div>
                        <div class="dash-job-info">
                          <div class="dash-job-name">
                            Emby 反代
                            <span v-if="embyProxyIssueCount > 0" class="dash-job-tag err">{{ embyProxyIssueCount }} 异常</span>
                          </div>
                          <div class="dash-job-meta">
                            <div class="dash-job-bar"><div class="dash-job-bar-fill emby" :style="{ width: jobBarWidth(runningEmbyProxies, totalEmbyProxies) }"></div></div>
                            <span>{{ runningEmbyProxies }} 运行中</span>
                          </div>
                        </div>
                        <div class="dash-job-stat">
                          <div class="dash-job-stat-num">{{ runningEmbyProxies }}<span class="frac">/{{ totalEmbyProxies }}</span></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- E. 日志中心 -->
                <div class="dash-panel">
                  <div class="dash-panel-head">
                    <div class="dash-panel-title">
                      <span class="dash-panel-title-dot" style="background: #94a3b8"></span>
                      日志中心
                      <span class="dash-panel-title-sub">最近 24 小时</span>
                    </div>
                    <button class="dash-panel-action" @click="setCurrentPage('logs')">查看全部 <i class="fas fa-chevron-right"></i></button>
                  </div>
                  <div class="dash-panel-body">
                    <div class="dash-log-grid">
                      <div class="dash-log-cell">
                        <div class="dash-log-cell-num">{{ totalLogCount.toLocaleString() }}</div>
                        <div class="dash-log-cell-key">日志总数</div>
                      </div>
                      <div class="dash-log-cell">
                        <div class="dash-log-cell-num">{{ logRetentionDays }} <span class="dash-log-cell-unit">天</span></div>
                        <div class="dash-log-cell-key">保留期</div>
                      </div>
                    </div>
                    <div class="dash-log-error" :class="{ 'has-error': recentErrorCount > 0 }">
                      <div class="dash-log-error-icon" @click="recentErrorCount > 0 && setCurrentPage('logs')">
                        <i :class="recentErrorCount > 0 ? 'fas fa-circle-exclamation' : 'fas fa-check'"></i>
                      </div>
                      <div class="dash-log-error-text" @click="recentErrorCount > 0 && setCurrentPage('logs')">
                        <div class="dash-log-error-title">{{ recentErrorCount > 0 ? `最近发现 ${recentErrorCount} 条错误` : '日志状态正常' }}</div>
                        <div class="dash-log-error-sub">{{ recentErrorCount > 0 ? '点击查看详情，或在确认无需关注后标记已读' : '最近 24 小时没有错误日志' }}</div>
                      </div>
                      <button
                        v-if="recentErrorCount > 0"
                        class="dash-log-error-ack"
                        :disabled="dashboardErrorsAcking"
                        @click.stop="ackDashboardErrors"
                        title="标记为已读，下次出现新错误时仪表盘会重新提示"
                      >
                        <i class="fas fa-check"></i>
                        <span>{{ dashboardErrorsAcking ? '处理中…' : '已读' }}</span>
                      </button>
                    </div>
                    <div class="dash-log-tip">
                      <i class="fas fa-info-circle"></i>
                      日志保留期可在「<a href="#" @click.prevent="setCurrentPage('settings')">系统设置</a>」中修改
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 存储管理 -->
        <div v-if="currentPage === 'accounts'" class="page-content">
          <AccountManagement />
        </div>
        
        <!-- 系统设置 -->
        <div v-if="currentPage === 'settings'" class="page-content">
          <SystemSettings
            :force-password-change="mustChangePassword"
            :password-change-reason="passwordChangeReason"
            @password-updated="handlePasswordUpdated"
            @settings-updated="loadAdminSystemConfig"
          />
        </div>
        
        <!-- 缓存管理 -->
        <div v-if="currentPage === 'cache'" class="page-content">
          <CacheCenter />
        </div>

        <div v-if="currentPage === 'strm'" class="page-content">
          <StrmGenerator />
        </div>

        <!-- 跨盘秒传 -->
        <div v-if="currentPage === 'cross-transfer'" class="page-content">
          <CrossDriveTransfer />
        </div>

        <!-- 系统日志 -->
        <div v-if="currentPage === 'logs'" class="page-content">
          <SystemLogs />
        </div>

        <div v-if="currentPage === 'plugins'" class="page-content">
          <PluginCenter />
        </div>
        

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '../stores/admin'
import axios from 'axios'
import { APP_VERSION } from '../constants/app'
import { applyTheme, isValidTheme } from '../utils/theme'
import AccountManagement from '../components/admin/AccountManagement.vue'
import SystemSettings from '../components/admin/SystemSettings.vue'
import CacheCenter from '../components/admin/CacheCenter.vue'
import StrmGenerator from '../components/admin/StrmGenerator.vue'
import CrossDriveTransfer from '../components/admin/CrossDriveTransfer.vue'
import SystemLogs from '../components/admin/SystemLogs.vue'
import PluginCenter from '../components/admin/PluginCenter.vue'
import DriverIcon from '../components/common/DriverIcon.vue'


// 路由
const router = useRouter()
const route = useRoute()
const appVersion = APP_VERSION

// 当前页面状态
const currentPage = ref('dashboard')
const mustChangePassword = ref(false)
const passwordChangeReason = ref('')
const homeReturnMode = ref('top_icon')
const currentTheme = ref('light')
const themeSaving = ref(false)
const dashboardCacheClearing = ref(false)

// 小屏抽屉状态
const sidebarOpen = ref(false)
const toggleSidebar = () => { sidebarOpen.value = !sidebarOpen.value }
const closeSidebar = () => { sidebarOpen.value = false }

const handleEsc = (e) => {
  if (e.key === 'Escape' && sidebarOpen.value) closeSidebar()
}
const handleResize = () => {
  // 回到桌面宽度时自动关闭抽屉，避免遗留状态
  if (window.innerWidth > 768 && sidebarOpen.value) sidebarOpen.value = false
}

// 打开抽屉时锁 body 滚动
watch(sidebarOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

// 使用admin store
const adminStore = useAdminStore()
const { accounts, drivers, loading } = storeToRefs(adminStore)

const pageTitles = {
  dashboard: '仪表盘',
  accounts: '存储管理',
  settings: '系统设置',
  cache: '缓存管理',
  strm: '媒体管理',
  'cross-transfer': '跨盘秒传',
  logs: '系统日志',
  plugins: '插件中心'
}
const adminPageKeys = Object.keys(pageTitles)

const normalizeAdminPage = (page) => {
  const value = String(page || '').trim()
  return adminPageKeys.includes(value) ? value : 'dashboard'
}

const updateAdminPageQuery = (page, method = 'push') => {
  const target = normalizeAdminPage(page)
  if (route.path !== '/admin') return
  if (String(route.query.page || '') === target) return
  router[method]({
    path: '/admin',
    query: {
      ...route.query,
      page: target
    }
  })
}

// 计算属性
const connectedAccounts = computed(() => {
  return accounts.value.filter(a => a.is_active && a.config?.auth_status === 'active').length
})

const currentPageTitle = computed(() => pageTitles[currentPage.value] || '管理后台')
const showSidebarHomeReturn = computed(() => ['sidebar', 'both'].includes(homeReturnMode.value))
const showTopHomeReturn = computed(() => ['top_icon', 'both'].includes(homeReturnMode.value))
const themeLabels = {
  auto: '跟随系统',
  light: '浅色主题',
  dark: '深色主题'
}
const themeIcons = {
  auto: 'fas fa-desktop',
  dark: 'fas fa-moon'
}
const themeIconClass = computed(() => themeIcons[currentTheme.value] || themeIcons.auto)
const themeToggleTitle = computed(() => `当前：${themeLabels[currentTheme.value] || themeLabels.light}，点击切换主题`)
const passwordChangeMessage = computed(() => {
  if (passwordChangeReason.value === 'default_credentials') {
    return '当前仍在使用默认管理员口令（admin/admin）。为保证后台安全，请先修改管理员密码。'
  }
  return '当前管理员密码为非安全状态（未加密或随机重置密码）。为保证后台安全，请先修改管理员密码。'
})
const dashboardStats = ref({
  strmTasks: [],
  cacheRetention: null,
  cacheStats: null,
  logStats: null,
  embyProxies: [],
  systemConfig: null,
})

const totalStrmTasks = computed(() => dashboardStats.value.strmTasks.length)
const runningStrmTasks = computed(() => dashboardStats.value.strmTasks.filter(t => t.status === 'running').length)
const totalCacheKeys = computed(() => dashboardStats.value.cacheStats?.total_keys || 0)
const cacheTotalSizeBytes = computed(() => dashboardStats.value.cacheStats?.total_size_bytes || 0)
const cacheHitRate = computed(() => dashboardStats.value.cacheStats?.hit_rate || 0)
const totalCacheRetentionTasks = computed(() => dashboardStats.value.cacheRetention?.total_count || 0)
const runningCacheRetentionTasks = computed(() => dashboardStats.value.cacheRetention?.running_count || 0)
const pausedStrmTasks = computed(() => dashboardStats.value.strmTasks.filter(t => t.status !== 'running').length)
const pausedCacheRetentionTasks = computed(() => dashboardStats.value.cacheRetention?.paused_count || 0)
const pausedTaskCount = computed(() => pausedStrmTasks.value + pausedCacheRetentionTasks.value)
const totalLogCount = computed(() => dashboardStats.value.logStats?.total || 0)
const recentErrorCount = computed(() => dashboardStats.value.logStats?.recent_errors || 0)
const logRetentionDays = computed(() => dashboardStats.value.systemConfig?.log_retention_days || 30)
const totalEmbyProxies = computed(() => dashboardStats.value.embyProxies.length)
const runningEmbyProxies = computed(() => dashboardStats.value.embyProxies.filter(p => p.status === 'running' && !p.last_error).length)
const embyProxyIssueCount = computed(() => dashboardStats.value.embyProxies.filter(p => p.status !== 'running' || p.last_error).length)

const expiredCount = computed(() =>
  accounts.value.filter(a => a.config?.auth_status === 'token_expired' || a.config?.auth_status === 'failed').length
)

const isAccountUnhealthy = (a) => {
  return !a?.is_active || a?.config?.auth_status === 'token_expired' || a?.config?.auth_status === 'failed'
}

const accountHealthClass = (a) => {
  if (!a.is_active) return 'muted'
  const s = a.config?.auth_status
  if (s === 'token_expired' || s === 'failed') return 'danger'
  return 'ok'
}

const accountHealthLabel = (a) => {
  if (!a.is_active) return '已禁用'
  const s = a.config?.auth_status
  if (s === 'token_expired' || s === 'failed') return '认证失效'
  return '正常'
}

const getDriverColor = (driverType) => {
  if (drivers.value[driverType]?.card_color) return drivers.value[driverType].card_color
  const colors = { pan123: '#4C74DF', '115': '#FF6B35', quark: '#1890FF', baidu: '#2932E1' }
  return colors[driverType] || '#6366f1'
}

const getDriverCardName = (driverType) => {
  if (drivers.value[driverType]?.card_name) return drivers.value[driverType].card_name
  const names = { pan123: '123', '115': '115', quark: 'Q', baidu: '百' }
  return names[driverType] || driverType.charAt(0).toUpperCase()
}

const getDriverLogo = (driverType) => {
  return drivers.value[driverType]?.card_logo || ''
}

const getDriverLabel = (driverType) => {
  if (drivers.value[driverType]?.name) return drivers.value[driverType].name
  return driverType
}

const getDriverCardStyle = (driverType) => {
  const color = getDriverColor(driverType)
  const tail = document?.documentElement?.dataset?.theme === 'dark' ? 'rgba(24, 29, 37, 0.92)' : '#ffffff'
  return {
    '--driver-color': color,
    background: `linear-gradient(135deg, ${hexToRgba(color, 0.18)} 0%, ${hexToRgba(color, 0.08)} 36%, ${tail} 82%)`
  }
}

const hexToRgba = (hex, alpha) => {
  const normalized = String(hex || '').replace('#', '')
  if (!/^[0-9a-fA-F]{6}$/.test(normalized)) return `rgba(76, 116, 223, ${alpha})`
  const value = parseInt(normalized, 16)
  const r = (value >> 16) & 255
  const g = (value >> 8) & 255
  const b = value & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const loadDashboardStats = async () => {
  try {
    const [strmRes, cacheRetentionRes, cacheStatsRes, logStatsRes, embyProxyRes, systemConfigRes] = await Promise.all([
      axios.get('/api/admin/strm/tasks'),
      axios.get('/api/cache-retention/stats'),
      axios.get('/api/admin/cache/stats'),
      axios.get('/api/logs/stats'),
      axios.get('/api/admin/strm/emby-proxies'),
      axios.get('/api/admin/system-config'),
    ])
    dashboardStats.value = {
      strmTasks: strmRes.data?.data || [],
      cacheRetention: cacheRetentionRes.data?.data || null,
      cacheStats: cacheStatsRes.data?.data || null,
      logStats: logStatsRes.data || null,
      embyProxies: embyProxyRes.data?.data || [],
      systemConfig: systemConfigRes.data?.data || null,
    }
  } catch (error) {
    console.error('加载仪表盘统计失败:', error)
  }
}

const formatDashboardSize = (bytes) => {
  const size = Number(bytes || 0)
  if (size <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1)
  return `${parseFloat((size / Math.pow(1024, index)).toFixed(2))} ${units[index]}`
}

const runningTaskCount = computed(() =>
  runningStrmTasks.value + runningCacheRetentionTasks.value + runningEmbyProxies.value
)
const totalTaskCount = computed(() =>
  totalStrmTasks.value + totalCacheRetentionTasks.value + totalEmbyProxies.value
)

const heroOnlineClass = computed(() => {
  if (!accounts.value.length) return 'muted'
  if (expiredCount.value > 0) return 'warn'
  return 'ok'
})

const heroStatusClass = computed(() => {
  if (expiredCount.value > 0) return 'danger'
  if (recentErrorCount.value > 0) return 'warn'
  return ''
})

const heroStatusIcon = computed(() => {
  if (expiredCount.value > 0) return 'fas fa-triangle-exclamation'
  if (recentErrorCount.value > 0) return 'fas fa-circle-exclamation'
  return 'fas fa-check'
})

const dashboardErrorsAcking = ref(false)
const ackDashboardErrors = async () => {
  if (dashboardErrorsAcking.value) return
  dashboardErrorsAcking.value = true
  try {
    const resp = await axios.post('/api/admin/dashboard/ack-errors')
    if (resp.data?.success) {
      window.appNotification?.success?.('已标记为已读，新错误会重新提示')
      await loadDashboardStats()
    } else {
      window.appNotification?.error?.('标记失败：' + (resp.data?.message || '未知错误'))
    }
  } catch (e) {
    window.appNotification?.error?.('标记失败：' + e.message)
  } finally {
    dashboardErrorsAcking.value = false
  }
}

const accountSummaryText = computed(() => {
  const total = accounts.value.length
  if (!total) return '尚未接入'
  const down = accounts.value.filter(isAccountUnhealthy).length
  return down > 0 ? `${total} 个 · ${down} 个异常` : `${total} 个 · 全部在线`
})

const splitCacheSize = computed(() => {
  const text = formatDashboardSize(cacheTotalSizeBytes.value)
  const parts = text.split(' ')
  return { value: parts[0] || '0', unit: parts[1] || 'B' }
})

const jobBarWidth = (running, total) => {
  const t = Number(total || 0)
  if (t <= 0) return '0%'
  const r = Math.max(0, Math.min(t, Number(running || 0)))
  return `${(r / t) * 100}%`
}

const _DOWNLOAD_MODE_TABLE = {
  redirect: { label: '302 直链', icon: 'fas fa-bolt' },
  proxy: { label: '本地代理', icon: 'fas fa-rotate' },
  proxy_server: { label: '代理服务器', icon: 'fas fa-network-wired' },
}

const getDownloadModeLabel = (account) => {
  const mode = String(account?.config?.download_mode || '').trim()
  return _DOWNLOAD_MODE_TABLE[mode]?.label || ''
}

const getDownloadModeIcon = (account) => {
  const mode = String(account?.config?.download_mode || '').trim()
  return _DOWNLOAD_MODE_TABLE[mode]?.icon || 'fas fa-circle'
}

const clearDashboardCache = async () => {
  if (!totalCacheKeys.value || dashboardCacheClearing.value) return
  dashboardCacheClearing.value = true
  try {
    const response = await axios.post('/api/admin/clear-cache')
    if (response.data?.success) {
      window.appNotification?.success?.('缓存已清空')
      await loadDashboardStats()
    } else {
      window.appNotification?.error?.('清空失败: ' + (response.data?.message || '未知错误'))
    }
  } catch (error) {
    window.appNotification?.error?.('清空失败: ' + error.message)
  } finally {
    dashboardCacheClearing.value = false
  }
}

const loadAdminSystemConfig = async () => {
  try {
    const response = await axios.get('/api/admin/system-config')
    if (response.data?.success) {
      const mode = response.data.data?.admin_home_return_mode
      homeReturnMode.value = ['sidebar', 'top_icon', 'both'].includes(mode) ? mode : 'top_icon'
      const theme = response.data.data?.theme
      currentTheme.value = isValidTheme(theme) ? theme : 'light'
      applyTheme(currentTheme.value)
    }
  } catch (error) {
    homeReturnMode.value = 'top_icon'
  }
}

const getNextTheme = (theme) => {
  const order = ['auto', 'light', 'dark']
  const index = order.indexOf(theme)
  return order[(index + 1) % order.length]
}

const toggleTheme = async () => {
  if (themeSaving.value) return
  const previousTheme = isValidTheme(currentTheme.value) ? currentTheme.value : 'light'
  const nextTheme = getNextTheme(previousTheme)
  currentTheme.value = nextTheme
  applyTheme(nextTheme)
  themeSaving.value = true
  try {
    const response = await axios.post('/api/admin/theme', { theme: nextTheme })
    if (!response.data?.success) {
      throw new Error(response.data?.message || '主题保存失败')
    }
  } catch (error) {
    currentTheme.value = previousTheme
    applyTheme(previousTheme)
    window.appNotification?.error?.('主题保存失败: ' + (error.message || '未知错误'))
  } finally {
    themeSaving.value = false
  }
}

// 方法
const isPageLocked = (page) => mustChangePassword.value && page !== 'settings'

const setCurrentPage = (page) => {
  if (isPageLocked(page)) {
    window.appNotification?.warning('请先在“系统设置”中修改管理员密码')
    updateAdminPageQuery('settings')
    closeSidebar()
    return
  }
  updateAdminPageQuery(page)
  closeSidebar()
}

const handleLogout = async () => {
  try {
    const response = await axios.post('/api/auth/logout')
    if (response.data.success) {
      window.appNotification.success('退出登录成功')
      // 跳转到首页
      router.push('/')
    } else {
      window.appNotification.error('退出登录失败')
    }
  } catch (error) {
    console.error('退出登录错误:', error)
    window.appNotification.error('退出登录失败')
  }
}

const handlePasswordUpdated = () => {
  mustChangePassword.value = false
  passwordChangeReason.value = ''
  adminStore.fetchAccounts()
  adminStore.fetchDrivers()
  loadDashboardStats()
}


// ===== 通知系统 =====
const notifications = ref([])
const unreadCount = ref(0)
const showNotificationPanel = ref(false)
let notificationPollingTimer = null

const fetchNotifications = async () => {
  try {
    const [listRes, countRes] = await Promise.all([
      axios.get('/api/admin/notifications'),
      axios.get('/api/admin/notifications/unread-count')
    ])
    notifications.value = listRes.data?.data || []
    unreadCount.value = countRes.data?.data || 0
  } catch (e) {
    console.error('获取通知失败:', e)
  }
}

const toggleNotificationPanel = () => {
  showNotificationPanel.value = !showNotificationPanel.value
  if (showNotificationPanel.value) {
    fetchNotifications()
  }
}

const markAllRead = async () => {
  try {
    await axios.post('/api/admin/notifications/read-all')
    notifications.value.forEach(n => n.read = true)
    unreadCount.value = 0
  } catch (e) {
    console.error('标记全部已读失败:', e)
  }
}

const handleNotificationClick = async (n) => {
  if (!n.read) {
    try {
      await axios.post(`/api/admin/notifications/${n.id}/read`)
      n.read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (e) {
      console.error('标记已读失败:', e)
    }
  }
}

const handleNotificationAction = (n) => {
  if (n.action_route) {
    if (n.action_route.startsWith('/')) {
      setCurrentPage(n.action_route.replace('/', '') || 'dashboard')
    } else {
      router.push(n.action_route)
    }
  }
  showNotificationPanel.value = false
}

const deleteNotification = async (id) => {
  try {
    await axios.delete(`/api/admin/notifications/${id}`)
    const target = notifications.value.find(n => n.id === id)
    notifications.value = notifications.value.filter(n => n.id !== id)
    if (target && !target.read) {
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  } catch (e) {
    console.error('删除通知失败:', e)
  }
}

const formatNotificationTime = (ts) => {
  if (!ts) return ''
  const now = Date.now() / 1000
  const diff = Math.max(0, now - ts)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  const d = new Date(ts * 1000)
  return `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const handleClickOutside = (e) => {
  if (showNotificationPanel.value) {
    const wrapper = document.querySelector('.notification-bell-wrapper')
    if (wrapper && !wrapper.contains(e.target)) {
      showNotificationPanel.value = false
    }
  }
}

// 生命周期
onMounted(async () => {
  window.addEventListener('keydown', handleEsc)
  window.addEventListener('resize', handleResize)
  try {
    const response = await axios.get('/api/auth/status')
    const authData = response.data?.data || {}
    if (!response.data?.success || !authData.is_admin) {
      router.push('/login')
      return
    }

    mustChangePassword.value = Boolean(authData.must_change_password)
    passwordChangeReason.value = String(authData.password_change_reason || '')
    await loadAdminSystemConfig()

    if (mustChangePassword.value) {
      updateAdminPageQuery('settings', 'replace')
      return
    }

    adminStore.fetchAccounts()
    adminStore.fetchDrivers()
    loadDashboardStats()
  } catch (error) {
    router.push('/login')
  }

  // 启动通知轮询
  fetchNotifications()
  notificationPollingTimer = setInterval(fetchNotifications, 30000)
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEsc)
  window.removeEventListener('resize', handleResize)
  document.body.style.overflow = ''
  if (notificationPollingTimer) {
    clearInterval(notificationPollingTimer)
    notificationPollingTimer = null
  }
  document.removeEventListener('click', handleClickOutside)
})

watch(
  () => route.query.page,
  (page) => {
    const target = normalizeAdminPage(page)
    if (page && String(page) !== target) {
      updateAdminPageQuery(target, 'replace')
      return
    }
    if (isPageLocked(target)) {
      updateAdminPageQuery('settings', 'replace')
      currentPage.value = 'settings'
      return
    }
    currentPage.value = target
  },
  { immediate: true }
)
</script>

<style scoped>
/* 管理后台页面样式 */

.admin-container {
  display: flex;
  height: 100vh;
  background-color: #F5F7FA;
}

/* 左侧边栏 */
.sidebar-container {
  width: 220px;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: relative;
  z-index: 1;
}

.sidebar-logo {
  max-width: 128px;
  max-height: 52px;
  width: auto;
  height: auto;
  margin-bottom: 2px;
  object-fit: contain;
}

.sidebar {
  width: 100%;
  background: linear-gradient(180deg, #4C74DF 0%, #02A6F0 100%);
  transition: width 0.28s;
  display: flex;
  flex-direction: column;
  border-top-right-radius: 24px;
  height: 100%;
}

.sidebar-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 25px 0 20px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.sidebar-nav {
  flex-grow: 1;
  padding: 16px;
  margin-top: 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  height: 50px;
  padding: 0 20px;
  color: rgba(255, 255, 255, 0.85);
  text-decoration: none;
  transition: all 0.2s ease;
  border-radius: 16px;
  margin-bottom: 4px;
  cursor: pointer;
  font-weight: 500;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background-color: #fff;
  color: #4C74DF;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-item.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.nav-item.disabled:hover {
  background-color: transparent;
  color: rgba(255, 255, 255, 0.85);
}

.nav-icon {
  margin-right: 24px;
  width: 24px;
  text-align: center;
  font-size: 18px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  text-align: center;
}

.sidebar-version {
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 14px;
  font-weight: 500;
  width: 100%;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #F5F7FA;
}

.navbar {
  background-color: #fff;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.security-warning-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 18px 24px 0;
  padding: 12px 16px;
  border-radius: 12px;
  background: #fff7ed;
  border: 1px solid #fdba74;
  color: #9a3412;
  font-size: 14px;
  font-weight: 500;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.breadcrumb {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.navbar-right {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

/* 汉堡按钮：仅小屏可见 */
.hamburger-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 18px;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
  padding: 0;
}

.hamburger-btn:hover {
  background-color: #F1F5F9;
  color: #4C74DF;
}

.hamburger-btn.active {
  background-color: #EEF2FF;
  color: #4C74DF;
}

/* 抽屉遮罩 */
.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 1000;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.24s ease;
}

.sidebar-backdrop.visible {
  opacity: 1;
  pointer-events: auto;
}

.nav-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-action:hover {
  background-color: #F5F7FA;
  color: #4C74DF;
}

.theme-toggle-action {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
}

.theme-sun-icon {
  width: 19px;
  height: 19px;
  color: #facc15;
}

.theme-toggle-action:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

/* 按钮类型的导航动作 */
.logout-action {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
}

.main-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.main-body::-webkit-scrollbar {
  width: 6px !important;
  height: 6px !important;
}

.main-body::-webkit-scrollbar-button,
.main-body::-webkit-scrollbar-button:start:decrement,
.main-body::-webkit-scrollbar-button:end:increment {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  -webkit-appearance: none !important;
  appearance: none !important;
  background: transparent !important;
  border: none !important;
}

.main-body::-webkit-scrollbar-track {
  background: transparent !important;
}

.main-body::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2) !important;
  border-radius: 3px !important;
  transition: all 0.2s ease !important;
}

.main-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.4) !important;
}

.main-body::-webkit-scrollbar-corner {
  background: transparent !important;
}

/* 页面内容 */
.page-content {
  width: 100%;
  margin: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}

.page-header p {
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
}

/* ═══════════ 仪表盘（重设计 v2） ═══════════ */
.dash-shell {
  display: grid;
  gap: 18px;
}

/* ── A. Hero 顶条 ── */
.dash-hero {
  background: linear-gradient(135deg, #ffffff 0%, #fafbff 100%);
  border: 1px solid #eef2f7;
  border-radius: 16px;
  padding: 18px 24px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.dash-hero.has-issues {
  border-color: #fecaca;
  box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.06);
}

/* 仅有"最近错误日志"时用警告级（橙色）态势，与"账号失效"的硬性问题（红色）区分开 */
.dash-hero.has-warning {
  border-color: #fde68a;
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.06);
}

.dash-hero-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.dash-hero-status {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: #ecfdf5;
  color: #10b981;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  transition: background 0.3s, color 0.3s;
}

.dash-hero-status.warn {
  background: #fffbeb;
  color: #d97706;
}

.dash-hero-status.danger {
  background: #fef2f2;
  color: #ef4444;
}

.dash-hero-text { min-width: 0; }

.dash-hero-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.dash-hero-sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.dash-hero-stats {
  display: flex;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.dash-hero-stat {
  padding: 0 18px;
  text-align: center;
  min-width: 64px;
  border-right: 1px solid #f1f5f9;
}

.dash-hero-stat:last-child { border-right: none; padding-right: 0; }
.dash-hero-stat:first-child { padding-left: 0; }

.dash-hero-stat-val {
  display: block;
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
  letter-spacing: -0.5px;
}

.dash-hero-stat-val.muted { color: #94a3b8; }
.dash-hero-stat-val.ok { color: #10b981; }
.dash-hero-stat-val.warn { color: #ef4444; }

.dash-hero-stat-key {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: #94a3b8;
  letter-spacing: 0.5px;
}

/* ── 2x2 网格 ── */
.dash-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 18px;
  align-items: start;
}

.dash-grid > .dash-col {
  display: grid;
  gap: 18px;
  min-width: 0;
}

/* ── 通用 panel ── */
.dash-panel {
  background: #fff;
  border: 1px solid #eef2f7;
  border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dash-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 8px;
  gap: 12px;
}

.dash-panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  min-width: 0;
}

.dash-panel-title-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dash-panel-title-sub {
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
  margin-left: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-panel-action {
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s;
  flex-shrink: 0;
  font-weight: 500;
}

.dash-panel-action:hover {
  color: #4C74DF;
  background: #eff6ff;
}

.dash-panel-body {
  padding: 8px 20px 18px;
  flex: 1;
  min-width: 0;
}

.dash-panel-foot {
  padding: 12px 20px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfd;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.dash-btn-ghost {
  border: 1px solid #eef2f7;
  background: #fff;
  color: #0f172a;
  padding: 7px 14px;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
  font-weight: 500;
}

.dash-btn-ghost:hover {
  border-color: #4C74DF;
  color: #4C74DF;
}

.dash-btn-danger {
  border: 1px solid #eef2f7;
  background: #fff;
  color: #64748b;
  padding: 7px 14px;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
}

.dash-btn-danger:hover:not(:disabled) {
  color: #ef4444;
  border-color: #fecaca;
  background: #fef2f2;
}

.dash-btn-danger:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* ── B. 存储账号列表 ── */
/* 容器最大显示约 6 行（每行 ~60px + gap 8px ≈ 400px），超出滚动 */
.dash-acc-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 430px;
  overflow-y: auto;
  padding-right: 4px;
  margin-right: -4px;
}

.dash-acc-list::-webkit-scrollbar { width: 4px; }
.dash-acc-list::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.32);
  border-radius: 999px;
}
.dash-acc-list::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.55);
}

.dash-acc-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.2s, filter 0.15s;
  /* 渐变背景由 inline style :style="getDriverCardStyle(...)" 注入 */
}

.dash-acc-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.05);
  filter: saturate(1.04);
}

.dash-acc-row.is-down {
  filter: saturate(0.7);
}

.dash-acc-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: -0.3px;
}

.dash-acc-info { min-width: 0; }

.dash-acc-name {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dash-acc-default-pill {
  font-size: 10px;
  font-weight: 600;
  color: var(--driver-color, #4C74DF);
  background: rgba(255, 255, 255, 0.6);
  padding: 1px 6px;
  border-radius: 5px;
  letter-spacing: 0.3px;
  flex-shrink: 0;
}

.dash-acc-driver {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-acc-mode {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.dash-acc-mode i {
  font-size: 10px;
  color: #cbd5e1;
}

.dash-acc-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: #64748b;
}

.dash-acc-status.warn { color: #ef4444; }

.dash-acc-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dash-acc-dot.ok { background: #10b981; }
.dash-acc-dot.muted { background: #94a3b8; }
.dash-acc-dot.danger { background: #ef4444; animation: dash-dot-pulse 1.8s ease-in-out infinite; }

@keyframes dash-dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}

.dash-acc-empty {
  text-align: center;
  padding: 28px 16px;
}

.dash-acc-empty-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  font-size: 20px;
  color: #94a3b8;
}

.dash-acc-empty p {
  margin: 0 0 12px;
  color: #94a3b8;
  font-size: 13px;
}

.dash-acc-empty button {
  border: none;
  background: #4C74DF;
  color: #fff;
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.dash-acc-empty button:hover {
  background: #3b5fd6;
}

/* ── C. 后台任务列表 ── */
.dash-job-list {
  display: flex;
  flex-direction: column;
}

.dash-job-row {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  align-items: center;
  gap: 14px;
  padding: 14px 8px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: background 0.15s;
}

.dash-job-row:last-child { border-bottom: none; }
.dash-job-row:hover { background: #f8fafc; border-radius: 10px; }

.dash-job-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.dash-job-icon.strm { background: #eef0ff; color: #6366f1; }
.dash-job-icon.retention { background: #e0f2fe; color: #02A6F0; }
.dash-job-icon.emby { background: #fef9c3; color: #ca8a04; }

.dash-job-info { min-width: 0; }

.dash-job-name {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dash-job-meta {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.dash-job-bar {
  flex: 1;
  max-width: 140px;
  height: 4px;
  background: #f1f5f9;
  border-radius: 999px;
  overflow: hidden;
}

.dash-job-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease;
}

.dash-job-bar-fill.strm { background: #6366f1; }
.dash-job-bar-fill.retention { background: #02A6F0; }
.dash-job-bar-fill.emby { background: #ca8a04; }

.dash-job-stat {
  text-align: right;
  flex-shrink: 0;
}

.dash-job-stat-num {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.3px;
}

.dash-job-stat-num .frac {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
}

.dash-job-tag {
  display: inline-block;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 6px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.dash-job-tag.warn { background: #fffbeb; color: #d97706; }
.dash-job-tag.err { background: #fef2f2; color: #ef4444; }

/* ── D. 全局缓存 ── */
.dash-cache-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.dash-cache-cell {
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.dash-cache-cell-num {
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.5px;
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-cache-cell-unit {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

.dash-cache-cell-key {
  margin-top: 4px;
  font-size: 11px;
  color: #94a3b8;
  letter-spacing: 0.3px;
}

.dash-cache-hit {
  margin-top: 14px;
  background: #f8fafc;
  padding: 14px 16px;
  border-radius: 12px;
}

.dash-cache-hit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.dash-cache-hit-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.dash-cache-hit-val {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.dash-cache-hit-bar {
  height: 6px;
  background: #fff;
  border-radius: 999px;
  overflow: hidden;
}

.dash-cache-hit-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4C74DF, #02A6F0);
  border-radius: 999px;
  transition: width 0.3s ease;
}

/* ── E. 日志中心 ── */
.dash-log-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.dash-log-cell {
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.dash-log-cell-num {
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.5px;
  line-height: 1.1;
}

.dash-log-cell-unit {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

.dash-log-cell-key {
  margin-top: 4px;
  font-size: 11px;
  color: #94a3b8;
  letter-spacing: 0.3px;
}

.dash-log-error {
  margin-top: 14px;
  padding: 14px 16px;
  background: #ecfdf5;
  border-radius: 12px;
  border: 1px solid #d1fae5;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: background 0.15s, border-color 0.15s;
}

.dash-log-error.has-error {
  background: #fef2f2;
  border-color: #fecaca;
}

.dash-log-error-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #fff;
  color: #10b981;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dash-log-error.has-error .dash-log-error-icon {
  color: #ef4444;
  cursor: pointer;
}

.dash-log-error-text { flex: 1; min-width: 0; }
.dash-log-error.has-error .dash-log-error-text { cursor: pointer; }
.dash-log-error.has-error .dash-log-error-text:hover .dash-log-error-title {
  color: #ef4444;
}

.dash-log-error-ack {
  flex-shrink: 0;
  border: 1px solid #fecaca;
  background: #fff;
  color: #ef4444;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s;
}

.dash-log-error-ack:hover:not(:disabled) {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #f87171;
}

.dash-log-error-ack:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.dash-log-error-ack i { font-size: 11px; }

.dash-log-error-title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.dash-log-error-sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.dash-log-tip {
  margin-top: 10px;
  font-size: 11px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dash-log-tip i { color: #94a3b8; }

.dash-log-tip a {
  color: #4C74DF;
  text-decoration: none;
}

.dash-log-tip a:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  /* 显示汉堡与遮罩 */
  .hamburger-btn {
    display: inline-flex;
  }

  .sidebar-backdrop {
    display: block;
  }

  /* sidebar 改抽屉：定位为固定覆盖层，默认收起 */
  .sidebar-container {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    width: 260px;
    max-width: 82vw;
    z-index: 1001;
    transform: translateX(-100%);
    transition: transform 0.28s ease;
    box-shadow: 2px 0 16px rgba(15, 23, 42, 0);
  }

  .sidebar-container.open {
    transform: translateX(0);
    box-shadow: 2px 0 16px rgba(15, 23, 42, 0.18);
  }

  /* 抽屉打开时保持右上圆角统一视觉 */
  .sidebar {
    border-top-right-radius: 0;
  }

  .main-body {
    padding: 16px;
  }

  /* 仪表盘小屏：2x2 → 单列 */
  .dash-grid {
    grid-template-columns: 1fr;
  }

  .dash-hero {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
    padding: 16px 18px;
  }

  .dash-hero-stats {
    width: 100%;
    justify-content: space-between;
  }

  .dash-hero-stat {
    flex: 1;
    padding: 0 6px;
    min-width: 0;
  }

  /* 账号行：极窄屏下隐藏 mode 胶囊，避免挤压 */
  .dash-acc-row {
    grid-template-columns: 36px minmax(0, 1fr) auto;
    gap: 10px;
  }

  .dash-acc-mode {
    display: none;
  }
}

@media (max-width: 480px) {
  .dash-cache-grid,
  .dash-log-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== 通知铃铛 ===== */
.notification-bell-wrapper {
  position: relative;
}

.notification-bell {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 17px;
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -8px;
  min-width: 17px;
  height: 17px;
  padding: 0 5px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 17px;
  text-align: center;
  border-radius: 8px;
  pointer-events: none;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.3);
}

.notification-panel {
  position: absolute;
  top: 48px;
  right: 0;
  width: 360px;
  max-width: calc(100vw - 24px);
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.10), 0 1px 4px rgba(15, 23, 42, 0.04);
  border: 1px solid #edf2f9;
  z-index: 2000;
  overflow: hidden;
}

.notification-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.notification-mark-all {
  border: none;
  background: none;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  padding: 3px 6px;
  border-radius: 5px;
  transition: all 0.15s;
}

.notification-mark-all:hover {
  color: #64748b;
  background: #f8fafc;
}

.notification-list {
  max-height: 380px;
  overflow-y: auto;
}

.notification-list::-webkit-scrollbar {
  width: 3px;
}

.notification-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.08);
  border-radius: 2px;
}

.notification-empty {
  padding: 32px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #fafbfc;
  cursor: pointer;
  transition: background 0.12s;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: #fafbfc;
}

.notification-item.unread {
  background: #f8faff;
}

.notification-item.unread:hover {
  background: #f0f3ff;
}

.notification-item-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}

.level-error .notification-item-icon {
  background: #fef2f2;
  color: #ef4444;
}

.level-warning .notification-item-icon {
  background: #fffbeb;
  color: #f59e0b;
}

.level-info .notification-item-icon {
  background: #eff6ff;
  color: #3b82f6;
}

.notification-item-body {
  flex: 1;
  min-width: 0;
}

.notification-item-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.notification-item-message {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-item-time {
  font-size: 11px;
  color: #c0c8d4;
  margin-top: 4px;
}

.notification-item-action {
  flex-shrink: 0;
  align-self: center;
  padding: 4px 0;
  border: none;
  background: none;
  color: #6366f1;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.12s;
}

.notification-item-action:hover {
  color: #4f46e5;
}

.notification-item-close {
  flex-shrink: 0;
  align-self: center;
  width: 22px;
  height: 22px;
  border: none;
  background: none;
  color: #c0c8d4;
  font-size: 10px;
  cursor: pointer;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.12s;
  margin-left: 2px;
}

.notification-item-close:hover {
  background: #f1f5f9;
  color: #94a3b8;
}

/* 更小屏幕的响应式设计 */
@media (max-width: 640px) {
  .navbar {
    padding: 0 12px;
  }
}
</style> 

<style>
:root[data-theme="dark"] .admin-container .main-body::-webkit-scrollbar-track,
:root[data-theme="dark"] .admin-container .dash-acc-list::-webkit-scrollbar-track,
:root[data-theme="dark"] .admin-container .notification-list::-webkit-scrollbar-track {
  background: transparent !important;
}

:root[data-theme="dark"] .admin-container .main-body::-webkit-scrollbar-thumb,
:root[data-theme="dark"] .admin-container .dash-acc-list::-webkit-scrollbar-thumb,
:root[data-theme="dark"] .admin-container .notification-list::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.7) !important;
}

:root[data-theme="dark"] .admin-container .main-body::-webkit-scrollbar-thumb:hover,
:root[data-theme="dark"] .admin-container .dash-acc-list::-webkit-scrollbar-thumb:hover,
:root[data-theme="dark"] .admin-container .notification-list::-webkit-scrollbar-thumb:hover {
  background: rgba(203, 213, 225, 0.86) !important;
}

:root[data-theme="dark"] .admin-container .main-body::-webkit-scrollbar-corner,
:root[data-theme="dark"] .admin-container .dash-acc-list::-webkit-scrollbar-corner,
:root[data-theme="dark"] .admin-container .notification-list::-webkit-scrollbar-corner {
  background: transparent !important;
}
</style>
