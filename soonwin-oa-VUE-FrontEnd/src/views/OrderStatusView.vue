<template>
  <div class="order-status-container">
    <!-- 公共头部 -->
    <CommonHeader title="订单进度" />

    <!-- 订单列表区域 -->
    <div class="order-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>待处理订单列表</span>
          </div>
        </template>

        <!-- 订单表格 -->
        <el-table
          :data="orders"
          style="width: 100%"
          @row-click="showOrderDetails"
          v-loading="loading"
        >
          <el-table-column prop="contract_no" label="合同编号" width="150" />
          <el-table-column prop="machine_name" label="名称" width="150" />
          <el-table-column prop="machine_model" label="机型" width="120" />
          <el-table-column prop="order_time" label="下单时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.order_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="ship_time" label="出货时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.ship_time) }}
            </template>
          </el-table-column>
          <el-table-column label="任务完成进度" width="150">
            <template #default="scope">
              <div
                style="cursor: pointer; display: flex; flex-direction: column; align-items: center;"
                @click.stop="showOrderDetails(scope.row)"
              >
                <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                  <div
                    :style="{width: `${getOrderStatusProgress(scope.row.id)}%`, height: '100%'}"
                    style="background: #67c23a; border-radius: 4px;"
                  ></div>
                </div>
                <div class="progress-text" style="margin-top: 2px;">
                  {{ getOrderStatusFraction(scope.row.id) }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="generateReport(scope.row)"
              >
                <el-icon style="margin-right: 5px;"><List /></el-icon> 报告
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页组件 -->
        <el-pagination
          class="pagination"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </el-card>
    </div>

    <!-- 订单进度详情弹窗 -->
    <el-dialog
      v-model="orderDetailDialogVisible"
      :title="`订单进度详情 - ${selectedOrderDetail?.contract_no || selectedOrder?.contract_no || ''}`"
      :width="isMobile ? '95%' : '80%'"
      :before-close="handleCloseOrderDetailDialog"
    >
      <div v-if="selectedOrderDetail || selectedOrder">
        <!-- 订单基础信息卡片 -->
        <el-card class="order-info-card">
          <template #header>
            <div class="card-header">
              <span>订单基础数据</span>
            </div>
          </template>
          <div class="order-info-container">
            <el-descriptions :column="isMobile ? 1 : 2" border>
              <el-descriptions-item label="合同编号">{{ (selectedOrderDetail || selectedOrder).contract_no }}</el-descriptions-item>
              <el-descriptions-item label="订单编号">{{ (selectedOrderDetail || selectedOrder).order_no }}</el-descriptions-item>
              <el-descriptions-item label="包装机单号">{{ (selectedOrderDetail || selectedOrder).machine_no }}</el-descriptions-item>
              <el-descriptions-item label="名称">{{ (selectedOrderDetail || selectedOrder).machine_name }}</el-descriptions-item>
              <el-descriptions-item label="机型">{{ (selectedOrderDetail || selectedOrder).machine_model }}</el-descriptions-item>
              <el-descriptions-item label="主机数量">{{ (selectedOrderDetail || selectedOrder).machine_count }}</el-descriptions-item>
              <el-descriptions-item label="下单时间">{{ formatDate((selectedOrderDetail || selectedOrder).order_time) }}</el-descriptions-item>
              <el-descriptions-item label="出货时间">{{ formatDate((selectedOrderDetail || selectedOrder).ship_time) }}</el-descriptions-item>
            </el-descriptions>

            <el-descriptions title="当前进度" border>
              <el-descriptions-item label="当前进度">{{ formatDate((selectedOrderDetail || selectedOrder).ship_time) }}</el-descriptions-item>
              <el-descriptions-item label="添加进度">
                <el-icon class="btn-add-status" @click="openAddStatusLogDialog"><Plus /></el-icon>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <!-- 订单状态日志卡片 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>OrderStatusLog</span>
              <div class="progress-container">
                <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                  <div :style="{width: `%`, height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                </div>
                <div class="progress-text" style="margin-top: 2px;">
                  is_completed / status_tasks_count
                </div>
              </div>
              <el-icon class="btn-add-task"><Plus /></el-icon>
            </div>
          </template>
          <div class="order-info-container">
            <el-descriptions
              direction="vertical"
              :column="2"
              title="StatusTask"
              border
            >
              <template #extra>
                <el-switch
                  v-model="is_completed"
                  size="large"
                  active-text="完成"
                  inactive-text="未完成"
                />
              </template>
              <el-descriptions-item :span="1" label="Image">
                image1, image2 , ...<el-icon class="btn-add-photo"><Camera /></el-icon>
              </el-descriptions-item>
              <el-descriptions-item :span="1" label="Description">
                Description
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
        <br>
        <!-- 订单状态日志卡片2 -->
        <el-card v-for="(statusLog, logIndex) in statusLogs" :key="statusLog.id">
          <template #header>
            <div class="card-header">
              <span>OrderStatusLog: {{ statusLog.status }}</span>
              <div class="progress-container">
                <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                  <div :style="{width: getStatusLogProgress(statusLog.id) + '%', height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                </div>
                <div class="progress-text" style="margin-top: 2px;">
                  {{ getStatusLogCompletionInfo(statusLog.id) }}
                </div>
              </div>
              <el-icon class="btn-add-task" @click="addStatusTask(statusLog.id)"><Plus /></el-icon>
            </div>
          </template>
          <div class="order-info-container">
            <el-descriptions
              v-for="(statusTask, taskIndex) in getStatusLogTasks(statusLog.id)"
              :key="statusTask.id"
              direction="vertical"
              :column="2"
              border
            >
              <template #extra>
                <el-switch
                  v-model="statusTask.is_completed"
                  size="large"
                  active-text="完成"
                  inactive-text="未完成"
                  @change="updateStatusTask(statusTask)"
                />
              </template>
              <el-descriptions-item :span="1" label="Image">
                <div v-if="statusTask.photo_path">
                  <div v-for="(image, imgIndex) in statusTask.photo_path.split(',')" :key="imgIndex" style="display: inline-block; margin-right: 5px;">
                    <el-image
                      :src="image"
                      :preview-src-list="statusTask.photo_path.split(',')"
                      preview-teleported
                      style="width: 50px; height: 50px; object-fit: cover;"
                    />
                  </div>
                </div>
                <el-icon class="btn-add-photo" @click="addPhotoToTask(statusTask.id)"><Camera /></el-icon>
              </el-descriptions-item>
              <el-descriptions-item :span="1" label="Name" class="clickable-field" @click="editStatusTaskField(statusTask, 'name')">
                {{ statusTask.name }}
              </el-descriptions-item>
              <el-descriptions-item :span="2" label="Description" class="clickable-field" @click="editStatusTaskField(statusTask, 'description')">
                {{ statusTask.description || '点击添加描述' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <!-- 底部操作区域 -->
        <div class="bottom-actions">
          <div class="progress-summary">
            <p>任务项进度：</p>
          </div>
          <div class="action-buttons">
            <el-button type="success" @click="">
              <el-icon style="margin-right: 5px;"><List /></el-icon>生成报告
            </el-button>
            <el-button type="primary" @click="">
              保存
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 添加订单状态日志模态框 -->
    <el-dialog
      v-model="showAddStatusLogDialog"
      title="添加订单状态日志"
      width="400px"
    >
      <el-form :model="newStatusLogForm" label-width="120px">
        <el-form-item label="状态" required>
          <el-input v-model="newStatusLogForm.status" placeholder="请输入状态名称" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="newStatusLogForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="预计完成时间">
          <el-date-picker
            v-model="newStatusLogForm.expected_completion_time"
            type="datetime"
            placeholder="选择预计完成时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddStatusLogDialog = false">取消</el-button>
          <el-button type="primary" @click="addStatusLog">确定</el-button>
        </span>
      </template>
    </el-dialog>



  </div>

</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, List, Loading, Camera } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';

// ===================== 响应式数据 =====================
const orders = ref<any[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const orderDetailDialogVisible = ref(false);
const selectedOrder = ref<any>({});
const selectedOrderDetail = ref<any>(null);
const selectedStatus = ref<any>(null);
const tasks = ref<any[]>([]);
const windowWidth = ref(window.innerWidth);
const is_completed = ref(false); // 补充缺失的响应式变量

// 订单状态日志相关
const showAddStatusLogDialog = ref(false);
const newStatusLogForm = ref({
  status: '',
  start_time: '',
  expected_completion_time: ''
});
const currentOrderStatusId = ref(null);
const statusLogs = ref<any[]>([]);


// ===================== 计算属性 =====================
// 判断是否为移动端
const isMobile = computed(() => windowWidth.value < 768);


// 获取用户角色
const userRole = ref('');

// 计算每个状态日志的进度
const getStatusLogProgress = (statusLogId: number) => {
  const tasks = getStatusLogTasks(statusLogId);
  if (tasks.length === 0) return 0;

  const completedTasks = tasks.filter((task: any) => task.is_completed).length;
  return Math.round((completedTasks / tasks.length) * 100);
};

// 获取某个状态日志的任务项
const getStatusLogTasks = (statusLogId: number) => {
  return tasks.value.filter((task: any) => task.status_log_id === statusLogId);
};

// 获取状态日志的完成信息
const getStatusLogCompletionInfo = (statusLogId: number) => {
  const tasks = getStatusLogTasks(statusLogId);
  const completedTasks = tasks.filter((task: any) => task.is_completed).length;
  return `${completedTasks} / ${tasks.length}`;
};

// 实时计算进度
const realTimeProgress = computed(() => {
  // 统计所有子任务（sub tasks）
  const allSubTasks = tasks.value.filter((task: any) => task.item_type === 'sub' && !task._toBeDeleted);
  const totalTasks = allSubTasks.length;

  // 统计已完成的子任务
  const completedTasks = allSubTasks.filter((task: any) => task.is_completed).length;

  // 计算进度百分比
  const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return {
    total_tasks: totalTasks,
    completed_tasks: completedTasks,
    progress: progress
  };
});

// ===================== 表单校验规则 =====================


// ===================== 工具方法 =====================
// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
};

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

// ===================== 业务逻辑方法 =====================
// 显示订单详情
const showOrderDetails = async (row: any) => {
  selectedOrderDetail.value = { ...row };
  orderDetailDialogVisible.value = true;

  // 加载订单状态详情
  await loadOrderStatusDetails();
};

// 关闭订单详情对话框
const handleCloseOrderDetailDialog = () => {
  orderDetailDialogVisible.value = false;
  selectedOrderDetail.value = null;
  selectedStatus.value = null;
  tasks.value = [];
};

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const response: any = await request.get('/api/order-status-orders', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    });

    orders.value = response.list || [];
    total.value = response.total || 0;
  } catch (error) {
    console.error('获取订单列表失败:', error);
    ElMessage.error('获取订单列表失败');
  } finally {
    loading.value = false;
  }
};

