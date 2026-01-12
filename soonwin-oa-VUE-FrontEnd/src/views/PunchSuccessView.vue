<template>
  <div class="punch-success-container">
    <el-card shadow="hover" class="success-card">
      <div class="success-icon">
        <el-icon class="icon"><Check /></el-icon>
      </div>
      <el-title level="2" class="title">打卡成功！</el-title>
      <el-divider></el-divider>
      <div class="info-list">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="员工姓名">{{ name }}</el-descriptions-item>
          <el-descriptions-item label="员工工号">{{ empId }}</el-descriptions-item>
          <el-descriptions-item label="打卡类型">{{ punchType }}</el-descriptions-item>
          <el-descriptions-item label="打卡时间">{{ punchTime }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <el-button type="primary" @click="goBackHome" class="back-btn">返回首页</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Check } from '@element-plus/icons-vue';

// 路由实例
const router = useRouter();
const route = useRoute();

// 接收URL参数（打卡成功后后端跳转时携带）
const name = ref('');
const empId = ref('');
const punchType = ref('');
const punchTime = ref('');

// 页面挂载时解析参数
onMounted(() => {
  const query = route.query;
  name.value = query.name as string || '未知用户';
  empId.value = query.emp_id as string || '未知工号';
  punchType.value = query.punch_type as string || '未知类型';
  punchTime.value = query.punch_time as string || new Date().toLocaleString();
});

// 返回首页
const goBackHome = () => {
  router.push('/');
};
</script>

<style scoped>
.punch-success-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.success-card {
  width: 450px;
  padding: 30px;
  text-align: center;
}

.success-icon {
  margin-bottom: 20px;
}

.icon {
  font-size: 60px;
  color: #38b000;
}

.title {
  color: #1989fa;
  margin-bottom: 20px;
}

.info-list {
  margin: 20px 0;
}

.back-btn {
  margin-top: 20px;
  width: 100%;
}
</style>