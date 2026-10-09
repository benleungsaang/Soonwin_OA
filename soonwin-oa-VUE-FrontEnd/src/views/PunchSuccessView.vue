<template>
  <div class="punch-success-container">
    <el-card v-if="hasValidPunchResult" shadow="hover" class="success-card">
      <div class="success-icon">
        <el-icon class="icon"><Check /></el-icon>
      </div>
      <h2 class="title">打卡成功！</h2>
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
import { ElMessage } from 'element-plus';
import { Check } from '@element-plus/icons-vue';

// 路由实例
const router = useRouter();
const route = useRoute();

// 接收URL参数（打卡成功后后端跳转时携带）
const name = ref('');
const empId = ref('');
const punchType = ref('');
const punchTime = ref('');
const hasValidPunchResult = ref(false);

// 页面挂载时解析参数
onMounted(() => {
  const query = route.query;
  const recordId = typeof query.record_id === 'string' ? Number(query.record_id) : NaN;
  const queryName = typeof query.name === 'string' ? query.name.trim() : '';
  const queryEmpId = typeof query.emp_id === 'string' ? query.emp_id.trim() : '';
  const queryPunchType = typeof query.punch_type === 'string' ? query.punch_type : '';
  const queryPunchTime = typeof query.punch_time === 'string' ? query.punch_time : '';
  const validPunchTypes = ['上班打卡', '下班打卡', '非打卡时间打卡'];

  if (
    !Number.isSafeInteger(recordId) || recordId <= 0 || !queryName || !queryEmpId || !validPunchTypes.includes(queryPunchType) ||
    !queryPunchTime || !Number.isFinite(Date.parse(queryPunchTime))
  ) {
    ElMessage.error('未收到有效的打卡记录确认，请重新打卡');
    router.replace({ name: 'punch' });
    return;
  }

  name.value = queryName;
  empId.value = queryEmpId;
  punchType.value = queryPunchType;
  punchTime.value = queryPunchTime;
  hasValidPunchResult.value = true;
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
