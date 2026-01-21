<template>
  <div class="punch-container">
    <el-card shadow="hover" class="punch-card">
      <el-page-header content="员工打卡" @back="goBackHome" />
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

// 打卡处理函数
const handlePunch = async () => {
  if (punchLoading.value) return;

  punchLoading.value = true;
  isPunchDisabled.value = true;

  try {
    const deviceId = getDeviceId();
    const empId = userInfo.value.emp_id;

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
      // 首次打卡成功，需要保存设备ID
      saveDeviceId(response.device_id);
      ElMessage.success(`首次打卡成功！设备ID已保存: ${response.device_id.substring(0, 8)}...`);
    } else if (response.status === 'device_change_required') {
      // 设备ID变化，询问用户是否申请更换设备
      const confirmChange = await ElMessageBox.confirm(
        '检测到设备ID发生变化，是否申请更换设备？',
        '设备变更提示',
        {
          confirmButtonText: '申请更换',
          cancelButtonText: '暂不更换',
          type: 'warning',
        }
      ).catch(() => {
        // 用户取消操作
        ElMessage.info('已取消设备更换申请');
        return null;
      });

      if (confirmChange === true) {
        // 用户同意申请更换设备
        const deviceChangeResponse = await request.post('/api/request-device-change', {
          emp_id: empId,
          new_device_id: deviceId
        });

        if (deviceChangeResponse.request_id) {
          ElMessage.success('设备更换申请已提交，请等待管理员审批');
        }
      }
    } else if (response.status === 'pending_approval') {
      // 设备更换申请已提交
      ElMessage.success('设备更换申请已提交，请等待管理员审批');
    } else {
      ElMessage.success('打卡成功！');
    }

    // 如果是成功打卡（非待审批状态），则跳转到成功页面
    if (!response.status || response.status !== 'pending_approval') {
      router.push({
        name: 'punchSuccess',
        query: {
          name: response.name,
          emp_id: response.emp_id,
          punch_type: response.punch_type,
          punch_time: response.punch_time
        }
      });
    }
  } catch (error: any) {
    console.error('打卡失败:', error);
    if (error.response?.data?.msg?.includes('设备ID未提供')) {
      // 首次打卡，没有设备ID，直接发送员工ID让后端生成设备ID
      const response = await request.post('/api/device-clock-in', {
        emp_id: userInfo.value.emp_id
      }, {
        headers: {
          'X-Device-ID': null
        }
      });

      if (response.device_id) {
        saveDeviceId(response.device_id);
        ElMessage.success('首次打卡成功！设备ID已保存');
        router.push({
          name: 'punchSuccess',
          query: {
            name: response.name,
            emp_id: response.emp_id,
            punch_type: response.punch_type,
            punch_time: response.punch_time
          }
        });
      }
    } else if (error.response?.data?.msg?.includes('需要绑定设备')) {
      // 首次打卡，需要绑定设备
      const response = await request.post('/api/device-clock-in', {
        emp_id: userInfo.value.emp_id
      }, {
        headers: {
          'X-Device-ID': null
        }
      });

      if (response.device_id) {
        saveDeviceId(response.device_id);
        ElMessage.success('首次打卡成功！设备ID已保存');
        router.push({
          name: 'punchSuccess',
          query: {
            name: response.name,
            emp_id: response.emp_id,
            punch_type: response.punch_type,
            punch_time: response.punch_time
          }
        });
      }
    } else if (error.response?.data?.msg?.includes('设备ID变化')) {
      // 设备ID变化，询问用户是否申请更换设备
      const confirmChange = await ElMessageBox.confirm(
        '检测到设备ID发生变化，是否申请更换设备？',
        '设备变更提示',
        {
          confirmButtonText: '申请更换',
          cancelButtonText: '暂不更换',
          type: 'warning',
        }
      ).catch(() => {
        // 用户取消操作
        ElMessage.info('已取消设备更换申请');
        return null;
      });

      if (confirmChange === true) {
        // 用户同意申请更换设备
        const deviceChangeResponse = await request.post('/api/request-device-change', {
          emp_id: userInfo.value.emp_id,
          new_device_id: getDeviceId()  // 使用当前设备ID作为新设备ID
        });

        if (deviceChangeResponse.request_id) {
          ElMessage.success('设备更换申请已提交，请等待管理员审批');
        }
      }
    } else {
      ElMessage.error(error.response?.data?.msg || '打卡失败');
    }
  } finally {
    punchLoading.value = false;
    isPunchDisabled.value = false;
  }
};

// 返回首页
const goBackHome = () => {
  router.push('/');
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