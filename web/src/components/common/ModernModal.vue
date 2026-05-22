<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div 
        v-if="modalState.isVisible" 
        class="modern-modal-overlay"
      >
        <Transition name="modal-scale">
          <div 
            class="modern-modal" 
            :class="modalClasses" 
            @click.stop
          >
            <!-- 模态框头部 - 只在有标题时显示 -->
            <div v-if="modalState.title" class="modern-modal-header">
              <h3 class="modern-modal-title">{{ modalState.title }}</h3>
              <button 
                v-if="modalState.closable" 
                class="modern-modal-close" 
                @click="closeModal"
                type="button"
                aria-label="关闭"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                </svg>
              </button>
            </div>
            
            <!-- 无标题时的关闭按钮 -->
            <div v-if="!modalState.title && modalState.closable" class="modern-modal-close-absolute">
              <button 
                class="modern-modal-close" 
                @click="closeModal"
                type="button"
                aria-label="关闭"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                </svg>
              </button>
            </div>
            
            <!-- 模态框内容 -->
            <div class="modern-modal-body" :class="modalState.bodyClass">
              <!-- 表单模式 -->
              <div 
                v-if="modalState.type === 'form'" 
                :class="['modern-form', modalState.data?.className]"
              >
                <div 
                  v-for="field in formState.fields" 
                  :key="field.name" 
                  :class="['form-group', field.className]"
                >
                  <label :for="field.name">{{ field.label }}</label>
                  <input 
                    v-if="['text', 'email', 'password', 'number'].includes(field.type)"
                    :id="field.name"
                    :name="field.name"
                    :type="field.type"
                    :placeholder="field.placeholder"
                    :readonly="field.readonly"
                    :class="field.className"
                    :autofocus="field.autofocus"
                    v-model="formState.values[field.name]"
                    @input="clearError(field.name)"
                    @keyup.enter="handleConfirm"
                    autocomplete="off"
                  />
                  <textarea 
                    v-else-if="field.type === 'textarea'"
                    :id="field.name"
                    :name="field.name"
                    :placeholder="field.placeholder"
                    :readonly="field.readonly"
                    :class="field.className"
                    v-model="formState.values[field.name]"
                    @input="clearError(field.name)"
                  ></textarea>
                  <div v-if="formState.errors[field.name]" class="form-error">
                    {{ formState.errors[field.name] }}
                  </div>
                </div>
              </div>
              
              <!-- 确认模式 -->
              <div v-else-if="modalState.type === 'confirm'" class="modern-confirm">
                <div class="confirm-icon">
                  <div class="flat-icon" :class="getIconBackgroundClass()">
                    <i v-if="modalState.icon === 'warning'" class="fas fa-exclamation-triangle warning-icon"></i>
                    <i v-else-if="modalState.icon === 'error'" class="fas fa-times-circle error-icon"></i>
                    <i v-else-if="modalState.icon === 'trash'" class="fas fa-trash-alt danger-icon"></i>
                    <i v-else-if="modalState.icon === 'question'" class="fas fa-question-circle question-icon"></i>
                    <i v-else class="fas fa-info-circle info-icon"></i>
                  </div>
                </div>
                <div class="confirm-content">
                  <div class="confirm-message">{{ modalState.content }}</div>
                  <label v-if="modalState.checkboxLabel" class="confirm-checkbox">
                    <input v-model="modalState.checkboxChecked" type="checkbox">
                    <span>{{ modalState.checkboxLabel }}</span>
                  </label>
                </div>
              </div>
              
              <!-- 自定义内容 -->
              <div v-else-if="modalState.type === 'custom'">
                <component
                  v-if="modalState.data?.component"
                  :is="modalState.data.component"
                  v-bind="modalState.data.componentProps || {}"
                  @resolve="confirmModal"
                  @cancel="closeModal"
                />
                <div v-else class="custom-content-text">{{ modalState.content }}</div>
              </div>
              
              <!-- 默认内容 -->
              <div v-else>
                {{ modalState.content }}
              </div>
            </div>
            
            <!-- 模态框底部 -->
            <div v-if="showFooter" class="modern-modal-footer">
              <button 
                v-if="(modalState.type === 'confirm' || modalState.type === 'form') && !modalState.hideCancelButton"
                class="btn btn-secondary" 
                @click="closeModal"
                :disabled="modalState.loading"
              >
                {{ modalState.cancelText || '取消' }}
              </button>
              <button 
                v-if="modalState.type === 'confirm' || modalState.type === 'form'"
                :class="['btn', modalState.confirmClass || 'btn-primary']" 
                @click="handleConfirm"
                :disabled="modalState.loading"
              >
                <!-- DEBUG: {{modalState.confirmClass}} -->
                <span v-if="modalState.loading" class="loading-spinner-small"></span>
                {{ modalState.confirmText || '确定' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useModal } from '../../composables/useModal.js'

const { modalState, formState, closeModal, confirmModal } = useModal()

// 提取文件名（排除后缀）的函数
const extractFileNameWithoutExtension = (fullName) => {
  const lastDotIndex = fullName.lastIndexOf('.')
  if (lastDotIndex === -1) {
    return fullName // 没有后缀，返回完整名称
  }
  return fullName.substring(0, lastDotIndex)
}

// 监听模态框显示状态，处理自动聚焦和文本选中
watch(() => modalState.isVisible, (visible) => {
  if (visible && modalState.type === 'form') {
    nextTick(() => {
      // 查找第一个带有autofocus属性的输入框
      const autofocusField = formState.fields.find(field => field.autofocus)
      if (autofocusField) {
        const input = document.getElementById(autofocusField.name)
        if (input) {
          input.focus()
          
          // 如果需要选中文本且是重命名操作
          if (autofocusField.selectText && autofocusField.defaultValue) {
            const fileNameWithoutExt = extractFileNameWithoutExtension(autofocusField.defaultValue)
            if (fileNameWithoutExt) {
              // 延迟一点确保输入框已经完全聚焦
              setTimeout(() => {
                input.setSelectionRange(0, fileNameWithoutExt.length)
              }, 50)
            }
          }
        }
      }
    })
  }
})

// ESC键关闭模态框
const handleKeydown = (event) => {
  if (event.key === 'Escape' && modalState.isVisible) {
    event.preventDefault()
    event.stopPropagation()
    event.stopImmediatePropagation?.()
    closeModal()
  }
}

// 添加和移除键盘事件监听器
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 模态框样式类
const modalClasses = computed(() => {
  const classes = []
  if (modalState.size) {
    classes.push(`modal-${modalState.size}`)
  }
  if (modalState.loading) {
    classes.push('modal-loading')
  }
  if (modalState.modalClass) {
    classes.push(modalState.modalClass)
  }
  return classes
})

const showFooter = computed(() => {
  if (modalState.hideFooter) return false
  return modalState.type === 'confirm' || modalState.type === 'form'
})

// 注意：已移除点击外部关闭功能，只保留ESC键关闭

// 清除表单错误
const clearError = (fieldName) => {
  if (formState.errors[fieldName]) {
    delete formState.errors[fieldName]
  }
}

// 获取图标背景类
const getIconBackgroundClass = () => {
  const icon = modalState.icon
  if (icon === 'warning') return 'warning-bg'
  if (icon === 'error') return 'error-bg'
  if (icon === 'trash') return 'danger-bg'
  if (icon === 'question') return 'question-bg'
  return 'info-bg'
}

// 处理确认
const handleConfirm = async () => {
  if (modalState.loading) return

  try {
    if (modalState.type === 'form') {
      // 表单验证
      const validate = modalState.data?.validate
      if (validate) {
        await validate(formState.values)
      }
      
      // 必填验证
      for (const field of formState.fields) {
        if (field.required && !formState.values[field.name]?.trim()) {
          formState.errors[field.name] = `请输入${field.label}`
          return
        }
      }
      
      confirmModal(formState.values)
    } else if (modalState.type === 'confirm') {
      if (modalState.checkboxLabel) {
        confirmModal({ checked: !!modalState.checkboxChecked })
      } else {
        confirmModal(true)
      }
    } else {
      confirmModal()
    }
  } catch (error) {
    if (modalState.type === 'form') {
      // 显示验证错误（跳过空错误消息）
      if (error.field && error.message) {
        formState.errors[error.field] = error.message
      } else if (error.message && error.message.trim()) {
        // 通用错误显示在第一个字段（仅当有实际错误消息时）
        const firstField = formState.fields[0]
        if (firstField) {
          formState.errors[firstField.name] = error.message
        }
      }
      // 如果是空错误消息，不显示任何错误，模态框保持开启
    }
  }
}

// 清理了所有冗余的按钮处理代码
</script>

<style scoped>
.custom-content-text {
  white-space: pre-wrap;
  word-break: break-word;
  color: #374151;
  line-height: 1.7;
}

/* 动画效果 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-scale-enter-active,
.modal-scale-leave-active {
  transition: all 0.3s ease;
}

.modal-scale-enter-from,
.modal-scale-leave-to {
  transform: scale(0.9);
  opacity: 0;
}

.confirm-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  font-size: 14px;
  color: #475569;
  cursor: pointer;
}

.confirm-checkbox input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.confirm-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
}

.confirm-message {
  width: 100%;
}
</style>

<!-- 删除了自定义的冗余样式，依赖modern-modal.css --> 
