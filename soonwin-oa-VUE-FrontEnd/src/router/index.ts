import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

// 导入页面组件（对应之前创建的视图）
import HomeView from '@/views/HomeView.vue';
import LoginView from '@/views/LoginView.vue';
import PunchSuccessView from '@/views/PunchSuccessView.vue';

// 定义路由规则
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: '首页' } // 页面标题（可选）
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { title: '登录' }
  },
  {
    path: '/punch-success',
    name: 'punchSuccess',
    component: PunchSuccessView,
    meta: { title: '打卡成功' }
  },
  // 后续可新增订单管理、费用核算等路由
  {
    path: '/order',
    name: 'order',
    component: () => import('@/views/OrderView.vue'), // 懒加载组件（优化性能）
    meta: { title: '订单管理', requiresAuth: true } // requiresAuth 标记需要登录才能访问
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // 使用 HTML5 History 模式
  routes // 导入路由规则
});

// 路由守卫：验证需要登录的页面（未登录则跳转登录页）
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title as string || 'SoonWin OA系统';

  // 验证是否需要登录
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('oa_token');
    if (token) {
      next(); // 已登录，放行
    } else {
      next('/login'); // 未登录，跳转登录页
    }
  } else {
    next(); // 不需要登录的页面直接放行
  }
});

export default router;