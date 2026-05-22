<template>
  <div v-if="loading" class="loading">
    <div class="loading-spinner"></div>
    加载中...
  </div>
  <div v-else class="accounts-grid">
    <div v-for="account in accounts" :key="account.id" class="account-card" :data-account-id="account.id">
      <div class="account-status-bar" :class="accountStatusClass(account)"></div>
      <div class="account-dropdown">
        <button class="dropdown-btn" @click="toggleDropdown(account.id)">
          <i class="fas fa-ellipsis-h"></i>
        </button>
        <div class="dropdown-menu" :class="{ show: account.showDropdown }">
          <a @click="editAccount(account)"><i class="fas fa-edit"></i> 编辑账号</a>
          <template v-if="account.config?.auth_status !== 'token_expired'">
            <a @click="toggleAccountStatus(account)">
              <i class="fas fa-power-off"></i>
              <span v-if="account.is_active">禁用账号</span>
              <span v-else>启用账号</span>
            </a>
            <a @click="setDefaultAccount(account)" v-if="!account.is_default">
              <i class="fas fa-star"></i> 设为默认
            </a>
            <a class="default-indicator" v-if="account.is_default">
              <i class="fas fa-star"></i> 当前默认
            </a>
          </template>
          <a @click="deleteAccount(account)" class="danger"><i class="fas fa-trash"></i> 删除账号</a>
        </div>
      </div>
      <div class="account-info">
        <DriverIcon
          class="driver-icon-large-wrap"
          :logo="getDriverLogo(account.driver_type)"
          :color="getDriverColor(account.driver_type)"
          :name="getDriverCardName(account.driver_type)"
          size="large"
        />
        <div class="account-details">
          <h4 class="account-name">
            {{ account.name }}
            <span v-if="account.config?.auth_status === 'token_expired'" class="auth-expired-tag">认证失效</span>
          </h4>
          <p class="account-time">创建于 {{ formatDate(account.created_at) }}</p>
        </div>
      </div>
    </div>
    <div class="add-account-card" @click="showAddAccount">
      <div class="add-account-content">
        <div class="add-icon"><i class="fas fa-plus"></i></div>
        <div class="add-text">添加账号</div>
      </div>
    </div>
  </div>
  
  <!-- 添加/编辑账号对话框 -->
  <AddAccountDialog
    :visible="showDialog"
    :edit-account="currentEditAccount"
    @close="handleDialogClose"
    @success="handleDialogSuccess"
  />
  
  <!-- 删除确认现在使用现代模态框 -->
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '../../stores/admin'
import { useModal } from '../../composables/useModal.js'
import AddAccountDialog from './AddAccountDialog.vue'
import DriverIcon from '../common/DriverIcon.vue'
import { formatDate } from '../../utils/format.js'

// 使用admin store
const adminStore = useAdminStore()
const { accounts, drivers, loading } = storeToRefs(adminStore)

// 模态框
const { confirm } = useModal()

// 对话框状态
const showDialog = ref(false)
const currentEditAccount = ref(null)
const pendingDeleteAccount = ref(null)

const accountStatusClass = (account) => {
  if (!account.is_active) return 'inactive'
  const authStatus = account.config?.auth_status
  if (authStatus === 'token_expired' || authStatus === 'failed') return 'expired'
  return 'active'
}

// 账号管理方法
const toggleDropdown = (accountId) => {
  // 关闭其他所有下拉菜单
  accounts.value.forEach(account => {
    if (account.id !== accountId) {
      account.showDropdown = false
    }
  })
  
  // 切换当前账号的下拉菜单
  const account = accounts.value.find(acc => acc.id === accountId)
  if (account) {
    const willShow = !account.showDropdown
    if (willShow) {
      adjustDropdownPosition(accountId)
    }
    account.showDropdown = willShow
  }
}

const adjustDropdownPosition = (accountId) => {
  const accountCard = document.querySelector(`[data-account-id="${accountId}"]`)
  if (!accountCard) return
  
  const dropdown = accountCard.querySelector('.dropdown-menu')
  if (!dropdown) return
  
  // 获取元素位置信息
  const dropdownBtn = accountCard.querySelector('.dropdown-btn')
  const btnRect = dropdownBtn.getBoundingClientRect()
  
  // 计算下拉菜单的位置
  let left = btnRect.right - 120 // 默认右对齐
  let top = btnRect.bottom + 5
  
  // 检查右边界
  if (left + 120 > window.innerWidth - 20) {
    left = btnRect.left - 120 // 向左对齐
  }
  
  // 检查下边界
  if (top + 150 > window.innerHeight - 20) {
    top = btnRect.top - 150 // 向上显示
  }
  
  dropdown.style.left = left + 'px'
  dropdown.style.top = top + 'px'
}

