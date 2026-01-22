import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import os from 'os';
import path from 'path';
function getNetworkIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        const netInterface = interfaces[name];
        if (netInterface) { // 检查netInterface是否为null或undefined
            for (const item of netInterface) {
                // 跳过内部/回环地址和IPv6地址
                if (!item.internal && item.family === 'IPv4') {
                    // 排除docker等虚拟网卡，可以添加特定网络接口过滤
                    if (!name.includes('docker') && !name.includes('vEthernet')) {
                        return item.address;
                    }
                }
            }
        }
    }
    // 如果无法获取IP，返回默认IP
    return '192.168.1.24';
}
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        // 配置路径别名（@指向src目录）
        alias: {
            '@': resolve(__dirname, 'src'),
            'pdfjs-dist': path.resolve(__dirname, 'node_modules/pdfjs-dist'),
        },
    },
    server: {
        host: '0.0.0.0', // 允许外部访问
        port: 5173, // 前端开发服务器端口
        proxy: {
            // 匹配所有以/api开头的请求，转发到后端
            '/api': {
                target: process.env.VITE_API_TARGET || `http://${getNetworkIP()}:5000`, // 后端服务地址，优先使用环境变量，否则自动检测本机IP
                changeOrigin: true, // 开启跨域请求头修改
                // 不重写路径，保持/api前缀完整传递给后端
            },
        },
    },
});
