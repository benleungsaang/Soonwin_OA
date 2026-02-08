<template>
  <div class="order-progress-container">
    <CommonHeader title="订单进度管理" />
    
    <el-card shadow="hover" class="management-card">
      <template #header>
        <div class="card-header">
          <span>订单进度管理</span>
        </div>
      </template>

      <!-- 订单搜索 -->
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="订单号">
          <el-input v-model="searchForm.orderNo" placeholder="请输入订单号" clearable />
        </el-form-item>
        <el-form-item label="合同号">
          <el-input v-model="searchForm.contractNo" placeholder="请输入合同号" clearable />
        </el-form-item>
        <el-form-item label="机器型号">
          <el-input v-model="searchForm.machineModel" placeholder="请输入机器型号" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">搜索</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 订单列表 -->
      <el-table
        :data="orders"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ 'text-align': 'center' }"
        :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
      >
        <el-table-column prop="contract_no" label="合同号" width="150" align="center" header-align="center" />
        <el-table-column prop="order_no" label="订单号" width="150" align="center" header-align="center" />
        <el-table-column prop="machine_no" label="机器号" width="150" align="center" header-align="center" />
        <el-table-column prop="machine_model" label="机器型号" width="150" align="center" header-align="center" />
        <el-table-column label="订单时间" width="120" align="center" header-align="center">
          <template #default="scope">
            {{ scope.row.order_time ? formatDateTime(scope.row.order_time) : '无' }}
          </template>
        </el-table-column>
        <el-table-column label="发货时间" width="120" align="center" header-align="center">
          <template #default="scope">
            {{ scope.row.ship_time ? formatDateTime(scope.row.ship_time) : '无' }}
          </template>
        </el-table-column>
        <el-table-column prop="current_status" label="当前状态" width="120" align="center" header-align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.current_status)">
              {{ scope.row.current_status || '未开始' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center" header-align="center">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="viewProgress(scope.row)"
              :icon="View"
              circle
            />
            <el-button
              size="small"
              type="success"
              @click="editProgress(scope.row)"
              :icon="Edit"
              circle
            />
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        class="pagination"
      />

      <!-- 进度详情对话框 -->
      <el-dialog
        v-model="progressDialogVisible"
        :title="`订单进度详情 - ${selectedOrder?.contract_no || ''}`"
        width="80%"
        top="5vh"
      >
        <div v-if="progressData" class="progress-detail">
          <!-- 进度统计 -->
          <el-card class="progress-stat-card">
            <div class="stat-item">
              <div class="stat-label">完成率</div>
              <div class="stat-value">{{ progressData.progress_stat.rate }}%</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">已完成</div>
              <div class="stat-value">{{ progressData.progress_stat.completed }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">总计</div>
              <div class="stat-value">{{ progressData.progress_stat.total }}</div>
            </div>
          </el-card>

          <!-- 进度状态时间线 -->
          <el-timeline class="progress-timeline">
            <el-timeline-item
              v-for="detail in progressData.progress_info.status_details"
              :key="detail.id"
              :timestamp="`状态: ${detail.status} | 开始: ${detail.start_time || '无'} | 预计完成: ${detail.expected_complete_time || '无'} | 实际完成: ${detail.actual_complete_time || '无'}`"
              :type="getTimelineType(detail.status, progressData.progress_info.current_status)"
              :hollow="true"
            >
              <el-card>
                <h4>{{ detail.status }}</h4>
                <p>开始时间: {{ detail.start_time || '无' }}</p>
                <p>预计完成时间: {{ detail.expected_complete_time || '无' }}</p>
                <p>实际完成时间: {{ detail.actual_complete_time || '无' }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>

          <!-- 进度项列表 -->
          <div class="progress-items-section">
            <h3>进度项列表</h3>
            <el-table
              :data="progressData.progress_items"
              style="width: 100%"
              stripe
              border
              :header-cell-style="{ 'text-align': 'center' }"
              :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
            >
              <el-table-column prop="title" label="项目名称" align="center" header-align="center" />
              <el-table-column prop="status" label="状态" width="100" align="center" header-align="center">
                <template #default="scope">
                  <el-tag :type="getProgressItemType(scope.row.status)">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="remark" label="备注" align="center" header-align="center" />
              <el-table-column label="创建时间" width="150" align="center" header-align="center">
                <template #default="scope">
                  {{ formatDateTime(scope.row.create_time) }}
                </template>
              </el-table-column>
              <el-table-column label="更新时间" width="150" align="center" header-align="center">
                <template #default="scope">
                  {{ scope.row.update_time ? formatDateTime(scope.row.update_time) : '无' }}
                </template>
              </el-table-column>
              <el-table-column label="附件" width="150" align="center" header-align="center">
                <template #default="scope">
                  <div v-if="scope.row.media_files && scope.row.media_files.length > 0">
                    <el-button
                      size="small"
                      type="primary"
                      @click="previewMedia(scope.row.media_files)"
                      :icon="View"
                    >
                      预览({{ scope.row.media_files.length }})
                    </el-button>
                  </div>
                  <div v-else>无附件</div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="progressDialogVisible = false">关闭</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 媒体文件预览对话框 -->
      <el-dialog
        v-model="mediaPreviewDialogVisible"
        title="媒体文件预览"
        width="80%"
      >
        <div class="media-preview-container">
          <div
            v-for="media in previewMediaFiles"
            :key="media.id"
            class="media-item"
          >
            <h4>{{ media.file_name }}</h4>
            <div v-if="media.file_type === 'image'" class="image-container">
              <img :src="media.file_url" :alt="media.file_name" style="max-width: 100%; max-height: 400px;" />
            </div>
            <div v-else-if="media.file_type === 'video'" class="video-container">
              <video :src="media.file_url" controls style="max-width: 100%; max-height: 400px;"></video>
            </div>
            <div v-else class="file-container">
              <el-link :href="media.file_url" target="_blank" type="primary">
                下载文件: {{ media.file_name }}
              </el-link>
            </div>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="mediaPreviewDialogVisible = false">关闭</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { View, Edit } from '@element-plus/icons-vue';
import request from '@/utils/request';
import CommonHeader from '@/components/CommonHeader.vue';

interface Order {
  id: string;
  contract_no: string;
  order_no: string;
  machine_no: string;
  machine_model: string;
  order_time?: string;
  ship_time?: string;
  current_status?: string;
}

interface ProgressData {
  order_info: {
    id: string;
    contract_no: string;
    order_no: string;
    machine_no: string;
    machine_name: string;
    machine_model: string;
    machine_count: number;
    order_time?: string;
    ship_time?: string;
  };
  progress_info: {
    id: number;
    current_status: string;
    status_details: Array<{
      id: number;
      status: string;
      start_time?: string;
      expected_complete_time?: string;
      actual_complete_time?: string;
    }>;
  };
  progress_items: Array<{
    id: number;
    title: string;
    status: string;
    remark: string;
    create_time: string;
    update_time?: string;
    media_files: Array<{
      id: number;
      file_type: string;
      file_url: string;
      file_name: string;
      upload_time: string;
    }>;
  }>;
  progress_stat: {
    completed: number;
    total: number;
    rate: number;
  };
}

interface MediaFile {
  id: number;
  file_type: string;
  file_url: string;
  file_name: string;
  upload_time: string;
}

// 搜索表单
const searchForm = ref({
  orderNo: '',
  contractNo: '',
  machineModel: ''
});

// 订单列表
const orders = ref<Order[]>([]);
const loading = ref(false);

// 分页
const pagination = ref({
  page: 1,
  size: 10,
  total: 0
});

// 进度详情对话框
const progressDialogVisible = ref(false);
const progressData = ref<ProgressData | null>(null);
const selectedOrder = ref<Order | null>(null);

// 媒体文件预览
const mediaPreviewDialogVisible = ref(false);
const previewMediaFiles = ref<MediaFile[]>([]);

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.page,
      size: pagination.value.size
    };

    // 添加搜索条件
    if (searchForm.value.orderNo) params.order_no = searchForm.value.orderNo;
    if (searchForm.value.contractNo) params.contract_no = searchForm.value.contractNo;
    if (searchForm.value.machineModel) params.machine_model = searchForm.value.machineModel;

    const response: any = await request.get('/api/orders', { params });

    if (response && response.data) {
      orders.value = response.data.list || [];
      pagination.value.total = response.data.total || 0;
    } else {
      orders.value = [];
      pagination.value.total = 0;
    }
  } catch (error) {
    ElMessage.error('获取订单列表失败');
    console.error('Error fetching orders:', error);
  } finally {
    loading.value = false;
  }
};

// 搜索
const onSearch = () => {
  pagination.value.page = 1;
  fetchOrders();
};

// 重置
const onReset = () => {
  searchForm.value = {
    orderNo: '',
    contractNo: '',
    machineModel: ''
  };
  pagination.value.page = 1;
  fetchOrders();
};

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.value.size = size;
  pagination.value.page = 1;
  fetchOrders();
};

