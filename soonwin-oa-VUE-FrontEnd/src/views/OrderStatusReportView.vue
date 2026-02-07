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
              <div style="width: 60%; height: 8px; background: rgba(255, 186, 98, 0.6); border-radius: 4px; overflow: hidden;">
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
                  <div style="width: 100px; height: 8px; background: rgba(255, 186, 98, 0.6); border-radius: 4px; overflow: hidden;">
                    <div :style="{width: getStatusLogProgress(statusLog.id) + '%', height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                  </div>
                  <div class="progress-text" style="margin-top: 2px;">
                    {{ getStatusLogCompletionInfo(statusLog.id) }}
                  </div>
                </div>
                <div class="status-log-meta">
                  <div class="status-meta-item">开始: {{ formatDate(statusLog.start_time) || '未有设置' }}</div>
                  <div class="status-meta-item">预计完成: {{ formatDate(statusLog.expected_completion_time)  || '未有设置' }}</div>
                  <div v-if="statusLog.actual_completion_time" class="status-meta-item">实际完成: {{ formatDate(statusLog.actual_completion_time) }}</div>
                </div>
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
              <el-table-column label="媒体文件" width="250">
                <template #default="scope">
                  <div class="task-media-container">
                    <template v-if="getTaskMediaFiles(scope.row).length > 0">
                      <div
                        v-for="(media, mediaIndex) in getTaskMediaFiles(scope.row)"
                        :key="'media-' + scope.row.id + '-' + mediaIndex"
                        style="position: relative; display: inline-block; margin-right: 5px;"
                      >
                        <template v-if="media.file_type === 'image'">
                          <el-image
                            :src="media.thumb || media.url"
                            :preview-src-list="getTaskImageUrls(scope.row)"
                            preview-teleported
                            hide-on-click-modal
                            close-on-press-esc
                            style="width: 40px; height: 40px; object-fit: cover; border-radius: 3px; cursor: pointer;"
                            fit="cover"
                          />
                          <div class="file-type-indicator" style="top: -3px; right: -3px;background-color: #67c23a;">
                            <el-icon><Picture /></el-icon>
                          </div>
                        </template>

                        <template v-else-if="media.file_type === 'video'">
                          <img
                            :src="media.thumb || media.url || '/assets/default-video-thumbnail.jpg'"
                            style="width: 40px; height: 40px; object-fit: cover; border-radius: 3px; cursor: pointer;"
                            @click="playVideo(media.url)"
                          />
                          <div class="file-type-indicator" style="top: -3px; right: -3px;">
                            <el-icon><VideoCamera /></el-icon>
                          </div>
                        </template>
                      </div>
                    </template>

                    <template v-else>
                      <span style="color: #999; font-size: 12px;">暂无媒体文件</span>
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

    <!-- 视频播放模态框 -->
    <div v-if="showVideoPlayer" class="video-modal-overlay" @click="closeVideoPlayer">
      <div class="video-modal-content" @click.stop>
        <video
          :src="currentVideoSrc"
          controls
          autoplay
          class="video-player"
          @click.stop
        ></video>
        <div class="video-controls">
          <button class="close-btn" @click="closeVideoPlayer">关闭</button>
        </div>
      </div>
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
  Clock,
  Picture,
  VideoCamera,
  VideoPlay
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

// 视频播放相关
const showVideoPlayer = ref(false);
const currentVideoSrc = ref('');

// 获取URL参数中的订单ID
const orderId = ref<number | null>(null);

// 计算属性和方法
const getStatusLogTasks = (statusLogId: number) => {
  return tasks.value.filter((task: any) => task.status_log_id === statusLogId);
};

/**
 * 将任务的媒体文件解析为结构化数组
 * @param task 任务对象
 * @returns 媒体文件对象数组 [{ url: '', thumb: '', file_type: '' }, ...]
 */
