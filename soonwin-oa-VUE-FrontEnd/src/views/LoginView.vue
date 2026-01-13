<template>
  <div class="login-container">
    <el-card shadow="hover" class="login-card">
      <h2 class="login-title">TOTP动态码登录</h2>
      <el-divider></el-divider>
      
      <!-- 登录表单 -->
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="80px" v-if="!showBindForm">
        <el-form-item label="员工工号" prop="empId">
          <el-input 
            v-model="loginForm.empId" 
            placeholder="请输入工号" 
            @keyup.enter="focusTotpCode"
            ref="empIdInputRef"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="动态验证码" prop="totpCode">
          <el-input 
            v-model="loginForm.totpCode" 
            placeholder="请输入6位动态码" 
            type="number"
            @keyup.enter="handleLogin"
            ref="totpCodeInputRef"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" class="login-btn" :loading="isLoading">登录</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 绑定表单 -->
      <div v-else>
        <el-form :model="bindForm" :rules="bindRules" ref="bindFormRef" label-width="100px">
          <el-form-item label="员工ID" prop="empId">
            <el-input v-model="bindForm.empId" placeholder="请输入员工ID" @blur="fetchTotpUri"></el-input>
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="bindForm.name" placeholder="员工姓名" disabled></el-input>
          </el-form-item>
          <el-form-item v-if="totpUri">
            <div class="qr-container">
              <p>请使用手机验证器APP扫描下方二维码进行绑定：</p>
              <div class="qrcode-place">
                <canvas ref="qrCodeRef"></canvas>
              </div>
            </div>
          </el-form-item>
          <el-form-item label="验证码" prop="verificationCode">
            <el-input v-model="bindForm.verificationCode" placeholder="请输入验证器中的6位验证码" type="number"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="verifyAndBind" :loading="isBinding">验证并绑定</el-button>
            <el-button @click="showBindForm = false">返回登录</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 绑定选项 -->
      <div class="bind-option" v-if="!showBindForm">
        <el-divider>或</el-divider>
        <p class="bind-text" @click="showBindForm = true">没有账号？点击这里绑定验证器</p>
      </div>
    </el-card>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { FormInstance, FormRules } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { LoginResponse } from '@/types';

// 引入二维码生成库
import QRCode from 'qrcode';

// 路由实例
const router = useRouter();
// 表单引用
const loginFormRef = ref<FormInstance | null>(null);
const bindFormRef = ref<FormInstance | null>(null);
// 输入框引用
const empIdInputRef = ref<any>(null);
const totpCodeInputRef = ref<any>(null);
// 加载状态
const isLoading = ref(false);
const isBinding = ref(false);
// 显示绑定表单
const showBindForm = ref(false);
// 二维码元素引用
const qrCodeRef = ref<HTMLCanvasElement | null>(null);

// 登录表单数据
const loginForm = reactive({
  empId: '',
  totpCode: '',
});

// 绑定表单数据
const bindForm = reactive({
  empId: '',
  name: '',
  verificationCode: '',
});

// TOTP URI
const totpUri = ref('');

// 表单校验规则
const loginRules = reactive<FormRules>({
  empId: [
    { required: true, message: '请输入员工工号', trigger: 'blur' },
    { min: 3, max: 20, message: '工号长度为3-20位', trigger: 'blur' },
  ],
  totpCode: [
    { required: true, message: '请输入动态验证码', trigger: 'blur' },
    { len: 6, message: '验证码长度为6位', trigger: 'blur' },
  ],
});

const bindRules = reactive<FormRules>({
  empId: [
    { required: true, message: '请输入员工ID', trigger: 'blur' },
  ],
  verificationCode: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码长度为6位', trigger: 'blur' },
  ],
});

// 跳转到验证码输入框
const focusTotpCode = () => {
  // 校验工号输入
  if (!loginFormRef.value) return;
  
  loginFormRef.value.validateField('empId', (errorMessage) => {
    if (!errorMessage) {
      // 工号验证通过，将焦点切换到验证码输入框
      setTimeout(() => {
        if (totpCodeInputRef.value) {
          totpCodeInputRef.value.focus();
        }
      }, 100); // 添加短暂延迟确保DOM更新
    }
  });
};

