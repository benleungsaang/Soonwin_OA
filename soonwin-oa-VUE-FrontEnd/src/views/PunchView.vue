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

// ===================== 类型定义 =====================
/** 员工信息类型 */
interface UserInfo {
  name: string;
  emp_id: string;
  dept: string;
}

/** 打卡响应数据类型 */
interface PunchResponse {
  code: number;
  msg: string;
  data: {
    emp_id: string;
    name: string;
    punch_type: string;
    punch_time: string;
    device_id?: string;
    status?: 'device_change_required' | 'pending_approval';
  };
}

/** 设备更换申请响应类型 */
interface DeviceChangeResponse {
  code: number;
  msg: string;
  data: {
    request_id: string;
    emp_id: string;
    old_device_id?: string;
    new_device_id?: string;
    request_time: string;
    status: 'pending';
  };
}

// ===================== 常量定义 =====================
const MOBILE_KEYWORDS = ['mobile', 'android', 'iphone', 'ipad', 'tablet', 'phone', 'ios', 'blackberry', 'windows phone', 'opera mini', 'mobile safari', 'mobile web', 'android mobile', 'iphone os'];
const DEVICE_ID_STORAGE_KEY = 'auth_device_id';
const TOKEN_STORAGE_KEY = 'oa_token';
const COOKIE_MAX_AGE = 365 * 24 * 60 * 60; // 1年有效期

// ===================== 状态管理 =====================
// 路由实例
const router = useRouter();

// 用户信息
const userInfo = ref<UserInfo>({
  name: '',
  emp_id: '',
  dept: ''
});

// 当前时间
const currentTime = ref('');
const punchLoading = ref(false);
const isPunchDisabled = ref(false);
const punchButtonText = ref('开始打卡');

// 定时器ID
let timeInterval: NodeJS.Timeout | null = null;

// ===================== 本地存储工具函数 =====================
/** 获取本地存储的设备ID */
const getDeviceId = (): string | null => {
  return localStorage.getItem(DEVICE_ID_STORAGE_KEY) || null;
};

/** 保存设备ID到本地存储和Cookie */
const saveDeviceId = (deviceId: string): void => {
  localStorage.setItem(DEVICE_ID_STORAGE_KEY, deviceId);
  // 设置Cookie，有效期1年
  document.cookie = `${DEVICE_ID_STORAGE_KEY}=${deviceId}; path=/; max-age=${COOKIE_MAX_AGE}`;
};

// ===================== 时间处理函数 =====================
/** 更新当前显示时间 */
const updateTime = (): void => {
  const now = new Date();
  currentTime.value = now.toLocaleString('zh-CN');
};

// ===================== 设备检测函数 =====================
/** 检测是否为移动设备 */
const isMobileDevice = (): boolean => {
  const userAgent = navigator.userAgent.toLowerCase();
  return MOBILE_KEYWORDS.some(keyword => userAgent.includes(keyword));
};

// ===================== 用户信息加载函数 =====================
/** 加载用户基本信息 */
const loadUserInfo = async (): Promise<void> => {
  try {
    // 1. 验证token
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      ElMessage.error('请先登录');
      router.push('/login');
      return;
    }

    // 2. 解析token获取员工ID
    const payload = JSON.parse(atob(token.split('.')[1]));
    const empId = payload.emp_id;

    // 3. 从后端获取员工信息（request已自动解包data）
    const employeeInfo = await request.get<UserInfo>(`/api/employee-basic-info/${empId}`);
    userInfo.value = employeeInfo;
  } catch (error: any) {
    console.error('获取用户信息失败:', error);
    ElMessage.error(error.response?.data?.msg || '获取用户信息失败');
  }
};

// ===================== 打卡核心逻辑函数 =====================
/** 处理首次打卡（无设备ID） */
const handleFirstPunch = async (empId: string): Promise<PunchResponse['data'] | null> => {
  try {
    // request自动解包data，直接返回data层数据
    const response = await request.post<PunchResponse['data']>('/api/device-clock-in',
      { emp_id: empId },
      { headers: { 'X-Device-ID': null } }
    );

    if (response.device_id) {
      saveDeviceId(response.device_id);
      ElMessage.success(`首次打卡成功！设备ID已保存: ${response.device_id.substring(0, 8)}...`);
      jumpToPunchSuccess(response);
    }
    return response;
  } catch (error: any) {
    console.error('首次打卡处理失败:', error);
    ElMessage.error(error.response?.data?.msg || '首次打卡绑定设备失败，请稍后重试');
    return null;
  }
};

