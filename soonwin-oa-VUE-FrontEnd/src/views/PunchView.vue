<template>
  <div class="punch-page">
    <main class="punch-shell">
      <header class="punch-header">
        <button class="back-button" type="button" aria-label="返回首页" @click="goHome">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="m15 18-6-6 6-6" />
          </svg>
        </button>
        <h1>员工打卡</h1>
        <span aria-hidden="true"></span>
      </header>

      <div class="punch-content">
        <section class="identity" aria-label="打卡人员">
          <div class="avatar" :class="{ 'is-success': confirmedRecord }">
            <img
              v-if="userInfo.emp_id && !avatarLoadError"
              :src="avatarUrl"
              alt="员工头像"
              @error="avatarLoadError = true"
            />
            <div v-else class="avatar-fallback" aria-hidden="true">
              {{ userInfo.emp_id ? userInfo.emp_id.slice(0, 1).toUpperCase() : '?' }}
            </div>
            <div class="success-overlay" aria-hidden="true">
              <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="m4.5 12 5 5L20 6.5" />
              </svg>
            </div>
          </div>
          <h2 class="employee-id">{{ userInfo.emp_id || ' ' }}</h2>
          <div class="status-tag" :class="{ 'is-success': confirmedRecord }" role="status" aria-live="polite">
            {{ statusText }}
          </div>
        </section>

        <section class="time-card" aria-label="打卡时间">
          <div class="time-label">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7v5l3.5 2" />
            </svg>
            <span>{{ confirmedRecord ? '本次打卡时间' : '当前时间' }}</span>
          </div>
          <div class="time-value">{{ displayTime }}</div>
          <div class="date-value">{{ displayDate }}</div>
        </section>

        <div class="action-area">
          <button
            class="primary-button"
            :class="{ secondary: confirmedRecord }"
            type="button"
            :disabled="punchLoading || isPunchDisabled"
            :aria-busy="punchLoading"
            @click="handlePrimaryAction"
          >
            {{ primaryButtonText }}
          </button>
          <div class="hint" aria-live="polite">{{ hintText }}</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import request from '@/utils/request';
import { getOrCreatePunchDeviceId } from '@/utils/punchDeviceId';
import { classifyPunchResponse, isDeviceBindingRequiredHttpError } from '@/utils/punchResponse';
import type { ConfirmedPunchRecord } from '@/utils/punchResponse';

// ===================== 类型定义 =====================
/** 员工信息类型 */
interface UserInfo {
  name: string;
  emp_id: string;
  dept: string;
}

// ===================== 常量定义 =====================
const MOBILE_KEYWORDS = ['mobile', 'android', 'iphone', 'ipad', 'tablet', 'phone', 'ios', 'blackberry', 'windows phone', 'opera mini', 'mobile safari', 'mobile web', 'android mobile', 'iphone os'];
const TOKEN_STORAGE_KEY = 'oa_token';
const WEEKDAYS = '日一二三四五六';

// ===================== 状态管理 =====================
const router = useRouter();
const userInfo = ref<UserInfo>({ name: '', emp_id: '', dept: '' });
const displayTime = ref('');
const displayDate = ref('');
const punchLoading = ref(false);
const isPunchDisabled = ref(false);
const confirmedRecord = ref<ConfirmedPunchRecord | null>(null);
const avatarLoadError = ref(false);
let timeInterval: ReturnType<typeof setInterval> | null = null;

const avatarUrl = computed(() => `/api/posts/avatar/${encodeURIComponent(userInfo.value.emp_id)}`);
const statusText = computed(() => {
  if (!confirmedRecord.value) return '准备开始打卡';
  if (confirmedRecord.value.status === 'already_punched') {
    return `本时段已打卡 · ${confirmedRecord.value.punch_type}`;
  }
  return `打卡成功 · ${confirmedRecord.value.punch_type}`;
});
const primaryButtonText = computed(() => {
  if (confirmedRecord.value) return '返回首页';
  return punchLoading.value ? '正在打卡…' : '开始打卡 →';
});
const hintText = computed(() => {
  if (confirmedRecord.value?.status === 'already_punched') return '本时段打卡记录已确认';
  if (confirmedRecord.value) return '本次打卡已记录';
  return '点击按钮记录当前打卡时间';
});

// ===================== 时间处理函数 =====================
const padTime = (value: number): string => String(value).padStart(2, '0');

