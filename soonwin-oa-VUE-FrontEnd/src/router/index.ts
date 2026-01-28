import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

// 懒加载页面组件以优化性能（按需加载）
const HomeView = () => import('@/views/HomeView.vue');
const LoginView = () => import('@/views/LoginView.vue');
const PunchView = () => import('@/views/PunchView.vue');
const PunchSuccessView = () => import('@/views/PunchSuccessView.vue');
const PunchRecordsView = () => import('@/views/PunchRecordsView.vue');
const EmployeeManagementView = () => import('@/views/EmployeeManagementView.vue');
const ExpenseManagementView = () => import('@/views/ExpenseManagementView.vue');
const OrderInspectionView = () => import('@/views/OrderInspectionView.vue');
const InspectionReportView = () => import('@/views/InspectionReportView.vue');
const DisplayFileUploadView = () => import('@/views/DisplayFileUploadView.vue');
const DisplayFileView = () => import('@/views/DisplayFileView.vue');
const InquiryListView = () => import('@/views/InquiryListView.vue');
const InquiryView = () => import('@/views/InquiryView.vue');
const MachinePartsManagementView = () => import('@/views/MachinePartsManagementView.vue');

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
    path: '/punch',
    name: 'punch',
    component: PunchView,
    meta: { title: '打卡', requiresAuth: true } // requiresAuth 标记需要登录才能访问
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
  },
  {
    path: '/punch-records',
    name: 'punchRecords',
    component: PunchRecordsView,
    meta: { title: '打卡记录', requiresAuth: true, requiresAdmin: true } // requiresAuth 标记需要登录才能访问，requiresAdmin 标记需要管理员权限
  },
  {
    path: '/employee-management',
    name: 'employeeManagement',
    component: EmployeeManagementView,
    meta: { title: '员工管理', requiresAuth: true, requiresAdmin: true } // requiresAuth 标记需要登录才能访问，requiresAdmin 标记需要管理员权限
  },
  {
    path: '/expense-management',
    name: 'expenseManagement',
    component: ExpenseManagementView,
    meta: { title: '费用管理', requiresAuth: true, requiresAdmin: true } // requiresAuth 标记需要登录才能访问，requiresAdmin 标记需要管理员权限
  },
  {
    path: '/order-inspection',
    name: 'orderInspection',
    component: OrderInspectionView,
    meta: { title: '订单验收', requiresAuth: true } // requiresAuth 标记需要登录才能访问
  },
  {
    path: '/inspection-report/:inspectionId',
    name: 'inspectionReport',
    component: InspectionReportView,
    props: true,
    meta: { title: '验收报告', requiresAuth: true } // requiresAuth 标记需要登录才能访问
  },
  {
    path: '/display-file-upload',
    name: 'displayFileUpload',
    component: DisplayFileUploadView,
    meta: { title: '上传展示文件', requiresAuth: true, requiresAdmin: true } // requiresAuth 标记需要登录才能访问，requiresAdmin 标记需要管理员权限
  },
  {
    path: '/display-files',
    name: 'displayFiles',
    component: DisplayFileView,
    meta: { title: '展示文件', requiresAuth: true } // requiresAuth 标记需要登录才能访问
  },
  {
    path: '/inquiries',
    name: 'inquiries',
    component: InquiryListView,
    meta: { title: '询盘管理', requiresAuth: true } // requiresAuth 标记需要登录才能访问
  },
  {
    path: '/inquiry',
    name: 'inquiryCreate',
    redirect: '/inquiries',
    meta: { title: '新增询盘', requiresAuth: true } // requiresAuth 标记需要登录才能访问
  },
  {
    path: '/inquiry/:id',
    name: 'inquiryEdit',
    redirect: '/inquiries',
    meta: { title: '编辑询盘', requiresAuth: true } // requiresAuth 标记需要登录才能访问
  },
  {
    path: '/machine-parts-management',
    name: 'machinePartsManagement',
    component: MachinePartsManagementView,
    meta: { title: '机器零部件管理', requiresAuth: true, requiresAdmin: true } // requiresAuth 标记需要登录才能访问，requiresAdmin 标记需要管理员权限
  },
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(), // 使用 HTML5 History 模式
  routes // 导入路由规则
});

// 路由守卫：验证需要登录的页面（未登录则跳转登录页）
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  document.title = to.meta.title as string || 'SoonWin OA系统';

  // 验证是否需要登录
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('oa_token');
    if (token) {
      // 检查是否需要管理员权限
      if (to.meta.requiresAdmin) {
        try {
          // 解码JWT token获取用户角色信息
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.user_role === 'admin') {
            next(); // 管理员权限，放行
          } else {
            // 非管理员用户尝试访问管理员页面
            alert('您没有权限访问此页面！');
            next('/'); // 返回首页
          }
        } catch (error) {
          console.error('解析用户信息失败:', error);
          next('/login'); // 解析失败，跳转登录页
        }
      } else {
        next(); // 已登录，放行
      }
    } else {
      next('/login'); // 未登录，跳转登录页
    }
  } else {
    next(); // 不需要登录的页面直接放行
  }
});

export default router;