// 获取订单进度百分比
const getOrderStatusProgress = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  return order ? (order.progress_percent || 0) : 0;
};

// 获取订单进度的分数格式 (如: "1/3")
const getOrderStatusFraction = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  if (!order) return '0/0';

  const completedTasks = order.completed_tasks || 0;
  const totalTasks = order.total_tasks || 0;

  return `${completedTasks}/${totalTasks}`;
};

// 分页 - 每页条数变化
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchOrders();
};

// 分页 - 当前页变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchOrders();
};

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const tokenStr = localStorage.getItem('oa_token');
    if (tokenStr) {
      const tokenParts = tokenStr.split('.');
      if (tokenParts.length === 3) {
        try {
          const payload = JSON.parse(atob(tokenParts[1]));
          userRole.value = payload.user_role || 'user';
        } catch (e) {
          console.error('解析token失败:', e);
          userRole.value = 'user';
        }
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
    userRole.value = 'user';
  }
};

// ===================== 业务逻辑方法 =====================

// 打开添加状态日志对话框
const openAddStatusLogDialog = () => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    ElMessage.error('请先选择一个订单');
    return;
  }

  // 如果还没有创建订单状态记录，先创建一个
  if (!selectedOrderDetail.value.status_id) {
    ElMessage.error('此订单尚无状态记录，请先创建');
    return;
  }

  currentOrderStatusId.value = selectedOrderDetail.value.status_id;
  showAddStatusLogDialog.value = true;
  // 重置表单
  newStatusLogForm.value = {
    status: '',
    start_time: '',
    expected_completion_time: ''
  };
};

