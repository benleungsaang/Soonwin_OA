<template>
  <div class="inspection-report-container">
    <div class="header">
      <div class="header-content">
        <el-page-header @back="goBack" content="订单验收报告" />
      </div>
    </div>

    <div v-if="loading" class="loading">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="reportData" class="report-content">
      <!-- 订单信息卡片 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>订单信息</span>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="合同编号">{{ reportData.inspection.contract_no }}</el-descriptions-item>
          <el-descriptions-item label="订单编号">{{ reportData.inspection.order_no }}</el-descriptions-item>
          <el-descriptions-item label="包装机单号">{{ reportData.inspection.machine_no }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ reportData.inspection.machine_name }}</el-descriptions-item>
          <el-descriptions-item label="机型">{{ reportData.inspection.machine_model }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ reportData.inspection.machine_count }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatDate(reportData.inspection.order_time) }}</el-descriptions-item>
          <el-descriptions-item label="出货时间">{{ formatDate(reportData.inspection.ship_time) }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 验收汇总卡片 -->
      <el-card class="summary-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span>验收汇总</span>
          </div>
        </template>
        <div class="summary-content">
          <div class="summary-item">
            <div class="summary-value">{{ reportData.summary.total_items }}</div>
            <div class="summary-label">检查项总数</div>
          </div>
          <div class="summary-item">
            <div class="summary-value">{{ reportData.summary.completed_items }}</div>
            <div class="summary-label">已完成项</div>
          </div>
          <div class="summary-item">
            <div class="summary-value" :class="reportData.summary.status === 'completed' ? 'completed' : reportData.summary.status === 'in_progress' ? 'in-progress' : 'pending'">
              {{ reportData.summary.progress }}%
            </div>
            <div class="summary-label">完成进度</div>
          </div>
          <div class="summary-item">
            <div class="summary-value" :class="getStatusClass(reportData.summary.status)">
              {{ getStatusText(reportData.summary.status) }}
            </div>
            <div class="summary-label">验收状态</div>
          </div>
        </div>
      </el-card>

      <!-- 检查项详情 -->
      <el-card class="items-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span>检查项详情</span>
          </div>
        </template>

        <div v-for="parentItem in groupedItems" :key="parentItem.id" class="inspection-group">
          <div class="parent-item">
            <div class="parent-header">
              <div class="parent-main">
                <h3 class="parent-title">{{ parentItem.item_category }}</h3>
                <div class="parent-stats">
                  <span class="progress-text">完成: {{ parentItem.completed_children }} / {{ parentItem.total_children }}</span>
                  <el-progress
                    :percentage="parentItem.progress"
                    :status="parentItem.progress === 100 ? 'success' : 'warning'"
                    :show-text="false"
                    height="12px"
                  />
                  <span class="progress-percent">{{ parentItem.progress }}%</span>
                </div>
              </div>
            </div>

            <div class="sub-items">
              <div
                v-for="subItem in parentItem.children"
                :key="subItem.id"
                class="sub-item"
                :class="getInspectionResultClass(subItem.inspection_result)"
              >
                <div class="sub-item-header">
                  <span class="sub-item-name">{{ subItem.item_name }}</span>
                  <div class="result-badge" :class="subItem.inspection_result">
                    {{ getInspectionResultText(subItem.inspection_result) }}
                  </div>
                </div>

                <div class="sub-item-details">
                  <!-- 正常情况 -->
                  <div v-if="subItem.inspection_result === 'normal'" class="normal-details">
                    <div v-if="subItem.photo_path" class="photo-section">
                      <h4>照片:</h4>
                      <img :src="subItem.photo_path" alt="正常照片" class="inspection-photo">
                    </div>
                  </div>

                  <!-- 缺陷情况 -->
                  <div v-else-if="subItem.inspection_result === 'defect'" class="defect-details">
                    <div v-if="subItem.photo_path" class="photo-section">
                      <h4>缺陷照片:</h4>
                      <img :src="subItem.photo_path" alt="缺陷照片" class="inspection-photo">
                    </div>
                    <div v-if="subItem.description" class="description-section">
                      <h4>缺陷描述:</h4>
                      <p class="defect-description">{{ subItem.description }}</p>
                    </div>
                  </div>

                  <!-- 无此项 -->
                  <div v-else-if="subItem.inspection_result === 'not_applicable'" class="not-applicable-details">
                    <p>此项不适用，无需检查</p>
                  </div>

                  <!-- 待检查 -->
                  <div v-else-if="subItem.inspection_result === 'pending'" class="pending-details">
                    <p>待检查</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 独立检查项 -->
        <div v-for="item in standaloneItems" :key="item.id" class="standalone-item">
          <div class="sub-item" :class="getInspectionResultClass(item.inspection_result)">
            <div class="sub-item-header">
              <span class="sub-item-name">{{ item.item_name }}</span>
              <div class="result-badge" :class="item.inspection_result">
                {{ getInspectionResultText(item.inspection_result) }}
              </div>
            </div>

            <div class="sub-item-details">
              <!-- 正常情况 -->
              <div v-if="item.inspection_result === 'normal'" class="normal-details">
                <div v-if="item.photo_path" class="photo-section">
                  <h4>照片:</h4>
                  <img :src="item.photo_path" alt="正常照片" class="inspection-photo">
                </div>
              </div>

              <!-- 缺陷情况 -->
              <div v-else-if="item.inspection_result === 'defect'" class="defect-details">
                <div v-if="item.photo_path" class="photo-section">
                  <h4>缺陷照片:</h4>
                  <img :src="item.photo_path" alt="缺陷照片" class="inspection-photo">
                </div>
                <div v-if="item.description" class="description-section">
                  <h4>缺陷描述:</h4>
                  <p class="defect-description">{{ item.description }}</p>
                </div>
              </div>

              <!-- 无此项 -->
              <div v-else-if="item.inspection_result === 'not_applicable'" class="not-applicable-details">
                <p>此项不适用，无需检查</p>
              </div>

              <!-- 待检查 -->
              <div v-else-if="item.inspection_result === 'pending'" class="pending-details">
                <p>待检查</p>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <div v-else class="no-data">
      <p>未找到验收报告数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import request from '@/utils/request';
import { ElMessage } from 'element-plus';

const router = useRouter();
const route = useRoute();

const reportData = ref<any>(null);
const loading = ref(false);
const inspectionId = ref(Number(route.params.inspectionId));

// 计算属性：分组的检查项
const groupedItems = computed(() => {
  if (!reportData.value || !reportData.value.items) return [];

  return reportData.value.items
    .filter((item: any) => item.item_type === 'parent')
    .map((parent: any) => {
      const children = reportData.value.items.filter((child: any) => child.parent_id === parent.id);
      return {
        ...parent,
        children: children,
        completed_children: children.filter((child: any) =>
          child.inspection_result === 'normal' || child.inspection_result === 'not_applicable'
        ).length,
        total_children: children.length,
        progress: children.length > 0
          ? Math.round((children.filter((child: any) =>
              child.inspection_result === 'normal' || child.inspection_result === 'not_applicable'
            ).length / children.length) * 100)
          : 0
      };
    });
});

// 计算属性：独立的检查项（没有父项的子项）
const standaloneItems = computed(() => {
  if (!reportData.value || !reportData.value.items) return [];
  return reportData.value.items.filter((item: any) => item.item_type === 'sub' && item.parent_id === null);
});

// 获取验收报告数据
const fetchReportData = async () => {
  if (!inspectionId.value) {
    ElMessage.error('无效的验收ID');
    return;
  }

  loading.value = true;
  try {
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
  return date.toISOString().split('T')[0];
};

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待验收',
    'in_progress': '验收中',
    'completed': '已完成'
  };
  return statusMap[status] || status;
};

