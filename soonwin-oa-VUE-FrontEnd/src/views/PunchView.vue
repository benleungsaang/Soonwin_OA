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
import { getOrCreatePunchDeviceId } from '@/utils/punchDeviceId';
import { classifyPunchResponse, ConfirmedPunchRecord, isDeviceBindingRequiredHttpError } from '@/utils/punchResponse';
import CommonHeader from '@/components/CommonHeader.vue';

// ===================== 类型定义 =====================
/** 员工信息类型 */
interface UserInfo {
  name: string;
  emp_id: string;
  dept: string;
}

/** 设备更换申请响应类型 */

// ===================== 常量定义 =====================
const MOBILE_KEYWORDS = ['mobile', 'android', 'iphone', 'ipad', 'tablet', 'phone', 'ios', 'blackberry', 'windows phone', 'opera mini', 'mobile safari', 'mobile web', 'android mobile', 'iphone os'];
const TOKEN_STORAGE_KEY = 'oa_token';

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
/** 未授权设备必须由管理员二维码现场授权。 */
const confirmDeviceChange = async (_empId: string): Promise<void> => {
  ElMessage.warning('当前设备尚未授权，请联系管理员现场生成绑定二维码后使用微信扫码申请。');
};

const showDeviceBindingRequired = async (): Promise<void> => {
  await ElMessageBox.alert(
    '当前设备未进行绑定，请联系管理员操作绑定。',
    '当前设备未绑定',
    {
      confirmButtonText: '我知道了',
      center: true,
      closeOnClickModal: false,
      customClass: 'device-binding-alert',
      showClose: false
    }
  );
};

/** 打卡成功跳转页面 */
const jumpToPunchSuccess = (response: ConfirmedPunchRecord): void => {
  router.push({
    name: 'punchSuccess',
    query: {
      record_id: response.record_id,
      name: response.name,
      emp_id: response.emp_id,
      punch_type: response.punch_type,
      punch_time: response.punch_time
    }
  });
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
    const deviceId = getOrCreatePunchDeviceId();
    const empId = userInfo.value.emp_id;

    if (!empId) {
      ElMessage.error('员工信息未加载，请刷新页面重试');
      return;
    }

    // 5. 调用打卡接口（request自动解包data）
    const response = await request.post<unknown>('/api/device-clock-in', {
      emp_id: empId,
      device_id: deviceId
    }, {
      headers: {
        'X-Device-ID': deviceId
      }
    });

    // 6. 只有后端回传已持久化记录的 ID 和完整字段才显示成功。
    const outcome = classifyPunchResponse(response, empId);
    if (outcome.kind === 'binding-required') {
      await confirmDeviceChange(empId);
      return;
    } else if (outcome.kind === 'pending-approval') {
      ElMessage.success('设备更换申请已提交，请等待管理员审批');
      return;
    } else if (outcome.kind !== 'confirmed') {
      ElMessage.error('服务器未确认有效的打卡记录，未显示打卡成功');
      return;
    }

    if (outcome.record.status === 'already_punched') {
      ElMessage.success(outcome.record.msg || '已存在有效的打卡记录');
    } else {
      ElMessage.success('打卡成功！');
    }
    jumpToPunchSuccess(outcome.record);
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

    if (isDeviceBindingRequiredHttpError(error)) {
      await showDeviceBindingRequired();
      return;
    }

    // 8. 服务器返回错误，根据错误信息执行对应恢复流程（request.ts已显示具体错误消息）
    const errorMsg = error.response?.data?.msg || '';
    const errorStatus = error.response?.data?.data?.status;

    // 请求拦截器已显示后端的二维码重新绑定指引，禁止再按成功响应处理。
    if (errorStatus === 'device_binding_required' || errorStatus === 'device_change_required') {
      return;
    }

    if (errorMsg.includes('设备ID变化') || errorMsg.includes('设备ID缺失') || errorStatus === 'device_change_required') {
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

:global(.device-binding-alert.el-message-box) {
  width: 420px !important;
  max-width: calc(100vw - 32px);
  box-sizing: border-box;
}

:global(.device-binding-alert .el-message-box__message p) {
  line-height: 1.6;
  overflow-wrap: anywhere;
}
</style>