const toggleAccountStatus = async (account) => {
  account.showDropdown = false
  try {
    const response = await fetch(`/api/admin/accounts/${account.id}/toggle`, { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const result = await response.json()
    if (result.success) {
      // 直接更新当前账号的状态，保持其他状态不变
      account.is_active = result.data.is_active
      const statusText = account.is_active ? '启用' : '禁用'
      if (window.appNotification) {
        window.appNotification.success(`账号"${account.name}"已${statusText}`)
      }
    } else {
      const errorMsg = result.message || result.detail || '状态切换失败'
      if (window.appNotification) {
        window.appNotification.error(`状态切换失败: ${errorMsg}`)
      }
    }
  } catch (error) {
    console.error('切换状态失败:', error)
    if (window.appNotification) {
      window.appNotification.error(`状态切换失败: ${error.message || '未知错误'}`)
    }
  }
}

const editAccount = async (account) => {
  account.showDropdown = false
  try {
    // 获取完整的账号信息
    const response = await fetch(`/api/admin/accounts/${account.id}`)
    const result = await response.json()
    if (result.success) {
      currentEditAccount.value = result.data
      showDialog.value = true
    } else {
      console.error('获取账号信息失败:', result.message)
    }
  } catch (error) {
    console.error('获取账号信息失败:', error)
  }
}

const deleteAccount = async (account) => {
  account.showDropdown = false
  
  try {
    await confirm({
      title: '确认删除',
      content: `确定要删除账号 「${account.name}」 吗？此操作不可撤销。`,
      confirmText: '删除',
      confirmClass: 'btn-danger',
      icon: 'trash'
    })
    
    await confirmDeleteAccount(account)
  } catch (error) {
    // 用户取消删除
    if (error.message !== 'Modal closed') {
      console.error('删除账号错误:', error)
    }
  }
}

const confirmDeleteAccount = async (account) => {
  try {
    const response = await fetch(`/api/admin/accounts/${account.id}`, { method: 'DELETE' })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const result = await response.json()
    if (result.success) {
      if (window.appNotification) {
        window.appNotification.success('账号删除成功！')
      }
      // 重新加载账号列表
      await adminStore.fetchAccounts()
    } else {
      const errorMsg = result.message || result.detail || '删除失败'
      if (window.appNotification) {
        window.appNotification.error(`删除失败: ${errorMsg}`)
      }
    }
  } catch (error) {
    console.error('删除失败:', error)
    if (window.appNotification) {
      window.appNotification.error(`删除失败: ${error.message || '未知错误'}`)
    }
  } finally {
    pendingDeleteAccount.value = null
  }
}

const setDefaultAccount = async (account) => {
  account.showDropdown = false
  try {
    const response = await fetch(`/api/admin/accounts/${account.id}/set-default`, { method: 'POST' })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const result = await response.json()
    if (result.success) {
      // 重新获取账号列表以更新排序
      await adminStore.fetchAccounts()
      if (window.appNotification) {
        window.appNotification.success(`已将"${account.name}"设为默认账号`)
      }
    } else {
      const errorMsg = result.message || result.detail || '设置默认账号失败'
      if (window.appNotification) {
        window.appNotification.error(`设置默认账号失败: ${errorMsg}`)
      }
    }
  } catch (error) {
    console.error('设置默认账号失败:', error)
    if (window.appNotification) {
      window.appNotification.error(`设置默认账号失败: ${error.message || '未知错误'}`)
    }
  }
}

const showAddAccount = () => {
  currentEditAccount.value = null
  showDialog.value = true
}

// 工具方法
const getDriverColor = (driverType) => {
  // 优先使用从API获取的驱动信息
  if (drivers.value[driverType] && drivers.value[driverType].card_color) {
    return drivers.value[driverType].card_color
  }
  
  // 后备颜色映射
  const colors = {
    'pan123': '#4C74DF',
    '115': '#FF6B35',
    'quark': '#1890FF',
    'baidu': '#2932E1'
  }
  return colors[driverType] || '#6366f1'
}

const getDriverCardName = (driverType) => {
  // 优先使用从API获取的驱动信息
  if (drivers.value[driverType] && drivers.value[driverType].card_name) {
    return drivers.value[driverType].card_name
  }
  
  // 后备名称映射
  const names = {
    'pan123': '123',
    '115': '115',
    'quark': 'Q',
    'baidu': '百'
  }
  return names[driverType] || driverType.charAt(0).toUpperCase()
}

const getDriverLogo = (driverType) => {
  return drivers.value[driverType]?.card_logo || ''
}




// 对话框事件处理
const handleDialogClose = () => {
  showDialog.value = false
  currentEditAccount.value = null
}

const handleDialogSuccess = (message) => {
  // 重新加载账号列表
  adminStore.fetchAccounts()
}

// 点击外部关闭下拉菜单
const handleGlobalClick = (event) => {
  if (!event.target.closest('.account-dropdown')) {
    accounts.value.forEach(account => {
      account.showDropdown = false
    })
  }
}

// 生命周期
onMounted(() => {
  adminStore.fetchAccounts()
  adminStore.fetchDrivers()
  
  document.addEventListener('click', handleGlobalClick)
  window.addEventListener('resize', () => {
    // 重新调整所有打开的下拉菜单位置
    accounts.value.forEach(account => {
      if (account.showDropdown) {
        adjustDropdownPosition(account.id)
      }
    })
  })
})
</script>

<style scoped>
/* 账号卡片网格 */
.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 0;
}

/* 账号卡片样式 */
.account-card {
  background: #fff;
  border-radius: 18px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease;
  overflow: hidden;
  position: relative;
  height: 140px;
  display: flex;
  align-items: center;
  padding: 20px;
}

.account-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 右侧状态条 */
.account-status-bar {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 4px;
  transition: background-color 0.3s ease;
}

.account-status-bar.active {
  background: linear-gradient(180deg, #10b981, #059669);
}

.account-status-bar.inactive {
  background: linear-gradient(180deg, #9ca3af, #6b7280);
}

.account-status-bar.expired {
  background: linear-gradient(180deg, #f87171, #ef4444);
}

/* 下拉菜单 */
.account-dropdown {
  position: absolute;
  top: 8px;
  right: 8px;
}

.dropdown-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
  padding: 8px 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
  min-width: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dropdown-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1e293b;
}

.dropdown-menu {
  position: fixed;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  min-width: 120px;
  opacity: 0;
  visibility: hidden;
  transform: scale(0.95);
  transform-origin: top right;
  transition: opacity 0.15s ease-out, visibility 0.15s ease-out, transform 0.15s ease-out;
  z-index: 10000;
}

.dropdown-menu.show {
  opacity: 1;
  visibility: visible;
  transform: scale(1);
}

.dropdown-menu a {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  color: #374151;
  text-decoration: none;
  font-size: 13px;
  transition: background-color 0.2s ease;
  cursor: pointer;
}

.dropdown-menu a:hover {
  background-color: #f3f4f6;
}

.dropdown-menu a.danger {
  color: #ef4444;
}

.dropdown-menu a.danger:hover {
  background-color: #fef2f2;
}

.dropdown-menu a.default-indicator {
  color: #f59e0b;
  cursor: default;
}

.dropdown-menu a i {
  margin-right: 8px;
  width: 12px;
  text-align: center;
}

/* 账号信息布局 */
.account-info {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.driver-icon-large {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 18px;
  flex-shrink: 0;
}

.driver-icon-large img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.account-details {
  flex: 1;
  min-width: 0;
}

.account-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 8px;
}

.auth-expired-tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 7px;
  font-size: 11px;
  font-weight: 600;
  color: #ef4444;
  background: #fef2f2;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.account-time {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

/* 添加账号卡片 */
.add-account-card {
  background: #fff;
  border: 2px dashed #d1d5db;
  border-radius: 18px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 140px;
  position: relative;
  overflow: hidden;
}

.add-account-card:hover {
  border-color: #4C74DF;
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.add-account-card:hover .add-icon {
  transform: scale(1.1);
  color: #4C74DF;
}

.add-account-card:hover .add-text {
  color: #4C74DF;
}

.add-account-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.add-icon {
  font-size: 24px;
  color: #9ca3af;
  transition: all 0.3s ease;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f3f4f6;
}

.add-text {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  transition: color 0.3s ease;
}

/* 加载状态 */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #64748b;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #4C74DF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .accounts-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .account-card {
    height: auto;
    min-height: 120px;
    padding: 16px;
  }
  
  .add-account-card {
    height: auto;
    min-height: 120px;
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .accounts-grid {
    gap: 12px;
  }
  
  .account-card {
    min-height: 100px;
    padding: 12px;
  }
  
  .add-account-card {
    min-height: 100px;
    padding: 12px;
  }
}
</style> 