// 获取状态样式类
const getStatusClass = (status: string) => {
  return `status-${status}`;
};

// 获取检查结果文本
const getInspectionResultText = (result: string) => {
  const resultMap: Record<string, string> = {
    'pending': '待检查',
    'normal': '正常',
    'defect': '缺陷',
    'not_applicable': '无此项'
  };
  return resultMap[result] || result;
};

// 获取检查结果样式类
const getInspectionResultClass = (result: string) => {
  return `result-${result}`;
};

// 返回按钮
const goBack = () => {
  router.go(-1); // 返回上一页
};

// 组件挂载时获取数据
onMounted(() => {
  fetchReportData();
});
</script>

<style scoped>
.inspection-report-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-card, .summary-card, .items-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

.summary-content {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
}

.summary-item {
  text-align: center;
  padding: 10px 20px;
  min-width: 120px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.summary-value.completed {
  color: #67c23a;
}

.summary-value.in-progress {
  color: #e6a23c;
}

.summary-value.pending {
  color: #909399;
}

.status-pending {
  color: #909399;
}

.status-in_progress {
  color: #e6a23c;
}

.status-completed {
  color: #67c23a;
}

.summary-label {
  font-size: 14px;
  color: #606266;
}

.inspection-group {
  margin-bottom: 25px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background-color: white;
}

.parent-item {
  padding: 15px;
}

.parent-header {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 15px;
  margin-bottom: 15px;
}

.parent-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.parent-title {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.parent-stats {
  text-align: right;
}

.progress-text {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.progress-percent {
  font-weight: bold;
  color: #409eff;
}

.sub-items {
  padding-left: 20px;
}

.sub-item {
  margin-bottom: 15px;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.sub-item.result-normal {
  border-left: 4px solid #67c23a;
  background-color: #f0f9ff;
}

.sub-item.result-defect {
  border-left: 4px solid #f56c6c;
  background-color: #fef0f0;
}

.sub-item.result-not_applicable {
  border-left: 4px solid #909399;
  background-color: #f4f4f5;
}

.sub-item.result-pending {
  border-left: 4px solid #e6a23c;
  background-color: #fdf6ec;
}

.sub-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.sub-item-name {
  font-weight: 500;
  font-size: 16px;
}

.result-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.result-badge.normal {
  background-color: #f0f9ff;
  color: #67c23a;
  border: 1px solid #b3d8ff;
}

.result-badge.defect {
  background-color: #fef0f0;
  color: #f56c6c;
  border: 1px solid #feb0b0;
}

.result-badge.not_applicable {
  background-color: #f4f4f5;
  color: #909399;
  border: 1px solid #d3d4d6;
}

.result-badge.pending {
  background-color: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #f5dab1;
}

.sub-item-details {
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
}

.photo-section {
  margin-top: 10px;
}

.photo-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.inspection-photo {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.description-section {
  margin-top: 10px;
}

.description-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.defect-description {
  padding: 8px;
  background-color: #fef0f0;
  border-left: 3px solid #f56c6c;
  border-radius: 2px;
  color: #606266;
  line-height: 1.5;
}

.loading {
  text-align: center;
  padding: 40px;
}

.no-data {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.standalone-item {
  margin-top: 20px;
}
</style>