import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  
  // 开发服务器配置
  server: {
    port: 5212,
    proxy: {
      // 代理API请求到后端
      '/api': {
        target: 'http://127.0.0.1:5211',
        changeOrigin: true
      }
    }
  },
  
  // 构建配置
  build: {
    outDir: 'static',
    assetsDir: 'assets',
    // 启用 gzip 压缩
    minify: 'terser',
    // 拆分代码块
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html')
      },
      output: {
        // 手动拆分代码块
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          elementPlus: ['element-plus'],
        }
      }
    },
    // 压缩选项
    terserOptions: {
      compress: {
        drop_console: true, // 移除 console.log
        drop_debugger: true, // 移除 debugger
      }
    }
  },
  
  // 路径别名
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
}) 
