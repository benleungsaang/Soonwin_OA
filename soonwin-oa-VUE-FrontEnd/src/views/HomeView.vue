<template>
  <div class="home-container">
    <!-- 二维码弹窗 -->
    <el-dialog v-model="showQrCodeDialog" title="网站二维码" width="300px" align-center>
      <div style="display: flex; flex-direction: column; align-items: center;">
        <canvas ref="qrCodeCanvasRef"></canvas>
        <p style="margin-top: 10px; color: #666; font-size: 13px;">扫描二维码访问网站首页</p>
      </div>
    </el-dialog>

    <el-container style="height: 100vh;">
      <!-- 头部区域：标题 + 右上角退出登录 -->
      <el-header class="header">
        <h1>{{ appTitle }}</h1>
        <div class="header-actions">
          <el-button
            class="qr-btn"
            @click="showQrCodeDialog = true"
            v-if="hasToken"
          >
            <el-icon><Grid /></el-icon><span class="btn-text">二维码</span>
          </el-button>
          <el-button
            class="logout-btn"
            @click="logout"
            v-if="hasToken"
          >
            <el-icon><SwitchButton /></el-icon><span class="btn-text">{{ currentUserName && currentUserEmpId ? `用户 ${currentUserEmpId} [ ${currentUserName} ] 登出` : '登出' }}</span>
          </el-button>
        </div>
      </el-header>

      <!-- 主体菜单区域：靠上展示无位移 -->
      <el-main class="main">
        <el-card shadow="hover" class="card">
          <el-divider></el-divider>

          <!-- 三列菜单容器：核心用order控制排序 -->
          <div class="menu-container" v-if="permissionsLoaded">
            <!-- 资源管理：PC左（order1），移动端第2（order2） -->
            <div class="menu-column resource-column">
              <div class="column-header" @click="toggleCollapse('resource')">
                <h3 class="column-title">资源管理</h3>
                <el-icon class="collapse-icon">
                  <ArrowDown v-if="!collapseStatus.resource" />
                  <ArrowRight v-else />
                </el-icon>
              </div>
              <transition name="menu-collapse" :duration="300">
                <div class="menu-wrapper" v-if="!collapseStatus.resource">
                  <el-menu :default-active="activeMenu" class="menu-list">
                    <el-menu-item index="13" @click="goToPhotoManagement" v-if="hasToken && permissions.photoManage">
                      <el-icon><Picture /></el-icon>
                      <span>照片管理</span>
                    </el-menu-item>
                    <el-menu-item index="14" @click="goToVideoManagement" v-if="hasToken && permissions.videoManage">
                      <el-icon><VideoCamera /></el-icon>
                      <span>视频管理</span>
                    </el-menu-item>
                    <el-menu-item index="15" @click="goToMachineManagementNew" v-if="hasToken && permissions.machineManage">
                      <el-icon><Tools /></el-icon>
                      <span>设备管理</span>
                    </el-menu-item>
                    <el-menu-item index="5" @click="goToExpenseManagement" v-if="hasToken && permissions.expenseManage">
                      <el-icon><Money /></el-icon>
                      <span>运营费用</span>
                    </el-menu-item>
                    <el-menu-item index="4" @click="goToEmployeeManagement" v-if="hasToken && permissions.employeeManage">
                      <el-icon><User /></el-icon>
                      <span>员工管理</span>
                    </el-menu-item>
                  </el-menu>
                </div>
              </transition>
            </div>

            <!-- 订单跟进：PC中（order2），移动端第1（order1） -->
            <div class="menu-column order-column" v-if="hasOrderMenu">
              <div class="column-header" @click="toggleCollapse('order')">
                <h3 class="column-title">订单跟进</h3>
                <el-icon class="collapse-icon">
                  <ArrowDown v-if="!collapseStatus.order" />
                  <ArrowRight v-else />
                </el-icon>
              </div>
              <transition name="menu-collapse" :duration="300">
                <div class="menu-wrapper" v-if="!collapseStatus.order">
                  <el-menu :default-active="activeMenu" class="menu-list">
                    <el-menu-item index="9" @click="goToInquiries" v-if="hasToken && permissions.inquiriesManage">
                      <el-icon><ChatDotRound /></el-icon>
                      <span>询盘登记表</span>
                    </el-menu-item>
                    <el-menu-item index="1" @click="goToOrder" v-if="hasToken && permissions.orderManage">
                      <el-icon><Document /></el-icon>
                      <span>订单管理</span>
                    </el-menu-item>

                    <el-menu-item index="16" @click="goToOrderStatus" v-if="hasToken && permissions.orderStatusManage">
                      <el-icon><List /></el-icon>
                      <span>订单状态管理</span>
                    </el-menu-item>
                    <el-menu-item index="18" @click="goToQuotationManagement" v-if="hasToken && permissions.quotationManage">
                      <el-icon><Coin /></el-icon>
                      <span>初步报价</span>
                    </el-menu-item>
                    <el-menu-item index="19" @click="goToOrderRecordManage" v-if="hasToken && permissions.orderRecordManage">
                      <el-icon><Wallet /></el-icon>
                      <span>订单快速记录</span>
                    </el-menu-item>
                    <el-menu-item index="20" @click="goToCustomerManage" v-if="hasToken && permissions.customerManage">
                      <el-icon><User /></el-icon>
                      <span>客户信息管理</span>
                    </el-menu-item>
                  </el-menu>
                </div>
              </transition>
            </div>

            <!-- 其它功能：PC右（order3），移动端第3（order3） -->
            <div class="menu-column other-column">
              <div class="column-header" @click="toggleCollapse('other')">
                <h3 class="column-title">其它功能</h3>
                <el-icon class="collapse-icon">
                  <ArrowDown v-if="!collapseStatus.other" />
                  <ArrowRight v-else />
                </el-icon>
              </div>
              <transition name="menu-collapse" :duration="300">
                <div class="menu-wrapper" v-if="!collapseStatus.other">
                  <el-menu :default-active="activeMenu" class="menu-list">
                    <el-menu-item index="2" @click="goToPunchIn" v-if="hasToken && permissions.punchManage">
                      <el-icon><Monitor /></el-icon>
                      <span>打卡</span>
                    </el-menu-item>
                    <el-menu-item index="3" @click="goToPunchRecords" v-if="hasToken && permissions.punchRecordsManage && userRole === 'admin'">
                      <el-icon><Timer /></el-icon>
                      <span>打卡记录</span>
                    </el-menu-item>
                    <el-menu-item index="10" @click="goToDisplayFiles" v-if="hasToken && permissions.displayFilesManage">
                      <el-icon><Files /></el-icon>
                      <span>展示文件</span>
                    </el-menu-item>
                    <el-menu-item index="17" @click="goToAttendanceSystem" v-if="hasToken && permissions.attendanceManage">
                      <el-icon><Clock /></el-icon>
                      <span>考勤系统</span>
                    </el-menu-item>
                  </el-menu>
                  <!-- 登录按钮：未登录时显示在其它功能列底部 -->
                  <el-menu class="menu-list login-menu" v-if="!hasToken">
                    <el-menu-item index="7" @click="goToLogin">
                      <el-icon><User /></el-icon>
                      <span>登录</span>
                    </el-menu-item>
                  </el-menu>
                </div>
              </transition>
            </div>
          </div>

          <!-- 权限加载时显示加载状态 -->
          <div v-else class="loading-container" style="display: flex; justify-content: center; align-items: center; height: 200px;">
            <el-icon class="is-loading">
              <Loading />
            </el-icon>
            <span style="margin-left: 10px;">正在加载权限信息...</span>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  Tools, Document, User, Clock, ChatDotRound, Money, Coin,
  Monitor,  Files, Picture, VideoCamera, ArrowDown, ArrowRight, Timer, List, Loading, Wallet, SwitchButton, Grid
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import QRCode from 'qrcode';
// 导入权限工具函数
import {
  hasToken as checkHasToken,
  hasModulePermission,
  hasRoutePermission,
  ModuleNames,
  loadUserPermissions,
  clearUserPermissions,
  initUserPermissions,
  getCurrentUserName,
  getCurrentUserEmpId
} from '@/utils/authUtils';