/** 处理设备更换申请 */
const handleDeviceChange = async (empId: string, newDeviceId: string | null): Promise<DeviceChangeResponse['data'] | null> => {
  if (!newDeviceId) {
    ElMessage.error('设备ID未获取到，请稍后重试');
    return null;
  }

  try {
    const response = await request.post<DeviceChangeResponse['data']>('/api/request-device-change', {
      emp_id: empId,
      new_device_id: newDeviceId
    });

    if (response?.request_id) {
      ElMessage.success('设备更换申请已提交，请等待管理员审批');
    }
    return response;
  } catch (error: any) {
    console.error('发送设备更换申请失败:', error);
    ElMessage.error(error.response?.data?.msg || '设备更换申请发送失败，请稍后重试');
    return null;
  }
};

/** 打卡成功跳转页面 */
const jumpToPunchSuccess = (response: PunchResponse['data']): void => {
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

/** 处理设备变更确认弹窗 */
const confirmDeviceChange = async (empId: string): Promise<void> => {
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
    // 用户确认更换设备
    await handleDeviceChange(empId, getDeviceId());
  } catch (cancelError) {
    // 用户取消操作
    ElMessage.info('已取消设备更换申请');
  }
};

/** 打卡主处理函数 */
const handlePunch = async (): Promise<void> => {
  // 1. 移动设备校验（强制）
  if (!isMobileDevice()) {
    ElMessage.error('请使用个人手机进行打卡');
    return;
  }

  // 2. 防止重复点击
  if (punchLoading.value) return;

  // 3. 设置加载状态
  punchLoading.value = true;
  isPunchDisabled.value = true;

  try {
    // 4. 基础参数校验
    const deviceId = getDeviceId();
    const empId = userInfo.value.emp_id;

    if (!empId) {
      ElMessage.error('员工信息未加载，请刷新页面重试');
      return;
    }

    // 5. 调用打卡接口（request自动解包data）
    const response = await request.post<PunchResponse['data']>('/api/device-clock-in', {
      emp_id: empId,
      device_id: deviceId
    }, {
      headers: {
        'X-Device-ID': deviceId
      }
    });

    // 6. 处理不同响应场景
    if (response.device_id) {
      // 首次打卡成功
      saveDeviceId(response.device_id);
      ElMessage.success(`首次打卡成功！设备ID已保存: ${response.device_id.substring(0, 8)}...`);
      jumpToPunchSuccess(response);
    } else if (response.status === 'device_change_required') {
      // 设备ID变化，询问是否更换
      await confirmDeviceChange(empId);
    } else if (response.status === 'pending_approval') {
      // 设备更换申请已提交
      ElMessage.success('设备更换申请已提交，请等待管理员审批');
    } else {
      // 正常打卡成功
      ElMessage.success('打卡成功！');
      jumpToPunchSuccess(response);
    }
  } catch (error: any) {
    // 7. 异常处理逻辑
    console.error('打卡失败:', error);
    const empId = userInfo.value.emp_id;

    if (!empId) {
      ElMessage.error('员工信息未加载，请刷新页面重试');
      return;
    }

    // 网络超时/连接失败：request.ts已统一显示"网络连接超时或信号不稳定…"提示
    if (!error.response) {
      return;
    }

    // 8. 服务器返回错误，根据错误信息执行对应恢复流程（request.ts已显示具体错误消息）
    const errorMsg = error.response?.data?.msg || '';
    const errorStatus = error.response?.data?.data?.status;

    if (errorMsg.includes('设备ID未提供') || errorMsg.includes('需要绑定设备')) {
      // 首次打卡绑定设备
      await handleFirstPunch(empId);
    } else if (errorMsg.includes('设备ID变化') || errorStatus === 'device_change_required') {
      // 设备ID变化确认
      await confirmDeviceChange(empId);
    }
  } finally {
    // 9. 重置加载状态
    punchLoading.value = false;
    isPunchDisabled.value = false;
  }
};

// ===================== 生命周期函数 =====================
/** 页面挂载初始化 */
onMounted(async (): Promise<void> => {
  // 加载用户信息
  await loadUserInfo();
  // 初始化时间显示
  updateTime();
  // 每秒更新时间
  timeInterval = setInterval(updateTime, 1000);
});

/** 页面卸载清理 */
onUnmounted((): void => {
  if (timeInterval) {
    clearInterval(timeInterval);
    timeInterval = null;
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