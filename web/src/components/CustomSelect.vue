<template>
  <div class="custom-select" :class="{ open: isOpen }" ref="selectRef">
    <div class="select-trigger" @click="toggleDropdown">
      <span class="select-value">{{ displayText }}</span>
      <span class="select-arrow">▼</span>
    </div>
    <Teleport to="body">
      <div 
        class="select-dropdown" 
        v-show="isOpen" 
        ref="dropdownRef"
        :style="dropdownStyle"
      >
        <div 
          v-for="option in options" 
          :key="option.value"
          class="select-option"
          :class="{ selected: option.value === modelValue }"
          :data-value="option.value"
          @click="selectOption(option)"
        >
          {{ option.label }}
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array,
    required: true
  },
  placeholder: {
    type: String,
    default: '请选择'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const isOpen = ref(false)
const selectRef = ref(null)
const dropdownRef = ref(null)

const displayText = computed(() => {
  const selectedOption = props.options.find(option => option.value === props.modelValue)
  return selectedOption ? selectedOption.label : props.placeholder
})

const dropdownStyle = computed(() => {
  if (!isOpen.value || !selectRef.value) return {}
  
  const trigger = selectRef.value.querySelector('.select-trigger')
  if (!trigger) return {}
  
  const rect = trigger.getBoundingClientRect()
  
  return {
    position: 'fixed',
    top: `${rect.bottom + 2}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    zIndex: '100000'
  }
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    // 强制重新计算位置
    nextTick(() => {
      // 触发重新计算
    })
  }
}

const selectOption = (option) => {
  emit('update:modelValue', option.value)
  emit('change', option)
  isOpen.value = false
}

const handleClickOutside = (event) => {
  if (!isOpen.value) return
  
  // 检查是否点击在触发器内
  if (selectRef.value && selectRef.value.contains(event.target)) {
    return
  }
  
  // 检查是否点击在下拉框内
  if (dropdownRef.value && dropdownRef.value.contains(event.target)) {
    return
  }
  
  // 点击在外部，关闭下拉框
  isOpen.value = false
}

onMounted(() => {
  // 使用多种事件类型确保能捕获到点击
  document.addEventListener('click', handleClickOutside, true)
  document.addEventListener('mousedown', handleClickOutside, true)
  document.addEventListener('touchstart', handleClickOutside, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside, true)
  document.removeEventListener('mousedown', handleClickOutside, true)
  document.removeEventListener('touchstart', handleClickOutside, true)
})
</script>

<style scoped>
.custom-select {
  position: relative;
  display: inline-block;
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.2s ease;
  height: 40px;
  box-sizing: border-box;
  font-size: 13px;
  line-height: 1.4;
}

.select-trigger:hover {
  border-color: #9ca3af;
}

.custom-select.open .select-trigger {
  border-color: #4C74DF;
  box-shadow: 0 0 0 2px rgba(76, 116, 223, 0.1);
}

.select-value {
  flex: 1;
  color: #374151;
  font-size: 14px;
}

.select-arrow {
  color: #6b7280;
  font-size: 12px;
  transition: transform 0.2s ease;
}

.custom-select.open .select-arrow {
  transform: rotate(180deg);
}

.select-dropdown {
  position: fixed;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 100000;
  max-height: 200px;
  overflow-y: auto;
}

.select-option {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  transition: background-color 0.2s ease;
}

.select-option:hover {
  background-color: #f8fafc;
}

.select-option.selected {
  /* 移除选中效果，保持和普通选项一样的外观 */
}

.select-option:first-child {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.select-option:last-child {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}
</style> 