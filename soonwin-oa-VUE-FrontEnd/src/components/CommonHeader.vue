<template>
  <div class="common-header">
    <el-page-header :content="title" @back="goBack">
      <template #extra>
        <el-button @click="logout">
          <el-icon><SwitchButton /></el-icon>用户 {{ currentUserEmpId && currentUserName ? currentUserEmpId + ' [ ' + currentUserName + ' ]' : (currentUserEmpId ? currentUserEmpId : '登录') }} 登出
        </el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ref, onMounted, provide, onUnmounted } from 'vue';
import { SwitchButton } from '@element-plus/icons-vue';
import {
  getCurrentUserEmpId,
  getCurrentUserName,
  getCurrentUserRole
} from '@/utils/authUtils';
import {
  getCurrentUserInfo,
  updateCurrentUserInfo,
  clearCurrentUserInfo
} from '@/utils/userInfo';

interface Props {
  title: string;
}

defineProps<Props>();

const route = useRoute();
const router = useRouter();

// 用户信息
const currentUserEmpId = ref<string | null>(null);
const currentUserName = ref<string | null>(null);
const currentUserRole = ref<string | null>(null);

// 提供用户信息，方便子组件使用
provide('currentUserEmpId', currentUserEmpId);
provide('currentUserName', currentUserName);
provide('currentUserRole', currentUserRole);

// 返回上一级路由（基于路由层级，非历史记录）
const goBack = () => {
  // 获取当前路由匹配的层级列表
  const matchedRoutes = route.matched;
  if (matchedRoutes.length >= 2) {
    // 取倒数第二个层级（上一级）的路径
    const parentPath = matchedRoutes[matchedRoutes.length - 2].path;
    // 跳转到父级路由
    router.push({ path: parentPath });
  } else {
    // 无父级时的兜底（比如首页），可跳转到默认页
    router.push({ path: '/' });
  }
};

// 获取用户信息
const getUserInfo = () => {
  updateCurrentUserInfo();
  const userInfo = getCurrentUserInfo();
  currentUserEmpId.value = userInfo?.empId || null;
  // 从JWT token直接获取用户名，确保与HomeView一致
  const token = localStorage.getItem('oa_token');
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      currentUserName.value = payload.name || payload.user_name || null;
      currentUserRole.value = payload.user_role || userInfo?.role || null;
    } catch (error) {
      console.error('解析用户信息失败:', error);
      // 降级处理：使用从userInfo获取的值
      currentUserName.value = userInfo?.name || null;
      currentUserRole.value = userInfo?.role || null;
    }
  } else {
    currentUserName.value = userInfo?.name || null;
    currentUserRole.value = userInfo?.role || null;
  }
};

// 监听localStorage变化，以便在其他标签页登录/登出时更新信息
const handleStorageChange = (e: StorageEvent) => {
  if (e.key === 'oa_token') {
    getUserInfo();
  }
};

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

    // 清除本地存储的token
    localStorage.removeItem('oa_token');

    // 清空用户信息
    clearCurrentUserInfo();
    currentUserEmpId.value = null;
    currentUserName.value = null;
    currentUserRole.value = null;

    // 提示用户
    ElMessage.success('已退出登录');
    // 跳转到登录页
    router.push('/login');
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('退出登录失败：', error);
    }
  }
};

// 组件挂载时获取用户信息
onMounted(() => {
  getUserInfo();

  // 监听storage事件，以便在其他标签页登录/登出时更新信息
  window.addEventListener('storage', handleStorageChange);
});

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange);
});
</script>

<style scoped>
.common-header {
  padding: 0 20px;
}
.el-icon{
  margin-right: 5px;
}

</style>