const handleCurrentChange = (page: number) => {
  pagination.value.page = page;
  fetchOrders();
};

// 查看进度详情
const viewProgress = async (order: Order) => {
  try {
    const response: any = await request.get(`/api/orders/${order.id}/progress`);
    
    if (response && response.data) {
      progressData.value = response.data;
      selectedOrder.value = order;
      progressDialogVisible.value = true;
    } else {
      ElMessage.error('获取进度详情失败');
    }
  } catch (error) {
    ElMessage.error('获取进度详情失败');
    console.error('Error fetching progress:', error);
  }
};

// 编辑进度
const editProgress = (order: Order) => {
  // 跳转到编辑页面，这里可以传订单ID参数
  ElMessage.warning('编辑功能请跳转到订单状态跟踪页面进行编辑');
  // 实际应用中可能会跳转到专门的编辑页面
  // router.push(`/order-progress/edit/${order.id}`);
};

// 预览媒体文件
const previewMedia = (mediaFiles: MediaFile[]) => {
  previewMediaFiles.value = mediaFiles;
  mediaPreviewDialogVisible.value = true;
};

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '无';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  } catch (error) {
    return dateString; // 如果解析失败，返回原始字符串
  }
};

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case '已完成':
    case '完成':
      return 'success';
    case '进行中':
    case '生产中':
      return 'primary';
    case '未开始':
      return 'info';
    case '暂停':
      return 'warning';
    case '取消':
      return 'danger';
    default:
      return 'info';
  }
};

