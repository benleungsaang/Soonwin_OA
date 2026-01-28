<template>
  <div class="punch-container">
    <el-card shadow="hover" class="punch-card">
      <CommonHeader title="员工打卡" />
      <el-divider></el-divider>

      <div class="punch-content">
        <div class="user-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="员工姓名">{{ userInfo.name }}</el-descriptions-item>
            <el-descriptions-item label="员工工号">{{ userInfo.emp_id }}</el-descriptions-item>
            <el-descriptions-item label="部门">{{ userInfo.dept }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="punch-time">
          <h3>当前时间</h3>
          <p class="current-time">{{ currentTime }}</p>
        </div>

        <div class="punch-actions">
          <el-button
            type="primary"
            size="large"
            :loading="punchLoading"
            @click="handlePunch"
            :disabled="isPunchDisabled"
            class="punch-btn"
          >
            <el-icon><Clock /></el-icon>
            {{ punchButtonText }}
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Clock } from '@element-plus/icons-vue';
import request from '@/utils/request';
import CommonHeader from '@/components/CommonHeader.vue';

// 路由实例
const router = useRouter();

// 用户信息
const userInfo = ref({
  name: '',
  emp_id: '',
  dept: ''
});

// 当前时间
const currentTime = ref('');
const punchLoading = ref(false);
const isPunchDisabled = ref(false);

// 打卡按钮文本
const punchButtonText = ref('开始打卡');

// 定时器ID
let timeInterval: NodeJS.Timeout | null = null;

// 从本地存储获取设备ID
const getDeviceId = () => {
  return localStorage.getItem('auth_device_id') || null;
};

// 保存设备ID到本地存储和Cookie
const saveDeviceId = (deviceId: string) => {
  localStorage.setItem('auth_device_id', deviceId);
  // 设置Cookie，有效期1年
  document.cookie = `auth_device_id=${deviceId}; path=/; max-age=${365 * 24 * 60 * 60}`;
};

// 获取用户信息
const loadUserInfo = async () => {
  try {
    const token = localStorage.getItem('oa_token');
    if (!token) {
      ElMessage.error('请先登录');
      router.push('/login');
      return;
    }

    // 从token中解析用户信息
    const payload = JSON.parse(atob(token.split('.')[1]));
    const empId = payload.emp_id;

    // 从后端获取员工详细信息
    const employeeInfo = await request.get(`/api/employee-basic-info/${empId}`);
    userInfo.value = {
      name: employeeInfo.name,
      emp_id: employeeInfo.emp_id,
      dept: employeeInfo.dept
    };
  } catch (error) {
    console.error('获取用户信息失败:', error);
    ElMessage.error('获取用户信息失败');
  }
};

// 检测是否为移动设备
const isMobileDevice = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  const mobileKeywords = ['mobile', 'android', 'iphone'];
  return mobileKeywords.some(keyword => userAgent.includes(keyword));
};

