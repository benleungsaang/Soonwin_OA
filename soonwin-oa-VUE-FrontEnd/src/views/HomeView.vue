<template>
  <div class="home-container">
    <el-container style="height: 100vh;">
      <!-- 头部区域：标题 + 右上角退出登录 -->
      <el-header class="header">
        <h1>{{ appTitle }}</h1>
        <el-button
          icon="SwitchButton"
          class="logout-btn"
          @click="logout"
          v-if="hasToken"
        >
          退出登录
        </el-button>
      </el-header>

      <!-- 主体菜单区域：靠上展示无位移 -->
      <el-main class="main">
        <el-card shadow="hover" class="card">
          <el-divider></el-divider>

          <!-- 三列菜单容器：核心用order控制排序 -->
          <div class="menu-container">
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
                    <el-menu-item index="13" @click="goToPhotoManagement" v-if="hasToken && hasPhotoManagePermission">
                      <el-icon><Picture /></el-icon>
                      <span>照片管理</span>
                    </el-menu-item>
                    <el-menu-item index="14" @click="goToVideoManagement" v-if="hasToken && hasVideoManagePermission">
                      <el-icon><VideoCamera /></el-icon>
                      <span>视频管理</span>
                    </el-menu-item>
                    <el-menu-item index="12" @click="goToMachinePartsManagement" v-if="hasToken && hasMachinePartsManagePermission">
                      <el-icon><Tools /></el-icon>
                      <span>机器零部件管理</span>
                    </el-menu-item>
                    <el-menu-item index="5" @click="goToExpenseManagement" v-if="hasToken && hasExpenseManagePermission">
                      <el-icon><Money /></el-icon>
                      <span>运营费用</span>
                    </el-menu-item>
                    <el-menu-item index="4" @click="goToEmployeeManagement" v-if="hasToken && hasEmployeeManagePermission">
                      <el-icon><User /></el-icon>
                      <span>员工管理</span>
                    </el-menu-item>
                  </el-menu>
                </div>
              </transition>
            </div>

            <!-- 订单跟进：PC中（order2），移动端第1（order1） -->
            <div class="menu-column order-column">
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
                    <el-menu-item index="9" @click="goToInquiries" v-if="hasToken && hasInquiriesManagePermission">
                      <el-icon><Document /></el-icon>
                      <span>询盘登记表</span>
                    </el-menu-item>
                    <el-menu-item index="1" @click="goToOrder" v-if="hasToken && hasOrderManagePermission">
                      <el-icon><Document /></el-icon>
                      <span>订单管理</span>
                    </el-menu-item>
                    <el-menu-item index="16" @click="goToOrderProgress" v-if="hasToken && hasOrderProgressManagePermission">
                      <el-icon><List /></el-icon>
                      <span>订单进度管理</span>
                    </el-menu-item>
                    <el-menu-item index="16" @click="goToOrderStatus" v-if="hasToken && hasOrderStatusManagePermission">
                      <el-icon><List /></el-icon>
                      <span>订单状态管理</span>
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
                    <el-menu-item index="2" @click="goToPunchIn" v-if="hasToken && hasPunchManagePermission">
                      <el-icon><Monitor /></el-icon>
                      <span>打卡</span>
                    </el-menu-item>
                    <el-menu-item index="3" @click="goToPunchRecords" v-if="hasToken && isCurrentUserAdmin">
                      <el-icon><Timer /></el-icon>
                      <span>打卡记录</span>
                    </el-menu-item>
                    <el-menu-item index="10" @click="goToDisplayFiles" v-if="hasToken">
                      <el-icon><Files /></el-icon>
                      <span>展示文件</span>
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
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import {
  Tools, Document, User, Clock, SwitchButton, Money, Finished,
  Monitor, Upload, Files, Box, Picture, VideoCamera, ArrowDown, ArrowRight, Timer, List
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
// 导入权限工具函数
import {
  hasToken as checkHasToken,
  hasModulePermission,
  ModuleNames,
  loadUserPermissions,
  clearUserPermissions
} from '@/utils/authUtils';

// 路由实例
const router = useRouter();
// 应用标题
const appTitle = ref(import.meta.env.VITE_APP_TITLE);
// 当前激活的菜单
const activeMenu = ref('1');
// 是否已登录（存在token）
const hasToken = ref(false);
// 折叠状态控制：默认订单跟进展开，其余折叠
const collapseStatus = ref({
  resource: false,  // 资源管理：默认折叠
  order: false,    // 订单跟进：默认展开
  other: false      // 其它功能：默认折叠
});

// ========== 权限判断计算属性 ==========
const hasEmployeeManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.EMPLOYEE_MANAGE, 'view');
});

const hasExpenseManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.EXPENSE_MANAGE, 'view');
});

const hasMachinePartsManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.MACHINE_MANAGE, 'view');
});

const hasPhotoManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.PHOTO_MANAGE, 'view');
});

const hasVideoManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.VIDEO_MANAGE, 'view');
});

const hasOrderManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.ORDER_MANAGE, 'view');
});

const hasInquiriesManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.INQUIRY_MANAGE, 'view');
});

const hasOrderStatusManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.ORDER_STATUS_MANAGE, 'view');
});

const hasPunchManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.PUNCH_MANAGE, 'view');
});

const hasDisplayFilesManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.DISPLAY_FILES_MANAGE, 'view');
});

const hasOrderProgressManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.ORDER_PROGRESS_MANAGE, 'view');
});

const hasDeviceManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.DEVICE_MANAGE, 'view');
});

const hasUserManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.USER_MANAGE, 'view');
});



// ========== 方法定义 ==========
// 折叠/展开切换方法
const toggleCollapse = (column: 'resource' | 'order' | 'other') => {
  collapseStatus.value[column] = !collapseStatus.value[column];
};

// 页面挂载时检查登录状态和加载权限
onMounted(async () => {
  hasToken.value = checkHasToken();
  if (hasToken.value) {
    // 加载用户权限
    await loadUserPermissions();
  }
});

// 所有跳转方法（增加权限检查）
const goToOrder = () => {
  if (hasOrderManagePermission.value) {
    router.push('/order');
  } else {
    ElMessage.error('您没有权限访问订单管理页面！');
  }
};

const goToPunchIn = () => {
  if (hasPunchManagePermission.value) {
    router.push('/punch');
  } else {
    ElMessage.error('您没有权限访问打卡页面！');
  }
};

const goToPunchRecords = () => {
  if (hasPunchManagePermission.value) {
    router.push('/punch-records');
  } else {
    ElMessage.error('您没有权限访问打卡记录页面！');
  }
};

const goToEmployeeManagement = () => {
  if (hasEmployeeManagePermission.value) {
    router.push('/employee-management');
  } else {
    ElMessage.error('您没有权限访问员工管理页面！');
  }
};

const goToExpenseManagement = () => {
  if (hasExpenseManagePermission.value) {
    router.push('/expense-management');
  } else {
    ElMessage.error('您没有权限访问运营费用页面！');
  }
};

const goToLogin = () => router.push('/login');



const goToInquiries = () => {
  if (hasInquiriesManagePermission.value) {
    router.push('/inquiries');
  } else {
    ElMessage.error('您没有权限访问询盘登记表页面！');
  }
};

const goToDisplayFiles = () => {
  if (hasDisplayFilesManagePermission.value) {
    router.push('/display-files');
  } else {
    ElMessage.error('您没有权限访问展示文件页面！');
  }
};

const goToMachinePartsManagement = () => {
  if (hasMachinePartsManagePermission.value) {
    router.push('/machine-parts-management');
  } else {
    ElMessage.error('您没有权限访问机器零部件管理页面！');
  }
};

const goToPhotoManagement = () => {
  if (hasPhotoManagePermission.value) {
    router.push('/photo-management');
  } else {
    ElMessage.error('您没有权限访问照片管理页面！');
  }
};

const goToVideoManagement = () => {
  if (hasVideoManagePermission.value) {
    router.push('/video-management');
  } else {
    ElMessage.error('您没有权限访问视频管理页面！');
  }
};

const goToOrderStatus = () => {
  if (hasOrderStatusManagePermission.value) {
    router.push('/order-status');
  } else {
    ElMessage.error('您没有权限访问订单状态管理页面！');
  }
};

const goToOrderProgress = () => {
  if (hasOrderProgressManagePermission.value) {
    router.push('/order-progress');
  } else {
    ElMessage.error('您没有权限访问订单进度管理页面！');
  }
};

// 退出登录
const logout = () => {
  localStorage.removeItem('oa_token');
  clearUserPermissions(); // 清空权限缓存
  hasToken.value = false;
  ElMessage.success('已退出登录');
  router.push('/login');
};
</script>

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
  position: absolute;
  right: 20px;
  color: rgb(255, 255, 255);
  background-color: rgba(82, 177, 255, 0.1);
  font-size: 14px;
  border: rgba(0, 0, 0, 0.2) solid 1px;
}
.logout-btn:hover {
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

  /* 移动端样式优化 */
  .header h1 {
    font-size: 18px;
  }
  .logout-btn {
    font-size: 12px;
    right: 10px;
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
    padding: 0 10px;
  }
  .header h1 {
    font-size: 16px;
  }
  .el-menu-item {
    height: 45px !important;
    line-height: 45px !important;
    font-size: 13px !important;
  }
}
</style>