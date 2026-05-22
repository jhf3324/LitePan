import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import axios from 'axios'

export const useAdminStore = defineStore('admin', () => {
  // 状态
  const accounts = ref([])
  const drivers = ref({})
  const loading = ref(false)
  
  // 获取所有可用驱动
  const fetchDrivers = async () => {
    try {
      loading.value = true
      const response = await axios.get('/api/admin/drivers')
      if (response.data.success) {
        drivers.value = response.data.data
      }
    } catch (error) {
      console.error('获取驱动列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取驱动配置结构
  const getDriverConfigSchema = async (driverName) => {
    try {
      const response = await axios.get(`/api/admin/drivers/${driverName}/config-schema`)
      if (response.data.success) {
        return response.data.data
      }
      throw new Error('获取配置结构失败')
    } catch (error) {
      console.error('获取驱动配置结构失败:', error)
      throw error
    }
  }
  
  // 获取所有账号
  const fetchAccounts = async () => {
    try {
      loading.value = true
      const response = await axios.get('/api/admin/accounts')
      if (response.data.success) {
        // 为每个账号添加前端所需的属性
        accounts.value = response.data.data.map(account => ({
          ...account,
          showDropdown: false
          // is_active 和 is_default 直接使用后端返回的值
        }))
      }
    } catch (error) {
      console.error('获取账号列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 创建账号
  const createAccount = async (accountData) => {
    try {
      loading.value = true
      const response = await axios.post('/api/admin/accounts', accountData)
      if (response.data.success) {
        // 刷新账号列表
        await fetchAccounts()
        // 显示成功通知
        if (window.appNotification) {
          window.appNotification.success('账号添加成功！')
        }
        return response.data
      }
      const errorMsg = response.data.message || '创建账号失败'
      if (window.appNotification) {
        window.appNotification.error(errorMsg)
      }
      throw new Error(errorMsg)
    } catch (error) {
      console.error('创建账号失败:', error)
      
      // 🔧 改进错误处理：避免重复的"添加失败"前缀
      let errorMessage = '未知错误'
      
      if (error.response && error.response.data) {
        // HTTP错误响应，使用后端返回的详细信息
        if (error.response.data.detail) {
          errorMessage = error.response.data.detail
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message
        }
      } else if (error.message) {
        // 网络错误或其他错误
        errorMessage = error.message
      }
      
      if (window.appNotification) {
        window.appNotification.error(errorMessage)
      }
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 更新账号
  const updateAccount = async (accountId, accountData) => {
    try {
      loading.value = true
      const response = await axios.put(`/api/admin/accounts/${accountId}`, accountData)
      if (response.data.success) {
        // 刷新账号列表
        await fetchAccounts()
        // 显示成功通知
        if (window.appNotification) {
          window.appNotification.success('账号更新成功！')
        }
        return response.data
      }
      const errorMsg = response.data.message || '更新账号失败'
      if (window.appNotification) {
        window.appNotification.error('更新失败: ' + errorMsg)
      }
      throw new Error(errorMsg)
    } catch (error) {
      console.error('更新账号失败:', error)
      
      // 🔧 改进错误处理：优先使用后端返回的详细错误信息
      let errorMessage = '更新失败: 未知错误'
      
      if (error.response && error.response.data) {
        // HTTP错误响应，使用后端返回的详细信息
        if (error.response.data.detail) {
          errorMessage = `更新失败: ${error.response.data.detail}`
        } else if (error.response.data.message) {
          errorMessage = `更新失败: ${error.response.data.message}`
        }
      } else if (error.message) {
        // 网络错误或其他错误
        errorMessage = `更新失败: ${error.message}`
      }
      
      if (window.appNotification) {
        window.appNotification.error(errorMessage)
      }
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 删除账号
  const deleteAccount = async (accountId) => {
    try {
      loading.value = true
      const response = await axios.delete(`/api/admin/accounts/${accountId}`)
      if (response.data.success) {
        // 刷新账号列表
        await fetchAccounts()
        return response.data
      }
      throw new Error(response.data.message || '删除账号失败')
    } catch (error) {
      console.error('删除账号失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 测试账号连接
  const testAccountConnection = async (accountId) => {
    try {
      const response = await axios.post(`/api/admin/accounts/${accountId}/test`)
      return response.data
    } catch (error) {
      console.error('测试连接失败:', error)
      throw error
    }
  }
  
  return {
    // 状态
    accounts,
    drivers,
    loading,
    
    // 方法
    fetchDrivers,
    getDriverConfigSchema,
    fetchAccounts,
    createAccount,
    updateAccount,
    deleteAccount,
    testAccountConnection
  }
}) 