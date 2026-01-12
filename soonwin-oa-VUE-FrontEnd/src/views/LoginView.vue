<template>
  <div class="login-container">
    <el-card shadow="hover" class="login-card">
      <el-title level="2" class="login-title">TOTP动态码登录</el-title>
      <el-divider></el-divider>
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="80px">
        <el-form-item label="员工工号" prop="empId">
          <el-input v-model="loginForm.empId" placeholder="请输入工号" prefix="el-icon-user"></el-input>
        </el-form-item>
        <el-form-item label="动态验证码" prop="totpCode">
          <el-input v-model="loginForm.totpCode" placeholder="请输入6位动态码" prefix="el-icon-lock" type="number"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" class="login-btn" :loading="isLoading">登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { FormInstance, FormRules } from 'element-plus';
import request from '@/utils/request';
import { LoginResponse } from '@/types';

// 路由实例
const router = useRouter();
// 表单引用
const loginFormRef = ref<FormInstance | null>(null);
// 加载状态
const isLoading = ref(false);

// 登录表单数据
const loginForm = reactive({
  empId: '',
  totpCode: '',
});

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

// 处理登录逻辑
const handleLogin = async () => {
  // 表单校验
  if (!loginFormRef.value) return;
  try {
    await loginFormRef.value.validate();
    isLoading.value = true;

    // 调用登录接口
    const res = await request.post<LoginResponse>('/totp/login', {
      emp_id: loginForm.empId,
      totp_code: loginForm.totpCode,
    });

    // 存储token
    localStorage.setItem('oa_token', res.token);
    ElMessage.success('登录成功！');

    // 跳转首页
    router.push('/');
  } catch (error) {
    console.error('登录失败：', error);
  } finally {
    isLoading.value = false;
  }
};
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
</style>