// 获取时间线类型
const getTimelineType = (status: string, currentStatus: string) => {
  if (status === currentStatus) {
    return 'primary';
  }
  
  // 检查是否已完成（状态在当前状态之前）
  const statusOrder = ['未开始', '下单', '设计', '采购', '生产', '测试', '包装', '发货', '完成'];
  const currentStatusIndex = statusOrder.indexOf(currentStatus);
  const statusIndex = statusOrder.indexOf(status);
  
  if (statusIndex < currentStatusIndex && currentStatusIndex >= 0 && statusIndex >= 0) {
    return 'success';
  }
  
  return 'info';
};

// 获取进度项类型
const getProgressItemType = (status: string) => {
  switch (status) {
    case '已完成':
      return 'success';
    case '进行中':
      return 'primary';
    case '未完成':
      return 'info';
    case '暂停':
      return 'warning';
    case '取消':
      return 'danger';
    default:
      return 'info';
  }
};

// 组件挂载时获取数据
onMounted(() => {
  fetchOrders();
});
</script>

<style scoped>
.order-progress-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.management-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.search-form .el-form-item {
  margin-bottom: 12px;
  margin-right: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.progress-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.progress-stat-card {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
  padding: 15px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.progress-timeline {
  margin: 20px 0;
}

.progress-items-section {
  margin-top: 30px;
}

.progress-items-section h3 {
  margin-bottom: 15px;
  color: #303133;
}

.media-preview-container {
  max-height: 60vh;
  overflow-y: auto;
}

.media-item {
  margin-bottom: 20px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.image-container, .video-container, .file-container {
  margin-top: 10px;
  text-align: center;
}
</style>