<template>
  <div class="order-status-report-container">
    <!-- 公共头部 -->
    <CommonHeader :title="`订单进度报告 - ${orderInfo?.contract_no || ''}`" />

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="orderInfo" class="report-content">
      <!-- 订单基础信息 -->
      <el-card class="report-section">
        <template #header>
          <div class="card-header">
            <span>订单基础信息</span>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="合同编号">{{ orderInfo.contract_no }}</el-descriptions-item>
          <el-descriptions-item label="订单编号">{{ orderInfo.order_no }}</el-descriptions-item>
          <el-descriptions-item label="包装机单号">{{ orderInfo.machine_no }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ orderInfo.machine_name }}</el-descriptions-item>
          <el-descriptions-item label="机型">{{ orderInfo.machine_model }}</el-descriptions-item>
          <el-descriptions-item label="主机数量">{{ orderInfo.machine_count }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatDate(orderInfo.order_time) }}</el-descriptions-item>
          <el-descriptions-item label="预计出货时间">{{ formatDate(orderInfo.ship_time) }}</el-descriptions-item>
          <el-descriptions-item label="总进度">
            <div class="progress-container">
              <div style="width: 60%; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                <div :style="{width: getOrderProgress() + '%', height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
              </div>
              <span style="margin-left: 15px;">{{ statusInfo.completed_tasks }} / {{ statusInfo.total_tasks }}</span>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 状态日志及任务详情 -->
      <div v-for="(statusLog, logIndex) in statusLogs" :key="statusLog.id" class="status-log-section">
        <el-card class="report-section">
          <template #header>
            <div class="card-header status-log-header">
              <div style="display: flex;align-items: center; gap: 20px;">
                <span class="status-log-title">{{ statusLog.status }}</span>
                <div class="progress-container">
                  <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                    <div :style="{width: getStatusLogProgress(statusLog.id) + '%', height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                  </div>
                  <div class="progress-text" style="margin-top: 2px;">
                    {{ getStatusLogCompletionInfo(statusLog.id) }}
                  </div>
                </div>
              </div>
              <div class="status-log-meta">
                <div v-if="statusLog.start_time" class="status-meta-item">开始: {{ formatDate(statusLog.start_time) }}</div>
                <div v-if="statusLog.expected_completion_time" class="status-meta-item">预计完成: {{ formatDate(statusLog.expected_completion_time) }}</div>
                <div v-if="statusLog.actual_completion_time" class="status-meta-item">实际完成: {{ formatDate(statusLog.actual_completion_time) }}</div>
              </div>
            </div>
          </template>

          <!-- 任务列表 -->
          <div class="tasks-container">
            <el-table :data="getStatusLogTasks(statusLog.id)" style="width: 100%" row-key="id">
              <el-table-column prop="name" label="任务名称" width="200">
                <template #default="scope">
                  <div class="task-name-cell">
                    <el-icon v-if="scope.row.is_completed" style="color: #67c23a;"><CircleCheckFilled /></el-icon>
                    <el-icon v-else style="color: #e6a23c;"><Clock /></el-icon>
                    <span style="margin-left: 8px;">{{ scope.row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="照片" width="200">
                <template #default="scope">
                  <div class="task-images-container">
                    <template v-if="scope.row.thumb_photo_path">
                      <el-image
                        v-for="(image, imgIndex) in scope.row.thumb_photo_path.split(',')"
                        :key="imgIndex"
                        :src="image"
                        :preview-src-list="scope.row.photo_path.split(',')"
                        preview-teleported
                        hide-on-click-modal
                        close-on-press-esc
                        style="width: 40px; height: 40px; object-fit: cover; margin-right: 5px; border-radius: 3px; cursor: pointer;"
                        fit="cover"
                      />
                    </template>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="200" />
              <el-table-column prop="is_completed" label="完成状态" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.is_completed ? 'success' : 'warning'">
                    {{ scope.row.is_completed ? '已完成' : '未完成' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="create_time" label="创建时间" width="150">
                <template #default="scope">
                  {{ formatDate(scope.row.create_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="update_time" label="更新时间" width="150">
                <template #default="scope">
                  {{ formatDate(scope.row.update_time) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="printReport">
          <el-icon><Printer /></el-icon> 打印报告
        </el-button>
        <el-button @click="exportToPDF">
          <el-icon><Download /></el-icon> 导出PDF
        </el-button>
        <el-button @click="goBack">
          <el-icon><Back /></el-icon> 返回
        </el-button>
      </div>
    </div>

    <div v-else class="no-data-container">
      <el-empty description="未找到订单进度信息" />
    </div>

    <!-- 加载遮罩 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  List,
  Printer,
  Download,
  Back,
  Loading,
  CircleCheckFilled,
  Clock
} from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';

// 响应式数据
const route = useRoute();
const router = useRouter();
const orderInfo = ref<any>(null);
const statusInfo = ref<any>(null);
const statusLogs = ref<any[]>([]);
const tasks = ref<any[]>([]);
const loading = ref(false);

// 获取URL参数中的订单ID
const orderId = ref<number | null>(null);

// 计算属性和方法
const getStatusLogTasks = (statusLogId: number) => {
  return tasks.value.filter((task: any) => task.status_log_id === statusLogId);
};

const getOrderProgress = () => {
  const completed = statusInfo.value?.completed_tasks || 0;
  const total = statusInfo.value?.total_tasks || 0;
  
  // 计算百分比，避免除零错误
  if (total === 0) {
    return 0;
  }
  
  return Math.round((completed / total) * 100);
};

const getStatusLogProgress = (statusLogId: number) => {
  const taskList = getStatusLogTasks(statusLogId);
  if (taskList.length === 0) return 0;

  const completedTasks = taskList.filter((task: any) => task.is_completed).length;
  return Math.round((completedTasks / taskList.length) * 100);
};

const getStatusLogCompletionInfo = (statusLogId: number) => {
  const taskList = getStatusLogTasks(statusLogId);
  const completedTasks = taskList.filter((task: any) => task.is_completed).length;
  return `${completedTasks} / ${taskList.length}`;
};

const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN');
};

const getProgressStatusText = (status: string) => {
  const statusMap: { [key: string]: string } = {
    'pending': '待开始',
    'in_progress': '进行中',
    'completed': '已完成'
  };
  return statusMap[status] || status;
};

const getCurrentStatusText = (status: number) => {
  const statusMap: { [key: number]: string } = {
    1: '下单',
    2: '排产',
    3: '完成生产',
    4: '验收阶段',
    5: '发货'
  };
  return statusMap[status] || `状态${status}`;
};

// 业务逻辑方法
const fetchOrderStatusReport = async () => {
  if (!orderId.value) {
    ElMessage.error('订单ID不能为空');
    return;
  }

  loading.value = true;
  try {
    const response: any = await request.get(`/api/order-status/${orderId.value}/report`);

    // request.ts会自动解包data，所以response直接就是数据内容
    orderInfo.value = response.order_info || {};
    statusInfo.value = response.status_info
    statusLogs.value = response.status_logs || [];
    tasks.value = response.tasks || [];
  } catch (error) {
    console.error('获取订单进度报告失败:', error);
    ElMessage.error('获取订单进度报告失败');
  } finally {
    loading.value = false;
  }
};

const printReport = () => {
  ElMessage.info('打印功能开发中...');
  // 实际项目中可以使用 window.print() 或专门的打印库
};

const exportToPDF = () => {
  ElMessage.info('PDF导出功能开发中...');
  // 实际项目中可以使用 jsPDF 或类似库
};

const goBack = () => {
  router.back();
};

// 生命周期
onMounted(() => {
  // 从路由参数获取订单ID
  const id = route.query.orderId;
  if (id) {
    orderId.value = typeof id === 'string' ? parseInt(id, 10) : id as number;
  } else {
    // 如果没有提供order_id，尝试从其他参数获取
    const idFromParams = route.params.orderId;
    if (idFromParams) {
      orderId.value = typeof idFromParams === 'string' ? parseInt(idFromParams, 10) : idFromParams as number;
    }
  }

  if (orderId.value) {
    fetchOrderStatusReport();
  } else {
    ElMessage.error('订单ID不能为空');
  }
});
</script>

<style scoped>
.order-status-report-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.report-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-log-header {
  flex-direction: column;
  align-items: flex-start;
}

.status-log-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.status-log-meta {
  display: flex;
  gap: 15px;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.status-meta-item {
  background-color: #f4f4f5;
  padding: 2px 8px;
  border-radius: 4px;
}

.progress-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  padding: 5px 10px;
  background-color: rgba(156, 156, 156, 0.1);
  border-radius: 5px;
}

.progress-text {
  font-size: 12px;
  color: #606266;
  text-align: center;
  width: 100%;
}

.tasks-container {
  margin-top: 15px;
}

.task-name-cell {
  display: flex;
  align-items: center;
}

.task-images-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 30px;
  padding: 20px 0;
  border-top: 1px solid #ebeef5;
}

.loading-container {
  padding: 40px;
}

.no-data-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-icon {
  font-size: 36px;
  animation: rotating 2s linear infinite;
  margin-bottom: 15px;
  color: #409eff;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .order-status-report-container {
    padding: 10px;
  }

  .status-log-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .status-log-meta {
    flex-wrap: wrap;
  }

  .action-buttons {
    flex-direction: column;
    align-items: center;
  }

  .el-table {
    font-size: 12px;
  }

  .el-table th,
  .el-table td {
    padding: 4px 2px;
  }
}
</style>