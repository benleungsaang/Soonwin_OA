import { defineConfig, loadEnv } from 'vite';
import type { ConfigEnv, UserConfig } from 'vite'; // 类型-only导入
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
// import os from 'os';
import path from 'path';

// function getNetworkIP() {
//   const interfaces = os.networkInterfaces();
//   for (const name of Object.keys(interfaces)) {
//     const netInterface = interfaces[name];
//     if (netInterface) { // 检查netInterface是否为null或undefined
//       for (const item of netInterface) {
//         // 跳过内部/回环地址和IPv6地址
//         if (!item.internal && item.family === 'IPv4') {
//           // 排除docker等虚拟网卡，可以添加特定网络接口过滤
//           if (!name.includes('docker') && !name.includes('vEthernet')) {
//             return item.address;
//           }
//         }
//       }
//     }
//   }
//   // 如果无法获取IP，返回默认IP
//   return '192.168.1.24';
// }

// https://vitejs.dev/config/
export default defineConfig(({ mode }: ConfigEnv): UserConfig => {
  // 加载对应环境的变量
  const env = loadEnv(mode, process.cwd());
  // 区分开发/生产环境的端口和代理目标
  const isDev = mode === 'development';
  const port = isDev ? Number(env.VITE_PORT || 5173) : Number(env.VITE_PORT || 5183);
  // const proxyTarget = isDev
  //   ? (env.VITE_API_TARGET || 'http://localhost:5001')
  //   : (env.VITE_API_TARGET || `http://${getNetworkIP()}:5000`);

  return {
    plugins: [vue()],
    // 开发服务器配置
    server: {
      // 开发环境前端访问端口（对应 .env.development 的 5173）
      port: port, // 关联配置的端口
      // 自动打开浏览器
      open: false, // 暂时关闭自动打开
      // 允许跨域
      cors: true,
      // 接口代理（开发环境转发到 5001）
      host: '0.0.0.0', // 统一允许外部访问
      proxy: isDev ? {
        // 将 /api 开头的请求代理到后端
        '/api': {
          // target: proxyTarget,
          target: env.VITE_API_TARGET || 'http://localhost:5001',
          changeOrigin: true,
          // 不重写路径，保持/api前缀完整传递给后端
          // 开发环境保留/api前缀（和后端一致）
          // rewrite: (path) => path.replace(/^\/api/, '')
        }
      } : {}, // 生产环境清空proxy（打包后不生效）
    },
    // 构建配置
    // build: {
    //   outDir: 'dist',
    //   sourcemap: false
    // },
    // 路径别名
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        'pdfjs-dist': path.resolve(__dirname, 'node_modules/pdfjs-dist'),
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('vue') || id.includes('vue-router')) {
                return 'vue';
              }
              if (id.includes('element-plus')) {
                return 'element-plus';
              }
              if (id.includes('pdfjs-dist')) {
                return 'pdf';
              }
              return 'vendor';
            }
          }
        }
      }
    },
  }
})