// 路由实例
const router = useRouter();
// 应用标题
const appTitle = ref(import.meta.env.VITE_APP_TITLE);
// 当前激活的菜单
const activeMenu = ref('1');
// 是否已登录（存在token）
const hasToken = ref(false);
// 权限是否已加载
const permissionsLoaded = ref(false);
// 用户角色
const userRole = ref<string | null>(null);
// 当前用户名
const currentUserName = ref<string | null>(null);
// 当前用户员工ID
const currentUserEmpId = ref<string | null>(null);

// 二维码弹窗
const showQrCodeDialog = ref(false);
const qrCodeCanvasRef = ref<HTMLCanvasElement | null>(null);

watch(showQrCodeDialog, async (newVal) => {
  if (newVal) {
    await nextTick();
    if (qrCodeCanvasRef.value) {
      const rootUrl = window.location.origin + '/';
      await QRCode.toCanvas(qrCodeCanvasRef.value, rootUrl, { width: 200, margin: 2 });
    }
  }
});

// 折叠状态控制：默认订单跟进展开，其余折叠
const collapseStatus = ref({
  resource: false,  // 资源管理：默认折叠
  order: false,    // 订单跟进：默认展开
  other: false      // 其它功能：默认折叠
});

// ========== 优化1：统一管理权限标识，动态生成权限判断 ==========
// 定义权限标识与功能名称的映射表（核心：把所有权限集中管理）
const permissionMap = {
  employeeManage: { key: 'user_manage', name: '员工管理', path: '/employee-management' },
  expenseManage: { key: 'expense_manage', name: '运营费用', path: '/expense-management' },
  photoManage: { key: 'photo_manage', name: '照片管理', path: '/photo-management' },
  videoManage: { key: 'video_manage', name: '视频管理', path: '/video-management' },
  orderManage: { key: 'order_manage', name: '订单管理', path: '/order' },
  inquiriesManage: { key: 'inquiry_manage', name: '询盘登记表', path: '/inquiries' },
  orderStatusManage: { key: 'order_status_manage', name: '订单状态管理', path: '/order-status' },
  punchManage: { key: 'punch_manage', name: '打卡', path: '/punch' },
  punchRecordsManage: { key: 'punch_manage', name: '打卡记录', path: '/punch-records' },
  displayFilesManage: { key: 'display_file_manage', name: '展示文件', path: '/display-files' },
  machineManage: { key: 'machine_manage', name: '设备管理（新版）', path: '/machine-management-new' },
  userManage: { key: 'user_manage', name: '用户管理', path: '/employee-management' },
  attendanceManage: { key: 'attendance_manage', name: '考勤系统', path: '/attendance-system' },
  quotationManage: { key: 'quotation_manage', name: '临时报价', path: '/quotation-management' },
  orderRecordManage: { key: 'order_record_manage', name: '订单快速记录', path: '/order-record' },
  customerManage: { key: 'customer_manage', name: '客户信息管理', path: '/customer-management' }
};

