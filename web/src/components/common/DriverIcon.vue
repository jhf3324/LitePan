<template>
  <img
    v-if="logo && !imgError"
    :src="logo"
    :alt="name || 'driver'"
    :class="['driver-icon-img', `size-${size}`, { 'no-frame': frame === false }]"
    :title="title"
    @error="imgError = true"
  >
  <div
    v-else
    :class="['driver-icon-fallback', `size-${size}`]"
    :style="{ background: color || '#6366f1' }"
    :title="title"
  >
    {{ name || '盘' }}
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  logo: {
    type: String,
    default: '',
  },
  color: {
    type: String,
    default: '',
  },
  name: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'badge',
    validator: (v) => ['mini', 'badge', 'large', 'xlarge', 'floating'].includes(v),
  },
  frame: {
    type: Boolean,
    default: true,
  },
})

const imgError = ref(false)

watch(() => props.logo, () => {
  imgError.value = false
})
</script>

<style scoped>
.driver-icon-img,
.driver-icon-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-sizing: border-box;
  overflow: hidden;
}

.driver-icon-img {
  object-fit: cover;
  background: transparent;
  border: none;
  padding: 0;
}

.driver-icon-img.no-frame {
  border-radius: 0;
}

.driver-icon-fallback {
  color: #fff;
  font-weight: 600;
  line-height: 1;
  user-select: none;
}

.driver-icon-img.size-mini,
.driver-icon-fallback.size-mini {
  width: 24px;
  height: 24px;
  font-size: 10px;
  border-radius: 6px;
}

.driver-icon-img.size-badge,
.driver-icon-fallback.size-badge {
  width: 36px;
  height: 36px;
  font-size: 12px;
  border-radius: 10px;
}

.driver-icon-img.size-floating,
.driver-icon-fallback.size-floating {
  width: 36px;
  height: 36px;
  font-size: 12px;
  border-radius: 10px;
}

.driver-icon-img.size-large,
.driver-icon-fallback.size-large {
  width: 48px;
  height: 48px;
  font-size: 14px;
  border-radius: 10px;
}

.driver-icon-img.size-xlarge,
.driver-icon-fallback.size-xlarge {
  width: 64px;
  height: 64px;
  font-size: 16px;
  border-radius: 12px;
}
</style>
