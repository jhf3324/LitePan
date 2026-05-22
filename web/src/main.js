import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import axios from 'axios'

// 全局 Axios 拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // 排除 auth 接口
      if (error.config.url !== '/api/auth/status' && error.config.url !== '/api/auth/login') {
        // 如果当前是在需要管理员权限的路由下，或者是请求了明确的 admin 接口
        const currentRoute = router.currentRoute.value
        const isApiAdmin = error.config.url.startsWith('/api/admin/')
        
        if (currentRoute.meta.requiresAuth || isApiAdmin) {
          router.push('/login')
          // 静默处理 401 错误，防止它继续抛给组件里的 catch 块去弹窗
          return new Promise(() => {}) 
        }
      }
    }
    return Promise.reject(error)
  }
)

// iconfont Symbol 雪碧图（需在首屏注入，供 SvgIcon / 通知条 <use> 引用）
import './assets/iconfont/iconfont.js'

// 只引入必要的 Element Plus 样式
import './assets/global.css'
import './assets/index.css'
import './assets/modern-modal.css'

// 引入通知系统
import './utils/notification.js'

const app = createApp(App)

app.use(router)
app.use(createPinia())

app.mount('#app') 
