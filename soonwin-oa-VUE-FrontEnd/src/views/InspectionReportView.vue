<template>
  <div class="inspection-report-container">
    <div v-if="loading" class="loading">
      <el-skeleton :rows="10" animated />
    </div>
    <div v-else-if="reportData" class="report-content">
      <!-- 订单基础信息 -->
      <el-card class="report-card">
        <template #header>
          <div class="card-header">
            <span>订单验收报告 - 报告生成时间：{{ formatDate(reportData.inspection.update_time) }}</span>
          </div>
        </template>

        <div class="order-info">
          <h3>订单基础信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="合同编号">{{ reportData.inspection.contract_no }}</el-descriptions-item>
            <el-descriptions-item label="订单编号">{{ reportData.inspection.order_no }}</el-descriptions-item>
            <el-descriptions-item label="包装机单号">{{ reportData.inspection.machine_no }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ reportData.inspection.machine_name }}</el-descriptions-item>
            <el-descriptions-item label="机型">{{ reportData.inspection.machine_model }}</el-descriptions-item>
            <el-descriptions-item label="主机数量">{{ reportData.inspection.machine_count }}</el-descriptions-item>
            <el-descriptions-item label="下单时间">{{ formatDate(reportData.inspection.order_time) }}</el-descriptions-item>
            <el-descriptions-item label="出货时间">{{ formatDate(reportData.inspection.ship_time) }}</el-descriptions-item>
            <el-descriptions-item label="验收状态">{{ formatStatus(reportData.inspection.inspection_status) }}</el-descriptions-item>
            <el-descriptions-item label="验收进度">{{ reportData.inspection.inspection_progress }}%</el-descriptions-item>
            <el-descriptions-item label="总检查项数">{{ reportData.summary.total_items }}</el-descriptions-item>
            <el-descriptions-item label="已完成检查项数">{{ reportData.summary.completed_items }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>

      <!-- 检查项详情 -->
      <el-card class="report-card">
        <template #header>
          <div class="card-header">
            <span>检查项详情</span>
          </div>
        </template>

        <div class="inspection-items">
          <div v-for="parentItem in reportData.items" :key="parentItem.id" class="inspection-group">
            <div class="parent-item">
              <div class="parent-title-container">
                <h3 class="parent-title">{{ parentItem.item_category }}</h3>
                    <div style="margin-bottom: 10px; margin-left: 20px; width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                      <div :style="{width: `${parentItem.progress}%`, height: '100%'}" style="background: #67c23a; border-radius: 4px;">
                      </div>
                    </div>
                    <span style="margin:0 0px 10px 10px; ">{{ parentItem.completed_children }}/{{ parentItem.total_children }}</span>
              </div>
              <div class="sub-items">
                <div
                  v-for="subItem in parentItem.children || []"
                  :key="subItem.id"
                  class="sub-item"
                >
                  <div class="sub-item-header">
                    <div class="sub-item-name">
                      <strong>{{ subItem.item_name }}</strong>
                    </div>
                    <div class="sub-item-result">
                      <el-tag
                        :type="getResultType(subItem.inspection_result)"
                        size="large"
                      >
                        {{ getResultText(subItem.inspection_result) }}
                      </el-tag>
                    </div>
                  </div>

                  <div class="sub-item-content">
                    <!-- 显示缺陷描述 -->
                    <div v-if="subItem.description" class="description-section">
                      <h4>缺陷描述</h4>
                      <p>{{ subItem.description }}</p>
                    </div>
                    <!-- 显示图片 -->
                    <div v-if="subItem.photo_path" class="photo-section">
                      <div class="photo-grid">
                        <img
                          v-for="(photo, index) in getPhotoPaths(subItem.photo_path)"
                          :key="index"
                          :src="getPhotoUrl(photo)"
                          :alt="`照片${index + 1}`"
                          class="photo-preview-static">
                      </div>
                    </div>

                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 显示没有父项的子项 -->
          <div v-for="standaloneItem in standaloneItems" :key="standaloneItem.id" class="standalone-item">
            <div class="sub-item">
              <div class="sub-item-header">
                <div class="sub-item-name">
                  <strong>{{ standaloneItem.item_name }}</strong>
                </div>
                <div class="sub-item-result">
                  <el-tag
                    :type="getResultType(standaloneItem.inspection_result)"
                    size="large"
                  >
                    {{ getResultText(standaloneItem.inspection_result) }}
                  </el-tag>
                </div>
              </div>

              <div class="sub-item-content">
                <!-- 显示图片 -->
                <div v-if="standaloneItem.photo_path" class="photo-section">
                  <div class="photo-grid">
                    <img
                      v-for="(photo, index) in getPhotoPaths(standaloneItem.photo_path)"
                      :key="index"
                      :src="getPhotoUrl(photo)"
                      :alt="`照片${index + 1}`"
                      class="photo-preview-static">
                  </div>
                </div>

                <!-- 显示缺陷描述 -->
                <div v-if="standaloneItem.description" class="description-section">
                  <h4>缺陷描述</h4>
                  <p>{{ standaloneItem.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 总结信息 -->
      <el-card class="report-card">
        <template #header>
          <div class="card-header">
            <span>验收总结</span>
          </div>
        </template>

        <div class="summary-info">
          <h3>验收总结</h3>
          <p><strong>验收状态：</strong>{{ formatStatus(reportData.summary.status) }}</p>
          <p><strong>总检查项数：</strong>{{ reportData.summary.total_items }}</p>
          <p><strong>已完成检查项数：</strong>{{ reportData.summary.completed_items }}</p>
          <p><strong>验收进度：</strong>{{ reportData.summary.progress }}%</p>
          <p><strong>报告生成时间：</strong>{{ formatDate(reportData.inspection.update_time) }}</p>
        </div>
      </el-card>
    </div>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="imagePreviewVisible"
      :show-close="true"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
      width="auto"
      top="5vh"
      class="image-preview-dialog"
    >
      <div style="text-align: center;">
        <img :src="previewImageUrl" style="max-width: 90vw; max-height: 80vh; object-fit: contain;" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import request from '@/utils/request';
import { ElMessage } from 'element-plus';

// 响应式数据
const reportData = ref<any>(null);
const loading = ref(true);
const imagePreviewVisible = ref(false);
const previewImageUrl = ref('');

// 路由
const route = useRoute();
const inspectionId = ref<number | null>(null);

// 计算属性：获取没有父项的子项
const standaloneItems = computed(() => {
  if (!reportData.value || !reportData.value.items) return [];
  return reportData.value.items.filter((item: any) => item.item_type === 'sub' && item.parent_id === null);
});

// 获取URL参数中的验收ID
onMounted(async () => {
  inspectionId.value = Number(route.params.inspectionId) || Number(route.query.inspectionId) || Number(route.query.id);
  if (!inspectionId.value) {
    ElMessage.error('未提供验收ID');
    loading.value = false;
    return;
  }

  await fetchReportData();
});

// 获取报告数据
const fetchReportData = async () => {
  try {
    loading.value = true;
    const response: any = await request.get(`/api/inspections/${inspectionId.value}/report`);
    reportData.value = response;
  } catch (error) {
    console.error('获取验收报告失败:', error);
    ElMessage.error('获取验收报告失败');
  } finally {
    loading.value = false;
  }
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

// 格式化状态
const formatStatus = (status: string) => {
  const statusMap: { [key: string]: string } = {
    'pending': '待验收',
    'in_progress': '验收中',
    'completed': '已完成'
  };
  return statusMap[status] || status;
};

// 获取检查结果类型
const getResultType = (result: string) => {
  const typeMap: { [key: string]: string } = {
    'normal': 'success',
    'defect': 'danger',
    'not_applicable': 'info',
    'pending': 'warning'
  };
  return typeMap[result] || 'info';
};

// 获取检查结果文本
const getResultText = (result: string) => {
  const textMap: { [key: string]: string } = {
    'normal': '正常',
    'defect': '不正常',
    'not_applicable': '没此项',
    'pending': '未检查'
  };
  return textMap[result] || result;
};

// 获取图片路径数组
const getPhotoPaths = (photoPath: string | null) => {
  if (!photoPath) return [];
  return photoPath.split(',').map(path => path.trim()).filter(path => path);
};

// 获取照片URL（处理相对路径）
const getPhotoUrl = (path: string) => {
  if (!path) return '';

  // 标准化路径分隔符
  const normalizedPath = path.replace(/\\/g, '/');

  // 如果路径已经是完整URL，则直接返回
  if (normalizedPath.startsWith('http://') || normalizedPath.startsWith('https://')) {
    return normalizedPath;
  }

  // 否则添加基础URL
  if (import.meta.env.MODE === 'development') {
    // 开发环境下，假设文件服务在后端服务器上
    return `http://192.168.30.70:5000/${normalizedPath}`;
  } else {
    return `${window.location.protocol}//${window.location.hostname}:5000/${normalizedPath}`;
  }
};

// 显示图片预览
const showImagePreview = (imageUrl: string) => {
  previewImageUrl.value = imageUrl;
  imagePreviewVisible.value = true;
};

// 获取当前日期时间
const getCurrentDateTime = () => {
  const now = new Date();
  return now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};
</script>

<style scoped>

/* 可编辑标题样式 */
.parent-title-container {
  display: inline-flex;
  align-items: center;
  flex: 1;
}


.inspection-report-container {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.report-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.order-info {
  padding: 20px 0;
}

.inspection-items {
  padding: 20px 0;
}

.inspection-group {
  margin-bottom: 30px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  background-color: white;
}

.parent-item {
  padding: 10px 0;
}

.parent-title {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 18px;
  font-weight: bold;
}

.parent-progress {
  margin-bottom: 20px;
}

.sub-items {
  padding-left: 20px;
}

.sub-item {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fafafa;
}

.sub-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.sub-item-name {
  font-weight: 500;
  font-size: 16px;
}

.sub-item-content {
  padding-top: 10px;
}

.photo-section {
  margin: 15px 0;
}

.photo-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.photo-item {
  cursor: pointer;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.3s;
}

.photo-item:hover {
  transform: scale(1.02);
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.photo-preview {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

.photo-preview-static {
  max-width: 1000px;
  height: auto;
  display: block;
  margin: 0 auto; /* 水平居中 */
  border-radius: 5px;
  border: 2px solid #dcdfe6;
  box-shadow: rgba(48, 49, 51, 0.1) 5px 5px 2px 0;
}

.description-section {
  margin-top: 10px;
  padding: 10px;
  background-color: #f4f4f5;
  border-radius: 4px;
}

.description-section h4 {
  margin: 0 0 5px 0;
  color: #606266;
  font-size: 14px;
}

.description-section p {
  margin: 0;
  color: #303133;
}

.standalone-item {
  margin: 20px 0;
}

.summary-info {
  padding: 20px 0;
}

.summary-info p {
  margin: 10px 0;
  line-height: 1.6;
}

.loading {
  padding: 40px;
  text-align: center;
}
</style>