// 动态生成权限计算属性（替代原来的多个零散computed）
const permissions = computed(() => {
  const result: Record<string, boolean> = {};
      Object.entries(permissionMap).forEach(([key, { key: permissionKey }]) => {
      result[key] = hasRoutePermission(permissionKey as any);
    });  return result;
});

// 订单跟进栏目是否有可显示的菜单项
const hasOrderMenu = computed(() => {
  if (!hasToken.value) return false; // 未登录时不显示
  // 判断订单跟进下的所有权限项是否有至少一个为true
  return permissions.value.inquiriesManage || permissions.value.orderManage || permissions.value.orderStatusManage || permissions.value.quotationManage || permissions.value.orderRecordManage;
});

// ========== 方法定义 ==========
// ========== 优化2：封装通用跳转方法（自动处理权限检查） ==========
/**
 * 通用页面跳转方法（带权限检查）
 * @param permissionKey 权限标识（对应permissionMap的key）
 * @param tipName 无权限时提示的功能名称（可选，默认用permissionMap中的name）
 */
const navigateToPage = (permissionKey: keyof typeof permissionMap, tipName?: string) => {
  const { key, name, path } = permissionMap[permissionKey];
  if (hasRoutePermission(key as any)) {
    router.push(path);
  } else {
    ElMessage.error(`您没有权限访问${tipName || name}页面！`);
  }
};