// 添加状态日志
const addStatusLog = async () => {
  if (!newStatusLogForm.value.status) {
    ElMessage.error('请输入状态名称');
    return;
  }

  try {
    const response: any = await request.post('/api/order-status-logs', {
      order_status_id: currentOrderStatusId.value,
      status: newStatusLogForm.value.status,
      start_time: newStatusLogForm.value.start_time,
      expected_completion_time: newStatusLogForm.value.expected_completion_time
    });

    if (response) {
      ElMessage.success('状态日志添加成功');
      statusLogs.value.push(response);
      showAddStatusLogDialog.value = false;

      // 重新加载订单状态详情
      await loadOrderStatusDetails();
    }
  } catch (error) {
    console.error('添加状态日志失败:', error);
    ElMessage.error('添加状态日志失败');
  }
};

// 添加状态任务
const addStatusTask = async (statusLogId: number) => {
  try {
    const response: any = await request.post('/api/order-status/' + currentOrderStatusId.value + '/tasks', {
      status_log_id: statusLogId,
      name: '新任务',
      category: '默认分类',
      description: '请输入任务描述'
    });

    if (response) {
      ElMessage.success('任务添加成功');
      tasks.value.push(response);
    }
  } catch (error) {
    console.error('添加任务失败:', error);
    ElMessage.error('添加任务失败');
  }
};