const formatDate = (date: Date): string => {
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 · 星期${WEEKDAYS[date.getDay()]}`;
};

/** 打卡前显示本地时钟；已确认后保留后端记录时间，不再更新。 */
const updateTime = (): void => {
  if (confirmedRecord.value) return;
  const now = new Date();
  displayTime.value = `${padTime(now.getHours())}:${padTime(now.getMinutes())}:${padTime(now.getSeconds())}`;
  displayDate.value = formatDate(now);
};

/** 后端返回本地日期时间字符串，按其字段格式化，避免浏览器解析格式差异。 */
const showConfirmedTime = (punchTime: string): void => {
  const match = punchTime.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/);
  if (match) {
    const [, year, month, day, hour, minute, second] = match;
    displayTime.value = `${hour}:${minute}:${second}`;
    displayDate.value = formatDate(new Date(Number(year), Number(month) - 1, Number(day)));
    return;
  }

  const parsed = new Date(punchTime);
  if (Number.isFinite(parsed.getTime())) {
    displayTime.value = `${padTime(parsed.getHours())}:${padTime(parsed.getMinutes())}:${padTime(parsed.getSeconds())}`;
    displayDate.value = formatDate(parsed);
  } else {
    displayTime.value = punchTime;
    displayDate.value = '';
  }
};

const showConfirmedRecord = (record: ConfirmedPunchRecord): void => {
  confirmedRecord.value = record;
  showConfirmedTime(record.punch_time);
  if (timeInterval) {
    clearInterval(timeInterval);
    timeInterval = null;
  }
};

const goHome = (): void => {
  router.push('/');
};

const handlePrimaryAction = (): void => {
  if (confirmedRecord.value) {
    goHome();
    return;
  }
  void handlePunch();
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
    showConfirmedRecord(outcome.record);
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
.punch-page {
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  justify-content: center;
  background: #f2f5f9;
  color: #202938;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.punch-page,
.punch-page * {
  box-sizing: border-box;
}

.punch-shell {
  width: 100%;
  max-width: 480px;
  min-width: 0;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.punch-header {
  height: 68px;
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 48px 1fr 48px;
  align-items: center;
  padding: 0 18px;
  border-bottom: 1px solid #f0f2f6;
}

.punch-header h1 {
  margin: 0;
  text-align: center;
  font-size: 17px;
  font-weight: 650;
}

.back-button {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: #253041;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.back-button:hover {
  background: #f4f7fa;
}

.back-button:focus-visible,
.primary-button:focus-visible {
  outline: 3px solid rgba(64, 158, 255, 0.35);
  outline-offset: 2px;
}

.punch-content {
  width: 100%;
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 28px calc(50px + env(safe-area-inset-bottom, 0px));
}

.identity {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: clamp(52px, 9vh, 92px);
}

.avatar {
  position: relative;
  width: 104px;
  height: 104px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 5px solid #f5f9ff;
  border-radius: 50%;
  background: #eaf3ff;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: #409eff;
  font-size: 32px;
  font-weight: 650;
}

.success-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(234, 249, 240, 0.78);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
}

.success-overlay svg {
  color: #1ab26a;
  filter: drop-shadow(0 1px 1px rgba(255, 255, 255, 0.6));
}

.avatar.is-success .success-overlay {
  opacity: 1;
}

.employee-id {
  max-width: 100%;
  overflow-wrap: anywhere;
  margin: 17px 0 11px;
  font-size: 25px;
  font-weight: 680;
  line-height: 1.2;
}

.status-tag {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #f3f6fa;
  padding: 6px 16px;
  color: #8593a5;
  font-size: 13px;
  text-align: center;
}

.status-tag.is-success {
  background: #eaf8f0;
  color: #139e5b;
  font-weight: 600;
}

.time-card {
  width: 100%;
  margin-top: clamp(44px, 8vh, 78px);
  padding: 26px 14px 27px;
  border: 1px solid #e7edf5;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 12px 35px rgba(35, 72, 115, 0.055);
  text-align: center;
}

.time-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #8795a9;
  font-size: 13px;
}

.time-label svg {
  width: 15px;
  height: 15px;
  flex: 0 0 15px;
}

.time-value {
  min-height: 1.12em;
  margin: 13px 0 12px;
  font-size: clamp(43px, 10vw, 58px);
  font-weight: 680;
  letter-spacing: -1.5px;
  line-height: 1.12;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.date-value {
  min-height: 1.2em;
  color: #8795a9;
  font-size: 13px;
}

.action-area {
  width: 100%;
  margin-top: clamp(44px, 9vh, 84px);
}

.primary-button {
  width: 100%;
  height: 60px;
  border: 0;
  border-radius: 16px;
  background: #409eff;
  box-shadow: 0 9px 20px rgba(64, 158, 255, 0.16);
  color: #fff;
  font: inherit;
  font-size: 17px;
  font-weight: 650;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.primary-button:hover:not(:disabled) {
  background: #318eec;
}

.primary-button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.primary-button.secondary {
  background: #eaf3ff;
  box-shadow: none;
  color: #2788e8;
}

.primary-button.secondary:hover:not(:disabled) {
  background: #deecff;
}

.hint {
  min-height: 18px;
  margin-top: 16px;
  color: #a0aaba;
  font-size: 12px;
  text-align: center;
}

@media (min-width: 600px) {
  .punch-page {
    padding: 20px;
  }

  .punch-shell {
    min-height: 800px;
    border-radius: 25px;
    box-shadow: 0 15px 40px rgba(34, 54, 80, 0.05);
    overflow: hidden;
  }
}

@media (max-height: 690px) {
  .identity {
    padding-top: 28px;
  }

  .time-card {
    margin-top: 28px;
  }

  .action-area {
    margin-top: 32px;
  }

  .punch-content {
    padding-bottom: calc(25px + env(safe-area-inset-bottom, 0px));
  }
}

@media (prefers-reduced-motion: reduce) {
  .success-overlay {
    transition: none;
  }
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