// ========== 简化后的跳转方法（基于通用方法封装） ==========
const goToOrder = () => navigateToPage('orderManage');
const goToPunchIn = () => navigateToPage('punchManage');
const goToPunchRecords = () => navigateToPage('punchRecordsManage');
const goToEmployeeManagement = () => navigateToPage('employeeManage');
const goToExpenseManagement = () => navigateToPage('expenseManage');
const goToLogin = () => router.push('/login');
const goToInquiries = () => navigateToPage('inquiriesManage');
const goToDisplayFiles = () => navigateToPage('displayFilesManage');
const goToPhotoManagement = () => navigateToPage('photoManage');
const goToVideoManagement = () => navigateToPage('videoManage');
const goToOrderStatus = () => navigateToPage('orderStatusManage');
const goToAttendanceSystem = () => navigateToPage('attendanceManage');
const goToMachineManagementNew = () => navigateToPage('machineManage');
const goToQuotationManagement = () => navigateToPage('quotationManage');
const goToOrderRecordManage = () => navigateToPage('orderRecordManage');
const goToCustomerManage = () => navigateToPage('customerManage');

// 折叠/展开切换方法
const toggleCollapse = (column: 'resource' | 'order' | 'other') => {
  collapseStatus.value[column] = !collapseStatus.value[column];
};

// 页面挂载时检查登录状态和加载权限
onMounted(async () => {
  hasToken.value = checkHasToken();
  if (hasToken.value) {
    try {
      // 一次性获取权限数据，同时初始化权限和角色
      const request = (await import('@/utils/request')).default;
      const response: any = await request.get('/api/user/permissions');

      if (response && Array.isArray(response) && response.length > 0) {
        // 使用第一条权限记录的角色名作为用户角色
        userRole.value = response[0].role_name;

        // 初始化用户权限
        initUserPermissions(response);
      } else {
        // 如果没有获取到权限数据，使用降级处理
        userRole.value = null;
        await loadUserPermissions(); // 调用原有逻辑
      }
    } catch (error) {
      console.error('加载用户权限和角色失败:', error);
      // 降级处理：尝试从token中获取角色并加载权限
      userRole.value = null;
      await loadUserPermissions();
    }

    // 获取当前用户名 - 直接从token解析以确保使用正确的字段名
    const token = localStorage.getItem('oa_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        // JWT payload中使用的是'name'字段，而不是'user_name'
        currentUserName.value = payload.name || payload.user_name || null;
        // 同时获取员工ID
        currentUserEmpId.value = payload.emp_id || null;
      } catch (error) {
        console.error('解析用户信息失败:', error);
        // 降级处理：尝试使用函数获取
        currentUserName.value = getCurrentUserName();
        currentUserEmpId.value = getCurrentUserEmpId();
      }
    }
  }
  // 设置权限已加载状态，以确保菜单项正确显示
  permissionsLoaded.value = true;
});



// 退出登录
const logout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    const currentUserName = getCurrentUserName();
    const currentUserEmpId = getCurrentUserEmpId();
    const userNameDisplay = currentUserName && currentUserEmpId ? `(${currentUserEmpId}[${currentUserName}])` : '';

    localStorage.removeItem('oa_token');
    clearUserPermissions(); // 清空权限缓存
    hasToken.value = false;
    ElMessage.success(`用户${userNameDisplay}已退出登录`);
    router.push('/login');
  } catch (error) {
    // 用户取消操作，不执行任何操作
    if (error !== 'cancel') {
      console.error('退出登录失败：', error);
    }
  }
};</script>

<style scoped>
.home-container {
  width: 100%;
  height: 100%;
}

/* 头部样式：固定高度防位移 */
.header {
  background-color: #0653a0;
  color: white;
  text-align: center;
  border-radius: 8px;
  font: hevatica, sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  padding: 0 20px;
  height: 60px;
}