// 打卡处理函数
const handlePunch = async () => {
  if (!isMobileDevice()) {
    ElMessage.warning('请使用个人手机进行打卡');
    return;
  }

  if (punchLoading.value) return;

  punchLoading.value = true;
  isPunchDisabled.value = true;

  // 提取通用函数：处理首次打卡逻辑
  const handleFirstPunch = async (empId: string) => {
    try {
      const response = await request.post('/api/device-clock-in', { emp_id: empId }, {
        headers: { 'X-Device-ID': null }
      });
      if (response.device_id) {
        saveDeviceId(response.device_id);
        ElMessage.success(`首次打卡成功！设备ID已保存: ${response.device_id.substring(0, 8)}...`);
        // 通用跳转逻辑
        jumpToPunchSuccess(response);
      }
      return response;
    } catch (error) {
      console.error('首次打卡处理失败:', error);
      ElMessage.error('首次打卡绑定设备失败，请稍后重试');
      return null;
    }
  };

  // 提取通用函数：处理设备更换申请
  const handleDeviceChange = async (empId: string, newDeviceId: string | null) => {
    if (!newDeviceId) {
      ElMessage.error('设备ID未获取到，请稍后重试');
      return null;
    }
    try {
      const deviceChangeResponse = await request.post('/api/request-device-change', {
        emp_id: empId,
        new_device_id: newDeviceId
      });
      if (deviceChangeResponse?.request_id) {
        ElMessage.success('设备更换申请已提交，请等待管理员审批');
      }
      return deviceChangeResponse;
    } catch (error) {
      console.error('发送设备更换申请失败:', error);
      ElMessage.error('设备更换申请发送失败，请稍后重试');
      return null;
    }
  };

  // 提取通用函数：打卡成功跳转
  const jumpToPunchSuccess = (response: any) => {
    router.push({
      name: 'punchSuccess',
      query: {
        name: response.name,
        emp_id: response.emp_id,
        punch_type: response.punch_type,
        punch_time: response.punch_time
      }
    });
  };

  try {
    const deviceId = getDeviceId();
    const empId = userInfo.value?.emp_id; // 增加可选链，避免取值报错

    // 校验员工ID是否存在
    if (!empId) {
      ElMessage.error('员工信息未加载，请刷新页面重试');
      return;
    }

    // 调用后端打卡API
    const response = await request.post('/api/device-clock-in', {
      emp_id: empId,
      device_id: deviceId
    }, {
      headers: {
        'X-Device-ID': deviceId
      }
    });

    if (response.device_id) {
      // 首次打卡成功
      saveDeviceId(response.device_id);
      ElMessage.success(`首次打卡成功！设备ID已保存: ${response.device_id.substring(0, 8)}...`);
      jumpToPunchSuccess(response);
    } else if (response.status === 'device_change_required') {
      // 设备ID变化，询问是否更换
      try {
        await ElMessageBox.confirm(
          '检测到设备ID发生变化，是否申请更换设备？',
          '设备变更提示',
          {
            confirmButtonText: '申请更换',
            cancelButtonText: '暂不更换',
            type: 'warning',
          }
        );
        // 用户点击确认（无需判断===true，confirm成功则执行此处）
        await handleDeviceChange(empId, deviceId);
      } catch (error) {
        // 用户取消操作
        ElMessage.info('已取消设备更换申请');
      }
    } else if (response.status === 'pending_approval') {
      ElMessage.success('设备更换申请已提交，请等待管理员审批');
    } else {
      ElMessage.success('打卡成功！');
      jumpToPunchSuccess(response);
    }
  } catch (error: any) {
    console.error('打卡失败:', error);
    const errorMsg = error.response?.data?.msg || '';
    const empId = userInfo.value?.emp_id;

    if (!empId) {
      ElMessage.error('员工信息未加载，请刷新页面重试');
      return;
    }

    // 首次打卡相关错误：合并重复逻辑
    if (errorMsg.includes('设备ID未提供') || errorMsg.includes('需要绑定设备')) {
      await handleFirstPunch(empId);
    }
    // 设备ID变化相关错误
    else if (errorMsg.includes('设备ID变化') || error.response?.data?.data?.status === 'device_change_required') {
      try {
        await ElMessageBox.confirm(
          '检测到设备ID发生变化，是否申请更换设备？',
          '设备变更提示',
          {
            confirmButtonText: '申请更换',
            cancelButtonText: '暂不更换',
            type: 'warning',
          }
        );
        // 用户确认更换：调用通用函数
        await handleDeviceChange(empId, getDeviceId());
      } catch (cancelError) {
        ElMessage.info('已取消设备更换申请');
      }
    } else {
      ElMessage.error(errorMsg || '打卡失败');
    }
  } finally {
    punchLoading.value = false;
    isPunchDisabled.value = false;
  }
};

// 更新时间
const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleString('zh-CN');
};

// 页面挂载时初始化
onMounted(async () => {
  await loadUserInfo();
  updateTime();

  // 每秒更新一次时间
  timeInterval = setInterval(updateTime, 1000);
});

// 页面卸载时清除定时器
onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval);
  }
});
</script>

<style scoped>
.punch-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.punch-card {
  width: 450px;
  padding: 30px;
}

.punch-content {
  margin-top: 20px;
}

.user-info {
  margin-bottom: 30px;
}

.punch-time {
  text-align: center;
  margin-bottom: 30px;
}

.current-time {
  font-size: 24px;
  font-weight: bold;
  color: #1989fa;
  margin: 10px 0;
}

.punch-actions {
  text-align: center;
}

.punch-btn {
  width: 100%;
  height: 60px;
  font-size: 18px;
}
</style>