import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    // 配置路径别名（@指向src目录）
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173, // 前端开发服务器端口
    proxy: {
      // 匹配所有以/api开头的请求，转发到后端
      '/api': {
        target: 'http://localhost:5000', // 后端服务地址
        changeOrigin: true, // 开启跨域请求头修改
        rewrite: (path) => path.replace(/^\/api/, ''), // 去掉请求路径中的/api前缀
      },
    },
  },
});