import { createRouter, createWebHistory } from 'vue-router'
import { APP_TITLE_SUFFIX } from '../constants/app'

const routes = [
  {
    path: '/',
    name: 'Index',
    component: () => import('@/views/Index.vue'),
    meta: {
      title: '文件浏览'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '管理员登录'
    }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: {
      title: '管理后台',
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 设置页面标题和认证检查
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - ${APP_TITLE_SUFFIX}` : APP_TITLE_SUFFIX
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    try {
      const response = await fetch('/api/auth/status')
      const data = await response.json()
      
      if (data.success && data.data.is_admin) {
        // 已认证，允许访问
        next()
      } else {
        // 未认证，重定向到登录页
        next('/login')
      }
    } catch (error) {
      // 请求失败，重定向到登录页
      next('/login')
    }
  } else {
    // 不需要认证，直接访问
    next()
  }
})

export default router 
