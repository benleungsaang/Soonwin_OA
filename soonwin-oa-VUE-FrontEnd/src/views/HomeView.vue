<template>
  <div class="home-container">
    <el-container style="height: 100vh;">
      <el-header class="header">
        <h1>{{ appTitle }}</h1>
      </el-header>
      <el-main class="main">
        <el-card shadow="hover" class="card">
          <!-- 替换 el-title 为 el-page-header -->
          <el-page-header content="SoonWin OA系统" />
          <el-divider></el-divider>
          <el-menu :default-active="activeMenu" class="menu">
            <el-menu-item index="1" @click="goToOrder" v-if="hasToken && isCurrentUserAdmin">
              <el-icon><Document /></el-icon>
              <span>订单管理</span>
            </el-menu-item>
            <el-menu-item index="6" @click="goToOrderInspection" v-if="hasToken">
              <el-icon><Finished /></el-icon>
              <span>订单验收</span>
            </el-menu-item>
            <el-menu-item index="4" @click="goToExpenseManagement" v-if="hasToken && isCurrentUserAdmin">
              <el-icon><Money /></el-icon>
              <span>运营费用</span>
            </el-menu-item>
            <el-menu-item index="2" @click="goToPunchRecords" v-if="hasToken && isCurrentUserAdmin">
              <el-icon><Clock /></el-icon>
              <span>打卡记录</span>
            </el-menu-item>
            <el-menu-item index="3" @click="goToEmployeeManagement" v-if="hasToken && isCurrentUserAdmin">
              <el-icon><User /></el-icon>
              <span>员工管理</span>
            </el-menu-item>
            <el-menu-item index="5" @click="goToLogin" v-if="!hasToken">
              <el-icon><User /></el-icon>
              <span>登录</span>
            </el-menu-item>
            <el-menu-item index="6" @click="logout" v-if="hasToken">
              <el-icon><SwitchButton /></el-icon>
              <span>退出登录</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { CreditCard, Document, User, Clock, SwitchButton, Money, Finished } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// 路由实例
const router = useRouter();
// 应用标题
const appTitle = ref(import.meta.env.VITE_APP_TITLE);
// 当前激活的菜单
const activeMenu = ref('1');
// 是否已登录（存在token）
const hasToken = ref(!!localStorage.getItem('oa_token'));
// 当前用户是否为管理员
const isCurrentUserAdmin = ref(false);

// 页面挂载时检查登录状态和用户角色
onMounted(() => {
  hasToken.value = !!localStorage.getItem('oa_token');
  if (hasToken.value) {
    // 从token中获取用户信息以确定角色
    try {
      const token = localStorage.getItem('oa_token');
      if (token) {
        // 解码JWT token获取用户角色信息
        const payload = JSON.parse(atob(token.split('.')[1]));
        isCurrentUserAdmin.value = payload.user_role === 'admin';
      }
    } catch (error) {
      console.error('解析用户信息失败:', error);
      isCurrentUserAdmin.value = false;
    }
  }
});

// 跳转NFC打卡（实际通过NFC贴纸触发，此处仅为入口展示） - 已删除
// const goToPunch = () => {
//   if (!hasToken.value) {
//     ElMessage.warning('无需登录，直接使用NFC贴纸打卡');
//     return;
//   }
//   ElMessage.info('请使用手机NFC贴纸靠近打卡区域');
// };

// 跳转订单管理（需登录）
const goToOrder = () => {
  router.push('/order');
};

// 跳转打卡记录页面（需登录）
const goToPunchRecords = () => {
  router.push('/punch-records');
};

// 跳转员工管理页面（仅管理员可见）
const goToEmployeeManagement = () => {
  if (!isCurrentUserAdmin.value) {
    ElMessage.error('您没有权限访问员工管理页面！');
    return;
  }
  router.push('/employee-management');
};

// 跳转费用管理页面（仅管理员可见）
const goToExpenseManagement = () => {
  if (!isCurrentUserAdmin.value) {
    ElMessage.error('您没有权限访问费用管理页面！');
    return;
  }
  router.push('/expense-management');
};

// 跳转设备管理页面（需登录）
const goToDeviceManagement = () => {
  router.push('/device-management');
};

// 跳转登录页
const goToLogin = () => {
  router.push('/login');
};

// 跳转登录页
const goToOrderInspection = () => {
  router.push('/order-inspection');
};

// 退出登录
const logout = () => {
  // 清除本地存储的token
  localStorage.removeItem('oa_token');
  // 更新登录状态
  hasToken.value = false;
  isCurrentUserAdmin.value = false;
  // 提示用户
  ElMessage.success('已退出登录');
  // 跳转到登录页
  router.push('/login');
};
</script>

<style scoped>
.home-container {
  width: 100%;
  height: 100%;
}

.header {
  background-color: #1989fa;
  color: white;
  text-align: center;
  line-height: 60px;
}

.main {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.card {
  width: 400px;
  padding: 20px;
}

.menu {
  margin-top: 20px;
}

.el-menu-item {
  height: 60px;
  line-height: 60px;
  font-size: 16px;
}
</style>