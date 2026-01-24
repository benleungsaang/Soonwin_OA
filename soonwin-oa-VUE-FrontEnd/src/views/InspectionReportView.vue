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
          <el-descriptions :column="isMobile ? 1 : 2" border>
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
                <div class="parent-progress-container">
                  <div class="parent-progress-bar">
                    <div :style="{width: `${parentItem.progress}%`}" class="parent-progress-fill"></div>
                  </div>
                  <span class="parent-progress-text">{{ parentItem.completed_children }}/{{ parentItem.total_children }}</span>
                </div>
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
                        :size="isMobile ? 'default' : 'large'"
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
                          class="photo-preview-static"
                          @click="showImagePreview(getPhotoUrl(photo))">
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
                    :size="isMobile ? 'default' : 'large'"
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
                      class="photo-preview-static"
                      @click="showImagePreview(getPhotoUrl(photo))">
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
          <div class="summary-item">
            <span class="summary-label">验收状态：</span>
            <span class="summary-value">{{ formatStatus(reportData.summary.status) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">总检查项数：</span>
            <span class="summary-value">{{ reportData.summary.total_items }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">已完成检查项数：</span>
            <span class="summary-value">{{ reportData.summary.completed_items }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">验收进度：</span>
            <span class="summary-value">{{ reportData.summary.progress }}%</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">报告生成时间：</span>
            <span class="summary-value">{{ formatDate(reportData.inspection.update_time) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="imagePreviewVisible"
      :show-close="true"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
      :width="isMobile ? '90%' : '90%'"
      top="5vh"
      class="image-preview-dialog"
    >
      <div style="text-align: center;">
        <img :src="previewImageUrl" style="max-width: 100%; max-height: 80vh; object-fit: contain;" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import request from '@/utils/request';
import { ElMessage } from 'element-plus';

// 响应式数据
const reportData = ref<any>(null);
const loading = ref(true);
const imagePreviewVisible = ref(false);
const previewImageUrl = ref('');
const windowWidth = ref(window.innerWidth);

// 路由
const route = useRoute();
const inspectionId = ref<number | null>(null);

// 计算属性：判断是否为移动端
const isMobile = computed(() => {
  return windowWidth.value < 768;
});

// 计算属性：获取没有父项的子项
const standaloneItems = computed(() => {
  if (!reportData.value || !reportData.value.items) return [];
  return reportData.value.items.filter((item: any) => item.item_type === 'sub' && item.parent_id === null);
});

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

// 获取URL参数中的验收ID
onMounted(async () => {
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize);
  
  inspectionId.value = Number(route.params.inspectionId) || Number(route.query.inspectionId) || Number(route.query.id);
  if (!inspectionId.value) {
    ElMessage.error('未提供验收ID');
    loading.value = false;
    return;
  }

  await fetchReportData();
});

// 组件卸载前移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
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
    // 开发环境下，使用相对路径通过Vite代理访问后端5001
    return `/${normalizedPath}`;
  } else {
    // 生产环境下，使用配置的API基础URL或默认的5000端口
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:5000`;
    if (apiBaseUrl.startsWith('http')) {
      // 如果VITE_API_BASE_URL是完整URL，则直接使用
      return `${apiBaseUrl}/${normalizedPath}`;
    } else {
      // 否则构建完整URL
      return `${window.location.protocol}//${window.location.hostname}${apiBaseUrl}/${normalizedPath}`;
    }
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
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.parent-progress-container {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.parent-progress-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  min-width: 100px;
}

.parent-progress-fill {
  height: 100%;
  background: #67c23a;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.parent-progress-text {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
}

.inspection-report-container {
  padding: 10px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .inspection-report-container {
    padding: 20px;
  }
}

.report-card {
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .card-header {
    font-size: 18px;
  }
}

.order-info {
  padding: 15px 0;
}

.inspection-items {
  padding: 15px 0;
}

.inspection-group {
  margin-bottom: 20px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 15px;
  background-color: white;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .inspection-group {
    margin-bottom: 30px;
    padding: 20px;
  }
}

.parent-item {
  padding: 10px 0;
}

.parent-title {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 16px;
  font-weight: bold;
  word-break: break-word;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .parent-title {
    margin: 0 0 15px 0;
    font-size: 18px;
  }
}

.sub-items {
  padding-left: 10px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .sub-items {
    padding-left: 20px;
  }
}

.sub-item {
  margin-bottom: 15px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fafafa;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .sub-item {
    margin-bottom: 20px;
    padding: 15px;
  }
}

.sub-item-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .sub-item-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.sub-item-name {
  font-weight: 500;
  font-size: 14px;
  word-break: break-word;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .sub-item-name {
    font-size: 16px;
  }
}

.sub-item-content {
  padding-top: 10px;
}

.photo-section {
  margin: 10px 0;
}

.photo-grid {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
  margin-top: 10px;
}

.photo-preview-static {
  max-width: min(100%, 1000px);
  height: auto;
  display: block;
  margin: 0 auto;
  border-radius: 5px;
  border: 2px solid #dcdfe6;
  box-shadow: rgba(48, 49, 51, 0.1) 2px 2px 4px 0;
  cursor: pointer;
  transition: transform 0.2s;
}

.photo-preview-static:hover {
  transform: scale(1.02);
}

.description-section {
  margin-top: 10px;
  padding: 8px;
  background-color: #f4f4f5;
  border-radius: 4px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .description-section {
    padding: 10px;
  }
}

.description-section h4 {
  margin: 0 0 5px 0;
  color: #606266;
  font-size: 13px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .description-section h4 {
    font-size: 14px;
  }
}

.description-section p {
  margin: 0;
  color: #303133;
  font-size: 13px;
  line-height: 1.5;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .description-section p {
    font-size: 14px;
    line-height: 1.6;
  }
}

.standalone-item {
  margin: 15px 0;
}

.summary-info {
  padding: 15px 0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
  padding: 8px 0;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .summary-item {
    flex-direction: row;
    padding: 10px 0;
  }
}

.summary-label {
  font-weight: bold;
  color: #606266;
  margin-bottom: 2px;
  font-size: 14px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .summary-label {
    margin-bottom: 0;
    margin-right: 10px;
  }
}

.summary-value {
  color: #303133;
  font-size: 14px;
  word-break: break-word;
}

.loading {
  padding: 40px;
  text-align: center;
}

/* 针对移动端的特殊样式 */
@media (max-width: 767px) {
  .el-descriptions__label {
    display: block;
    font-weight: bold;
    margin-bottom: 2px;
  }
  
  .el-descriptions__content {
    display: block;
    margin-top: 2px;
  }
}
</style>