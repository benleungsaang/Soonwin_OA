<template>
  <div class="common-header">
    <el-page-header :content="title" @back="goBack">
      <template #extra>
        <span v-if="isAdmin && appVersion" class="version-badge" :title="'点击查看版本记录'" @click="showVersionDialog = true">v{{ appVersion }}</span>
        <el-button v-if="isAdmin" type="warning" @click="handleRestart" :loading="restarting">
          <el-icon><RefreshRight /></el-icon><span class="btn-text">重启服务</span>
        </el-button>
        <el-button @click="showQrCodeDialog = true">
          <el-icon><Grid /></el-icon><span class="btn-text">二维码</span>
        </el-button>
        <el-button @click="logout">
          <el-icon><SwitchButton /></el-icon><span class="btn-text">用户 {{ currentUserEmpId && currentUserName ? currentUserEmpId + ' [ ' + currentUserName + ' ]' : (currentUserEmpId ? currentUserEmpId : '登录') }} 登出</span>
        </el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>

    <el-dialog v-model="showQrCodeDialog" title="网站二维码" width="300px" align-center>
      <div style="display: flex; flex-direction: column; align-items: center;">
        <canvas ref="qrCodeCanvasRef"></canvas>
        <p style="margin-top: 10px; color: #666; font-size: 13px;">扫描二维码访问网站首页</p>
      </div>
    </el-dialog>

    <!-- 版本记录弹窗 -->
    <VersionHistoryDialog v-model:visible="showVersionDialog" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, provide, onUnmounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { SwitchButton, Grid, RefreshRight } from '@element-plus/icons-vue';
import QRCode from 'qrcode';
import VersionHistoryDialog from './VersionHistoryDialog.vue';
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

// 二维码弹窗
const showQrCodeDialog = ref(false);
const qrCodeCanvasRef = ref<HTMLCanvasElement | null>(null);

// 管理员判断
const isAdmin = computed(() => currentUserRole.value === 'admin');
// 服务版本号（后端 /api/version 返回，重启按钮左侧展示）
const appVersion = ref('');
// 版本记录弹窗
const showVersionDialog = ref(false);
async function loadAppVersion() {
  try {
    const res = await fetch('/api/version');
    const data = await res.json();
    if (data?.version) appVersion.value = data.version;
  } catch { /* ignore */ }
}
// 重启服务
const restarting = ref(false);
async function handleRestart() {
  try {
    await ElMessageBox.confirm('确定要重启服务器 OA 服务吗？', '确认重启', { type: 'warning' });
    restarting.value = true;
    const res = await fetch('/api/admin/restart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: 'SoonwinOA_Restart_Key_2026' }),
    });
    const data = await res.json();
    if (data.success) ElMessage.success(data.msg);
    else ElMessage.error(data.msg);
  } catch { /* cancelled */ }
  finally { restarting.value = false }
}

watch(showQrCodeDialog, async (newVal) => {
  if (newVal) {
    await nextTick();
    if (qrCodeCanvasRef.value) {
      const rootUrl = window.location.origin + '/';
      await QRCode.toCanvas(qrCodeCanvasRef.value, rootUrl, { width: 200, margin: 2 });
    }
  }
});

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
  loadAppVersion();

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
.el-icon {
  margin-right: 5px;
  vertical-align: middle;
  display: inline-flex;
  align-items: center;
}
.el-button {
  display: inline-flex !important;
  align-items: center !important;
}
/* 版本号徽标（重启服务按钮左侧）：低饱和浅蓝底 + 蓝色字，灰底上清晰可见 */
.version-badge {
  display: inline-flex;
  align-items: center;
  margin-right: 8px;
  padding: 4px 10px;
  background: rgba(59, 130, 246, 0.08);
  color: #3b82f6;
  font-size: 12px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 6px;
  white-space: nowrap;
  vertical-align: middle;
  cursor: pointer;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .common-header {
    padding: 0 10px;
  }
  .common-header :deep(.el-page-header__extra) {
    display: flex;
    gap: 4px;
  }
  .common-header :deep(.el-page-header__extra) .el-button {
    padding: 5px 8px;
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .common-header :deep(.el-page-header__content) {
    font-size: 13px;
  }
  .common-header :deep(.el-page-header__extra) .el-button {
    padding: 4px 6px;
    font-size: 11px;
  }
  .btn-text {
    display: none;
  }
  .el-icon {
    margin-right: 0;
  }
  .version-badge {
    display: none;
  }
}
</style>