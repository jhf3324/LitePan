<template>
  <div class="top-nav">
    <div class="nav-left">
      <div v-if="accountSwitchMode === 'dropdown'" class="account-selector">
        <div class="custom-select" :class="{ open: dropdownOpen }" @click="$emit('toggle-dropdown')">
          <div class="select-trigger">
            <span class="select-value">{{ selectedAccountName || '请选择账号' }}</span>
            <svg class="select-arrow" width="16" height="16" viewBox="0 0 20 20" fill="none">
              <path stroke="#6b7280" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m6 8 4 4 4-4" />
            </svg>
          </div>
          <div class="select-dropdown" v-show="dropdownOpen">
            <div class="select-option" @click.stop="$emit('select-account', null)">请选择账号</div>
            <div
              v-for="account in activeAccounts"
              :key="account.id"
              class="select-option"
              :class="{ selected: selectedAccountId === account.id }"
              @click.stop="$emit('select-account', account)"
            >
              {{ account.name }}
            </div>
          </div>
        </div>
      </div>

      <div class="breadcrumb">
        <template v-if="breadcrumbItems.length <= maxBreadcrumbItems">
          <span
            v-for="(item, index) in breadcrumbItems"
            :key="index"
            class="breadcrumb-item"
            :class="{ active: index === breadcrumbItems.length - 1 }"
            :data-id="item.path"
            :title="item.name"
            @click="$emit('navigate-to-path', item.path)"
          >
            <span class="breadcrumb-item-label">{{ item.name }}</span>
          </span>
        </template>

        <template v-else>
          <span
            class="breadcrumb-item"
            :data-id="breadcrumbItems[0].path"
            :title="breadcrumbItems[0].name"
            @click="$emit('navigate-to-path', breadcrumbItems[0].path)"
          >
            <span class="breadcrumb-item-label">{{ breadcrumbItems[0].name }}</span>
          </span>
          <span class="breadcrumb-ellipsis-dropdown">
            <span class="breadcrumb-ellipsis">...</span>
            <div class="breadcrumb-dropdown">
              <div
                v-for="(item, index) in hiddenBreadcrumbItems"
                :key="'hidden-' + index"
                class="breadcrumb-dropdown-item"
                :title="item.name"
                @click="$emit('navigate-to-path', item.path)"
              >
                <span class="breadcrumb-dropdown-item-label">{{ item.name }}</span>
              </div>
            </div>
          </span>
          <span
            v-for="(item, index) in visibleLastItems"
            :key="'last-' + index"
            class="breadcrumb-item"
            :class="{ active: index === visibleLastItems.length - 1 }"
            :data-id="item.path"
            :title="item.name"
            @click="$emit('navigate-to-path', item.path)"
          >
            <span class="breadcrumb-item-label">{{ item.name }}</span>
          </span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  dropdownOpen: {
    type: Boolean,
    default: false
  },
  selectedAccountId: {
    type: [Number, String],
    default: null
  },
  selectedAccountName: {
    type: String,
    default: ''
  },
  activeAccounts: {
    type: Array,
    default: () => []
  },
  breadcrumbItems: {
    type: Array,
    default: () => []
  },
  maxBreadcrumbItems: {
    type: Number,
    default: 4
  },
  hiddenBreadcrumbItems: {
    type: Array,
    default: () => []
  },
  visibleLastItems: {
    type: Array,
    default: () => []
  },
  accountSwitchMode: {
    type: String,
    default: 'dropdown'
  }
})

defineEmits(['toggle-dropdown', 'select-account', 'navigate-to-path'])
</script>