// 处理登录逻辑
const handleLogin = async () => {
  // 表单校验
  if (!loginFormRef.value) return;
  try {
    await loginFormRef.value.validate();
    isLoading.value = true;

    // 调用登录接口
    const res: any = await request.post<LoginResponse>('/api/totp/login', {
      emp_id: loginForm.empId,
      totp_code: loginForm.totpCode,
    });

    // 检查响应结构并提取token
    let token, empId, name;
    if (res && res.token) {
      // 如果res直接包含token（axios拦截器已解包）
      token = res.token;
      empId = res.emp_id || res.empId;
      name = res.name || res.name;
    } else {
      // 如果res是完整响应（不太可能，但作为后备）
      token = res?.data?.token;
      empId = res?.data?.emp_id || res?.data?.empId;
      name = res?.data?.name || res?.data?.name;
    }

    if (!token) {
      throw new Error('登录响应中未包含有效token');
    }

    // 存储token
    localStorage.setItem('oa_token', token);
    ElMessage.success('登录成功！');

    // 跳转首页
    router.push('/');
  } catch (error: any) {
    console.error('登录失败：', error);
    ElMessage.error(error.message || '登录失败');
  } finally {
    isLoading.value = false;
  }
};

// 获取TOTP URI
const fetchTotpUri = async () => {
  if (!bindForm.empId) return;
  
  try {
    // request.post 工具已经自动处理了响应，返回的是 res.data 部分
    const res: any = await request.post('/api/totp-qr', { emp_id: bindForm.empId });
    console.log('TOTP QR API response:', res); // 调试日志
    
    // 检查是否是完整的响应格式还是已经解包的数据
    let totpData;
    if (res && res.data && typeof res.data === 'object' && res.data.totp_uri) {
      // 如果res.data包含实际的TOTP数据，说明是完整响应格式
      totpData = res.data;
    } else if (res && res.totp_uri) {
      // 如果res直接包含TOTP数据，说明已经解包
      totpData = res;
    } else {
      throw new Error('服务器响应格式错误，缺少必要的TOTP数据');
    }
    
    totpUri.value = totpData.totp_uri || '';
    bindForm.name = totpData.name || '';
    
    if (!totpUri.value) {
      throw new Error('获取TOTP配置失败：服务器未返回有效的URI');
    }
    
    console.log('Generated TOTP URI:', totpUri.value); // 调试日志
    
    // 使用 nextTick 确保 DOM 更新完成
    await nextTick();
    
    // 检查二维码canvas元素是否存在
    if (!qrCodeRef.value) {
      console.error('二维码canvas元素未找到');
      ElMessage.error('二维码canvas元素未找到');
      return;
    }
    
    // 直接使用canvas元素生成二维码
    try {
      await QRCode.toCanvas(qrCodeRef.value, totpUri.value, { 
        width: 200,
        height: 200,
        margin: 2,
        errorCorrectionLevel: 'M'  // 设置错误纠正级别
      });
      console.log('二维码生成成功');
    } catch (error) {
      console.error('生成二维码失败:', error);
      ElMessage.error('生成二维码失败: ' + (error as Error).message);
    }
  } catch (error: any) {
    console.error('获取TOTP URI失败:', error);
    ElMessage.error(error.message || '获取TOTP配置失败，请确认员工ID是否正确');
    totpUri.value = '';
  }
};

// 验证并绑定TOTP
const verifyAndBind = async () => {
  try {
    await bindFormRef.value?.validate();
    isBinding.value = true;
    
    await request.post('/api/verify-totp', {
      emp_id: bindForm.empId,
      totp_code: bindForm.verificationCode
    });
    
    ElMessage.success('TOTP验证成功！您的账户已更新为待审批状态，请联系管理员进行审批');
    showBindForm.value = false;
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      ElMessage.error('TOTP验证失败');
    }
  } finally {
    isBinding.value = false;
  }
};

// 组件挂载时检查是否需要安装qrcode库
onMounted(() => {
  // 确保qrcode库已安装
  try {
    if (typeof QRCode === 'undefined') {
      console.error('qrcode库未正确导入');
    }
  } catch (e) {
    console.error('检查qrcode库时出错:', e);
  }
});
</script>
<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.login-card {
  width: 400px;
  padding: 30px;
}

.login-title {
  text-align: center;
  color: #1989fa;
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
}

.bind-option {
  text-align: center;
  margin-top: 20px;
}

.bind-text {
  color: #1989fa;
  cursor: pointer;
  font-size: 14px;
  text-decoration: underline;
}

.bind-text:hover {
  opacity: 0.8;
}

.qr-container {
  text-align: center;
}

.qr-container p {
  margin-bottom: 15px;
}

.qrcode-place {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 10px auto;
  min-height: 220px; /* 确保容器有足够的高度 */
  min-width: 220px;  /* 确保容器有足够的宽度 */
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  background-color: #fff;
}
</style>