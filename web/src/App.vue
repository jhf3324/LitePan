<template>
  <div id="app">
    <router-view />
    <!-- 全局模态框 -->
    <ModernModal />
  </div>
</template>

<script setup>
import ModernModal from './components/common/ModernModal.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: #f5f5f5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  min-height: 100vh;
}

/* 全局样式 */
.page-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin: 20px;
}

.page-header {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e6e6e6;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.page-description {
  color: #909399;
  font-size: 14px;
}

/* 按钮样式 */
.btn-group {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

/* 表格样式 */
.table-container {
  margin-top: 20px;
}

/* 表单样式 */
.form-container {
  max-width: 600px;
}

.form-footer {
  text-align: right;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e6e6e6;
}

/* 状态标签 */
.status-tag {
  font-size: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-container {
    margin: 10px;
    padding: 15px;
  }
  
  .btn-group {
    flex-direction: column;
  }
  
  .form-container {
    max-width: 100%;
  }
}
</style> 