.logout-btn {
  color: rgb(255, 255, 255);
  background-color: rgba(82, 177, 255, 0.1);
  font-size: 14px;
  border: rgba(0, 0, 0, 0.2) solid 1px;
}
.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.header-actions {
  position: absolute;
  right: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.qr-btn {
  color: rgb(255, 255, 255);
  background-color: rgba(82, 177, 255, 0.1);
  font-size: 14px;
  border: rgba(0, 0, 0, 0.2) solid 1px;
}
.qr-btn:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

/* 主体区域：靠上展示，无位移 */
.main {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  background-color: #f5f7fa;
  padding: 20px 0 20px 0;
  height: calc(100vh - 60px);
  box-sizing: border-box;
}

.card {
  width: 90%;
  max-width: 1200px;
  padding: 20px;
  border-radius: 8px;
  min-height: 200px;
  box-sizing: border-box;
}

/* 菜单容器：核心用flex + order控制排序，PC横向，移动端纵向 */
.menu-container {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
  padding-top: 10px;
  width: 100%;
}

/* 通用列样式：PC等分宽度，移动端100%宽度 */
.menu-column {
  flex: 1;
  min-width: 250px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

/* PC端排序控制：核心order属性（数值越小越靠左） */
.resource-column { order: 1; } /* 资源管理-左 */
.order-column { order: 2; }    /* 订单跟进-中 */
.other-column { order: 3; }   /* 其它功能-右 */

/* 列头部：固定宽度，防位移 */
.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 8px 10px;
  border-radius: 6px;
  flex-shrink: 0;
  width: 100%;
}
.column-header:hover {
  background-color: #e8f4ff;
}

/* 列标题样式 */
.column-title {
  font-size: 18px;
  color: #0653a0;
  margin: 0;
  padding-left: 10px;
  border-left: 4px solid #0653a0;
}

/* 折叠图标样式 */
.collapse-icon {
  color: #0653a0;
  transition: all 0.3s ease;
}

/* 菜单包裹层：防压缩 */
.menu-wrapper {
  width: 100%;
  margin-top: 8px;
  flex-grow: 1;
}

/* 菜单列表样式 */
.menu-list {
  border: none !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.login-menu {
  margin-top: 12px !important;
}

/* 菜单项样式：固定尺寸，防压缩换行 */
.el-menu-item {
  height: 60px !important;
  line-height: 60px !important;
  font-size: 16px !important;
  border-radius: 6px !important;
  margin-bottom: 8px !important;
  width: 100% !important;
  box-sizing: border-box !important;
  white-space: nowrap !important;
  overflow: visible !important;
}
.el-menu-item:hover {
  background-color: #e8f4ff !important;
}

/* 折叠/展开平滑动画 */
.menu-collapse-enter-from,
.menu-collapse-leave-to {
  max-height: 0 !important;
  opacity: 0 !important;
  overflow: hidden !important;
}
.menu-collapse-enter-to,
.menu-collapse-leave-from {
  max-height: 800px !important;
  opacity: 1 !important;
}
.menu-collapse-enter-active,
.menu-collapse-leave-active {
  transition: all 0.2s ease-in-out !important;
  overflow: hidden !important;
}

/* 移动端适配（768px以下）：核心调整排序+纵向排列 */
@media (max-width: 768px) {
  .menu-container {
    flex-direction: column;
    gap: 15px;
  }
  .menu-column {
    min-width: 100%;
    align-items: stretch;
  }
  /* 移动端排序控制：修改order值，实现 订单1、资源2、其它3 */
  .order-column { order: 1; }    /* 订单跟进-第1 */
  .resource-column { order: 2; } /* 资源管理-第2 */
  .other-column { order: 3; }   /* 其它功能-第3 */

  /* 头部移动端：改为两端对齐，防止标题与按钮重叠 */
  .header {
    justify-content: space-between;
    padding: 0 10px;
    height: 50px;
  }
  .header h1 {
    font-size: 15px;
    flex-shrink: 1;
    margin-right: 8px;
  }
  .header-actions {
    position: static;
    gap: 4px;
    flex-shrink: 0;
  }
  .logout-btn, .qr-btn {
    font-size: 11px;
    padding: 5px 8px;
  }
  .card {
    width: 95%;
    padding: 10px;
  }
  .el-menu-item {
    height: 50px !important;
    line-height: 50px !important;
    font-size: 14px !important;
  }
  .column-title {
    font-size: 16px;
  }
}

/* 小屏手机适配（480px以下） */
@media (max-width: 480px) {
  .header {
    padding: 0 6px;
    height: 44px;
  }
  .header h1 {
    font-size: 13px;
    margin-right: 4px;
  }
  .header-actions {
    gap: 3px;
  }
  .logout-btn, .qr-btn {
    font-size: 10px;
    padding: 4px 6px;
  }
  .btn-text {
    display: none;
  }
  .el-menu-item {
    height: 45px !important;
    line-height: 45px !important;
    font-size: 13px !important;
  }
}
</style>