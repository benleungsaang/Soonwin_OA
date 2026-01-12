import { createApp } from 'vue';
import App from './App.vue';
import { createPinia } from 'pinia'; // 状态管理
import ElementPlus from 'element-plus'; // UI组件库
import 'element-plus/dist/index.css'; // Element Plus样式
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'; // 中文语言包
import request from '@/utils/request'; // 封装的Axios请求
import router from '@/router'; // 导入路由配置（关键修正）

// 创建App实例
const app = createApp(App);

// 全局挂载
app.use(createPinia());
app.use(ElementPlus, { locale: zhCn });
app.use(router); // 注册路由
app.config.globalProperties.$request = request; // 全局注入请求工具

// 挂载App
app.mount('#app');