const getTaskMediaFiles = (task: any) => {
  if (!task) return [];

  // 使用新的media_files字段
  if (task.media_files && Array.isArray(task.media_files)) {
    return task.media_files
      .filter((file: any) => file.file_type === 'image' || file.file_type === 'video') // 获取图片和视频
      .map((file: any) => ({
        url: file.file_path,
        thumb: file.thumb_path || file.file_path, // 如果没有缩略图，使用原图
        id: file.id,  // 媒体文件ID
        file_type: file.file_type  // 文件类型：image或video
      }));
  }

  // 兼容旧字段结构
  const mediaFiles = [];

  // 检查旧的images字段
  if (task.images && Array.isArray(task.images)) {
    task.images.forEach((img: any) => {
      mediaFiles.push({
        url: img.file_path || img.url,
        thumb: img.thumb_path || img.url,
        id: img.id,
        file_type: 'image'
      });
    });
  }

  // 检查旧的videos字段
  if (task.videos && Array.isArray(task.videos)) {
    task.videos.forEach((vid: any) => {
      mediaFiles.push({
        url: vid.file_path || vid.url,
        thumb: vid.thumb_path || vid.url,
        id: vid.id,
        file_type: 'video'
      });
    });
  }

  // 检查旧的单独字段
  if (task.photo_path && task.thumb_photo_path) {
    const photoPaths = task.photo_path.split(',').map((p: string) => p.trim());
    const thumbPaths = task.thumb_photo_path.split(',').map((t: string) => t.trim());

    for (let i = 0; i < Math.min(photoPaths.length, thumbPaths.length); i++) {
      mediaFiles.push({
        url: photoPaths[i],
        thumb: thumbPaths[i],
        file_type: 'image'
      });
    }
  }

  return mediaFiles;
};

/**
 * 获取任务的图片URL列表（用于预览）
 * @param task 任务对象
 * @returns 图片URL数组
 */
const getTaskImageUrls = (task: any) => {
  return getTaskMediaFiles(task)
    .filter((media: any) => media.file_type === 'image')
    .map((media: any) => media.url); // 总是返回原图用于预览
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

// 视频播放功能
const playVideo = (videoUrl: string) => {
  if (!videoUrl) {
    ElMessage.error('视频URL无效');
    return;
  }
  // 替换反斜杠为正斜杠
  const correctedUrl = videoUrl.replace(/\\/g, '/');
  currentVideoSrc.value = correctedUrl;
  showVideoPlayer.value = true;
};

const closeVideoPlayer = () => {
  showVideoPlayer.value = false;
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
    statusInfo.value = response.status_info;
    statusLogs.value = response.status_logs || [];

    // 处理任务数据，兼容新旧数据结构
    if (response.tasks && Array.isArray(response.tasks)) {
      // 无论返回的是分组结构还是扁平结构，都直接使用
      // 如果是分组结构（每个元素包含tasks数组），则展开
      if (response.tasks.length > 0 && Array.isArray(response.tasks[0].tasks)) {
        tasks.value = response.tasks.flatMap((taskGroup: any) => {
          return taskGroup.tasks || [];
        });
      } else {
        // 如果是扁平结构，直接赋值
        tasks.value = response.tasks || [];
      }
    } else {
      tasks.value = [];
    }
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
    orderId.value = typeof id === 'string' ? parseInt(id, 10) : Array.isArray(id) ? parseInt(id[0], 10) : id;
  } else {
    // 如果没有提供order_id，尝试从其他参数获取
    const idFromParams = route.params.orderId;
    if (idFromParams) {
      orderId.value = typeof idFromParams === 'string' ? parseInt(idFromParams, 10) : Array.isArray(idFromParams) ? parseInt(idFromParams[0], 10) : idFromParams;
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
  margin-left: 30px;
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

.file-type-indicator {
  position: absolute;
  width: 16px;
  height: 16px;
  background-color: #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.file-type-indicator .el-icon {
  font-size: 10px;
  color: white;
  margin: 0;
  padding: 0;
}

/* 简易视频播放模态框样式 */
.video-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 99999;
}

.video-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 90vw;
  max-height: 90vh;
  z-index: 100000;
}

.video-player {
  max-width: 100%;
  max-height: 85vh;
  border-radius: 8px;
  background: #000;
}

.video-controls {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.close-btn {
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
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