// 更新状态任务
const updateStatusTask = async (task: any) => {
  try {
    await request.put(`/api/order-status/${currentOrderStatusId.value}/tasks/${task.id}`, {
      is_completed: task.is_completed,
      name: task.name,
      description: task.description
    });

    ElMessage.success('任务更新成功');
  } catch (error) {
    console.error('更新任务失败:', error);
    ElMessage.error('更新任务失败');
  }
};

// 编辑状态任务字段
const editStatusTaskField = async (task: any, field: string) => {
  // 这里可以使用Element Plus的Input组件来实现内联编辑
  // 但为了简化，我们先保持使用prompt
  const newValue = prompt(`请输入新的${field === 'name' ? '名称' : '描述'}:`, task[field]);
  if (newValue !== null && newValue !== task[field]) {
    task[field] = newValue;
    await updateStatusTask(task);
  }
};

// 添加照片到任务
const addPhotoToTask = async (taskId: number) => {
  // 创建一个隐藏的文件输入元素
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = async (event: any) => {
    const file = event.target.files[0];
    if (!file) return;

    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      ElMessage.error('请选择图片文件');
      return;
    }

    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_id', taskId.toString());

    try {
      const response: any = await request.post(`/api/order-status/${currentOrderStatusId.value}/tasks/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response) {
        ElMessage.success('图片上传成功');

        // 更新对应任务的图片路径
        const task = tasks.value.find((t: any) => t.id === taskId);
        if (task) {
          if (task.photo_path) {
            task.photo_path = `${task.photo_path},${response.file_url}`;
          } else {
            task.photo_path = response.file_url;
          }
        }
      }
    } catch (error) {
      console.error('图片上传失败:', error);
      ElMessage.error('图片上传失败');
    }
  };
  input.click();
};

// 加载订单状态详情
const loadOrderStatusDetails = async () => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    return;
  }

  const orderId = selectedOrderDetail.value?.id || selectedOrder.value?.id;
  if (!orderId) {
    return;
  }

  try {
    const response: any = await request.get('/api/order-status', {
      params: { order_id: orderId }
    });

    if (response) {
      // 设置当前订单状态ID
      currentOrderStatusId.value = response.id;

      // 获取完整的订单状态详情（包含状态日志和任务）
      const detailResponse: any = await request.get(`/api/order-status/${response.id}`);

      if (detailResponse) {
        // 获取所有状态日志
        statusLogs.value = detailResponse.status_logs || [];

        // 提取所有任务项
        tasks.value = detailResponse.tasks.flatMap((category: any) => category.children || []);
      }
    }
  } catch (error) {
    console.error('加载订单状态详情失败:', error);
  }
};

// ===================== 生命周期 =====================
// 组件挂载
onMounted(async () => {
  window.addEventListener('resize', handleResize);
  await fetchUserInfo();
  fetchOrders();
});

// 组件卸载
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// ===================== 路由 =====================
</script>

<style scoped>
/* 基础容器样式 */
.order-status-container {
  padding: 10px;
}

/* 图标样式 */
.el-icon {
  padding: 8px 15px;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}

.btn-add-status {
  background-color: #33c44b;
}

.btn-add-photo {
  color: gray;
  background-color: rgba(156, 156, 156, 0.1);
  font-size: 16px;
  margin-left: 15px;
}

.btn-add-task {
  padding: 6px 12px;
  color: gray;
  background-color: rgba(156, 156, 156, 0.3);
  font-size: 16px;
  margin-left: 15px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 进度容器 */
.progress-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  padding: 5px 10px;
  background-color: rgba(156, 156, 156, 0.1);
  border-radius: 5px;
}

/* 订单列表区域 */
.order-list-section {
  margin-bottom: 15px;
}

/* 进度文本 */
.progress-text {
  font-size: 12px;
  color: #606266;
  text-align: center;
  width: 100%;
}

/* 分页样式 */
.pagination {
  margin-top: 15px;
  text-align: center;
}

/* 订单信息卡片 */
.order-info-card {
  margin-bottom: 15px;
}

/* 订单信息容器 */
.order-info-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 底部操作区域 */
.bottom-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

/* 操作按钮组 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

/* 进度汇总文本 */
.progress-summary {
  font-size: 14px;
  color: #606266;
}

/* 图片预览对话框样式 */
.image-preview-dialog .el-dialog {
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview-dialog .el-dialog__body {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 可点击编辑字段样式 */
.clickable-field {
  cursor: pointer;
  border: 1px dashed transparent;
  padding: 2px;
  border-radius: 3px;
}

.clickable-field:hover {
  border: 1px dashed #409eff;
  background-color: #f5f7fa;
}

/* 全屏加载遮罩 */
.fullscreen-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.loading-icon {
  font-size: 24px;
  animation: rotating 2s linear infinite;
  margin-bottom: 10px;
  display: block;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 表格行样式 */
:deep(.el-table .el-table__row) {
  cursor: pointer;
}

:deep(.el-table .el-table__row:hover > td) {
  background-color: #f5f7fa;
}

/* ===================== 移动端适配 ===================== */
@media (min-width: 768px) {
  .order-status-container {
    padding: 20px;
  }

  .order-list-section {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
  }

  .order-info-card {
    margin-bottom: 20px;
  }

  .bottom-actions {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding-top: 20px;
  }

  .action-buttons {
    gap: 10px;
    justify-content: flex-start;
  }
}

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

  .el-table {
    font-size: 12px;
  }

  .el-table th,
  .el-table td {
    padding: 4px 0;
  }

  .el-button {
    font-size: 12px;
    padding: 6px 12px;
  }

  .el-radio {
    font-size: 12px;
  }

  .el-input__inner {
    font-size: 12px;
  }

  .action-buttons {
    flex-wrap: nowrap;
    overflow-x: auto;
    justify-content: flex-start;
    gap: 6px;
  }
}
</style>