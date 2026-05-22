import { reactive, markRaw } from 'vue'

// 全局模态框状态
const modalState = reactive({
  isVisible: false,
  title: '',
  content: '',
  type: 'default', // default, confirm, form, custom
  size: 'medium', // small, medium, large, fullscreen
  closable: true,
  maskClosable: false, // 默认禁用点击外部关闭，只允许ESC键关闭
  loading: false,
  data: null,
  resolve: null,
  reject: null
})

// 表单状态
const formState = reactive({
  fields: [],
  values: {},
  errors: {}
})

let modalResetTimer = null

const clearPendingModalReset = () => {
  if (modalResetTimer) {
    clearTimeout(modalResetTimer)
    modalResetTimer = null
  }
}

export function useModal() {
  // 显示模态框
  const showModal = (options) => {
    return new Promise((resolve, reject) => {
      clearPendingModalReset()
      Object.assign(modalState, {
        ...options,
        isVisible: true,
        resolve,
        reject
      })
    })
  }

  // 关闭模态框
  const closeModal = () => {
    modalState.isVisible = false
    if (modalState.reject) {
      modalState.reject(new Error('Modal closed'))
    }
    resetModal()
  }

  // 确认模态框
  const confirmModal = (result) => {
    modalState.isVisible = false
    if (modalState.resolve) {
      modalState.resolve(result)
    }
    resetModal()
  }

  // 重置模态框状态
  const resetModal = () => {
    clearPendingModalReset()
    modalResetTimer = setTimeout(() => {
      Object.assign(modalState, {
        title: '',
        content: '',
        type: 'default',
        size: 'medium',
        modalClass: '',
        bodyClass: '',
        closable: true,
        maskClosable: false, // 保持与默认配置一致
        loading: false,
        data: null,
        resolve: null,
        reject: null,
        // 重置按钮和图标相关属性
        confirmClass: null,
        confirmText: null,
        cancelText: null,
        icon: null,
        hideCancelButton: false,
        checkboxLabel: null,
        checkboxChecked: false,
        hideFooter: false
      })
      Object.assign(formState, {
        fields: [],
        values: {},
        errors: {}
      })
      modalResetTimer = null
    }, 300) // 等待动画完成
  }

  // 确认对话框
  const confirm = (options) => {
    return showModal({
      type: 'confirm',
      size: 'medium', // 改为medium，与form模态框保持一致
      hideCancelButton: options?.hideCancelButton ?? true,
      ...options
    })
  }

  // 表单对话框
  const form = (options) => {
    // 初始化表单状态
    formState.fields = options.fields || []
    formState.values = {}
    formState.errors = {}
    
    // 设置默认值
    formState.fields.forEach(field => {
      formState.values[field.name] = field.defaultValue || ''
    })

    return showModal({
      type: 'form',
      size: options.size || 'medium',
      ...options,
      data: options
    })
  }

  // 自定义模态框
  const custom = (options) => {
    const data = {
      ...options,
      component: options.component ? markRaw(options.component) : null,
      componentProps: options.componentProps || null
    }
    return showModal({
      type: 'custom',
      hideFooter: options.hideFooter ?? true,
      ...options,
      data
    })
  }

  // 设置加载状态
  const setLoading = (loading) => {
    modalState.loading = loading
  }

  return {
    modalState,
    formState,
    showModal,
    closeModal,
    confirmModal,
    confirm,
    form,
    custom,
    setLoading
  }
} 
