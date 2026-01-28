<template>
  <div class="common-header">
    <el-page-header :content="title" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';

interface Props {
  title: string;
}

defineProps<Props>();

const router = useRouter();

// 返回上一页
const goBack = () => {
  router.go(-1);
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
</script>

<style scoped>
.common-header {
  padding: 0 20px;
}
</style>