import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import path from 'path';
import AutoImport from 'unplugin-auto-import/vite';
import Components from 'unplugin-vue-components/vite';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
// 引入体积分析插件
import { visualizer } from 'rollup-plugin-visualizer';
// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    // 加载对应环境的变量
    const env = loadEnv(mode, process.cwd());
    // 区分开发/生产环境的端口和代理目标
    const isDev = mode === 'development';
    const port = isDev ? Number(env.VITE_PORT || 5173) : Number(env.VITE_PORT || 5183);
    // const proxyTarget = isDev
    //   ? (env.VITE_API_TARGET || 'http://localhost:5001')
    //   : (env.VITE_API_TARGET || `http://${getNetworkIP()}:5000`);
    return {
        plugins: [
            vue({
                template: {
                    compilerOptions: {
                        isCustomElement: (tag) => tag === 'emoji-picker',
                    },
                },
            }),
            // 自动导入 Vue 相关 API（如 ref、reactive、onMounted 等）
            AutoImport({
                resolvers: [ElementPlusResolver()], // 同时自动导入 Element Plus 的 API（如 ElMessage）
                imports: ['vue', 'vue-router'], // 自动导入 Vue、VueRouter 的内置 API
                dts: true, // 生成 auto-imports.d.ts 类型文件，解决 TS 类型提示问题
            }),
            // 自动导入组件（包括 Element Plus 组件）
            Components({
                resolvers: [ElementPlusResolver()], // 自动识别并导入 Element Plus 组件
                dts: true, // 生成 components.d.ts 类型文件
            }),
            // 体积分析插件配置
            visualizer({
                // 生成的分析报告文件名，默认在项目根目录
                filename: 'dist/stats.html',
                // 分析模式：treemap（树形图，最直观）、sunburst（旭日图）、network（网络拓扑）
                template: 'treemap',
                // 开启 gzip 体积分析（可选，更贴近实际传输体积）
                gzipSize: true,
                // 开启 brotli 体积分析（可选）
                brotliSize: true,
                // 是否在打包完成后自动打开报告页面（可选）
                open: true,
            })
        ],
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
                },
                // 将 /assets 开头的请求代理到后端（用于静态文件服务）
                '/assets': {
                    target: env.VITE_API_TARGET || 'http://localhost:5001',
                    changeOrigin: true,
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
    };
});
