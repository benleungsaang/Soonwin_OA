<template>
  <div class="attendance-json-export-container">
    <!-- 公共头部 -->
    <CommonHeader title="考勤数据JSON导出" />

    <el-card class="export-card">
      <template #header>
        <div class="card-header">
          <span>考勤数据JSON导出</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px" style="max-width: 600px;">
        <el-form-item label="选择年份">
          <el-date-picker
            v-model="form.year"
            type="year"
            placeholder="选择年份"
            format="YYYY"
            value-format="YYYY"
          />
        </el-form-item>

        <el-form-item label="选择月份">
          <el-date-picker
            v-model="form.month"
            type="month"
            placeholder="选择月份"
            format="YYYY-MM"
            value-format="MM"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="exportJson" :loading="exportLoading">
            <el-icon style="margin-right: 5px;"><Download /></el-icon> 导出JSON
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Download } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';

// 表单数据
const form = ref({
  year: new Date().getFullYear().toString(),
  month: (new Date().getMonth() + 1).toString().padStart(2, '0')
});

// 导出状态
const exportLoading = ref(false);

// 导出JSON数据
const exportJson = async () => {
  if (!form.value.year || !form.value.month) {
    ElMessage.warning('请选择年份和月份');
    return;
  }

  exportLoading.value = true;
  try {
    // 直接使用fetch来处理blob响应
    const token = localStorage.getItem('oa_token');
    const params = new URLSearchParams({
      year: form.value.year,
      month: form.value.month
    });

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/attendance/export-json?${params}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });

    if (!response.ok) {
      throw new Error(`导出失败: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // 如果API返回的是包含code/msg/data结构的响应
    if (data.code === 200 && data.data) {
      // 将数据转换为JSON字符串
      const jsonData = JSON.stringify(data.data, null, 2);

      // 创建Blob对象
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const fileName = `考勤数据_${form.value.year}-${form.value.month}.json`;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      ElMessage.success('JSON数据导出成功');
    } else {
      throw new Error(data.msg || '导出失败');
    }
  } catch (error) {
    console.error('导出JSON数据失败:', error);
    ElMessage.error('导出JSON数据失败');
  } finally {
    exportLoading.value = false;
  }
};
</script>

<style scoped>
.attendance-json-export-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.export-card {
  margin-top: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
</style>