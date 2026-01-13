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
            <el-menu-item index="1" @click="goToPunch">
              <el-icon><CreditCard /></el-icon>
              <span>NFC打卡</span>
            </el-menu-item>
            <el-menu-item index="2" @click="goToOrder" v-if="hasToken">
              <el-icon><Document /></el-icon>
              <span>订单管理</span>
            </el-menu-item>
            <el-menu-item index="3" @click="goToPunchRecords" v-if="hasToken">
              <el-icon><Clock /></el-icon>
              <span>打卡记录</span>
            </el-menu-item>
            <el-menu-item index="4" @click="goToEmployeeManagement" v-if="hasToken">
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
import { CreditCard, Document, User, Clock, SwitchButton } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// 路由实例
const router = useRouter();
// 应用标题
const appTitle = ref(import.meta.env.VITE_APP_TITLE);
// 当前激活的菜单
const activeMenu = ref('1');
// 是否已登录（存在token）
const hasToken = ref(!!localStorage.getItem('oa_token'));

// 页面挂载时检查登录状态
onMounted(() => {
  hasToken.value = !!localStorage.getItem('oa_token');
});

// 跳转NFC打卡（实际通过NFC贴纸触发，此处仅为入口展示）
const goToPunch = () => {
  if (!hasToken.value) {
    ElMessage.warning('无需登录，直接使用NFC贴纸打卡');
    return;
  }
  ElMessage.info('请使用手机NFC贴纸靠近打卡区域');
};

// 跳转订单管理（需登录）
const goToOrder = () => {
  router.push('/order');
};

// 跳转打卡记录页面（需登录）
const goToPunchRecords = () => {
  router.push('/punch-records');
};

// 跳转员工管理页面（需登录）
const goToEmployeeManagement = () => {
  router.push('/employee-management');
};

// 跳转设备管理页面（需登录）
const goToDeviceManagement = () => {
  router.push('/device-management');
};

// 跳转登录页
const goToLogin = () => {
  router.push('/login');
};

// 退出登录
const logout = () => {
  // 清除本地存储的token
  localStorage.removeItem('oa_token');
  // 更新登录状态
  hasToken.value = false;
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