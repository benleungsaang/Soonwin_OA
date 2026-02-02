<template>
  <div class="log-management-container">
    <CommonHeader title="日志管理" />
    
    <!-- 日志类型选择 -->
    <el-card shadow="hover" class="filter-card">
      <el-select
        v-model="selectedLogType"
        placeholder="选择日志类型"
        style="width: 200px;"
        @change="switchLogType"
      >
        <el-option label="询盘日志" value="inquiry" />
        <el-option label="视频日志" value="video" />
        <el-option label="图片日志" value="image" />
        <el-option label="人员日志" value="user" />
      </el-select>
    </el-card>

    <!-- 通用日志组件（非模态框形式） -->
    <div class="log-content">
      <CommonLogDialog
        :visible="true"
        :log-type="selectedLogType"
        :show-statistics="true"
        :handle-jump="handleJumpToDetail"
        @close="() => {}"
        style="position: relative; top: 0; left: 0; width: 100%;"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import CommonHeader from '@/components/CommonHeader.vue';
import CommonLogDialog from '@/components/CommonLogDialog.vue';

const router = useRouter();
const selectedLogType = ref('inquiry');

// 切换日志类型
const switchLogType = () => {
  // 可以在这里添加额外的逻辑
};

// 跳转到详情页面
const handleJumpToDetail = (id: number) => {
  switch (selectedLogType.value) {
    case 'inquiry':
      router.push(`/inquiries/${id}`);
      break;
    case 'video':
      router.push(`/videos/${id}`);
      break;
    case 'image':
      router.push(`/images/${id}`);
      break;
    case 'user':
      router.push(`/users/${id}`);
      break;
    default:
      ElMessage.info('暂不支持该类型的详情跳转');
  }
};
</script>

<style scoped>
.log-management-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.filter-card {
  margin-bottom: 20px;
  padding: 15px;
}

.log-content {
  width: 100%;
}

:deep(.el-dialog) {
  position: relative;
  top: 0 !important;
  margin: 0 !important;
  width: 100% !important;
}

:deep(.el-dialog__wrapper) {
  position: static !important;
  background-color: transparent !important;
}

:deep(.el-dialog__header) {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 15px 20px;
  border-top: 1px solid #ebeef5;
}
</style>