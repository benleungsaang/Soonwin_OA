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
                @click="goToReport(scope.row)"
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
              <!-- <el-descriptions-item label="当前进度">{{ formatDate((selectedOrderDetail || selectedOrder).ship_time) }}</el-descriptions-item> -->
              <el-descriptions-item :span="2" label="添加进度">
                <el-icon class="btn-add-status" @click="openAddStatusLogDialog"><Plus /></el-icon>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <!-- 订单状态日志卡片 -->
        <el-card body-style="padding:8px;" v-for="(statusLog, logIndex) in statusLogs" :key="statusLog.id" class="status-log-card">
          <template #header>
            <div class="card-header status-header" >

              <div style="display: flex;gap: 20px;">
                  <span class="clickable-field card-title" @click.stop="openEditFieldDialog(statusLog, 'status', '修改状态', updateStatusLogStatus)">{{ statusLog.status }}</span>
                <div class="progress-container">
                  <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                    <div :style="{width: getStatusLogProgress(statusLog.id) + '%', height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                  </div>
                  <div class="progress-text" style="margin-top: 2px;">
                    {{ getStatusLogCompletionInfo(statusLog.id) }}
                  </div>
                </div>
              </div>

              <div>
                <el-icon class="btn-add-task" @click.stop="addStatusTask(statusLog.id)"><Plus /></el-icon>
                <el-icon class="btn-del-status" @click.stop="deleteStatusLog(statusLog.id)"><Delete /></el-icon>
                <el-icon @click.stop="toggleStatusLog(statusLog.id)" :class="['expand-icon', {'expanded': expandedStatusLogs[statusLog.id] === true}]"><ArrowRight /></el-icon>
              </div>

            </div>
          </template>
          <div class="order-info-container" v-show="expandedStatusLogs[statusLog.id] === true">
            <el-descriptions  class="sub-card"
              v-for="(statusTask, taskIndex) in getStatusLogTasks(statusLog.id)"
              :key="statusTask.id"
              direction="vertical"
              :column="3"
              border
            >
              <el-descriptions-item :span="3" label="照片">
                <div class="task-img-container">
                  <template v-if="statusTask.thumb_photo_path">
                      <div v-for="(image, imgIndex) in statusTask.thumb_photo_path.split(',')" :key="imgIndex" style="display: flex; margin-right: 10px;">
                        <el-image
                          :src="image"
                          :preview-src-list="statusTask.photo_path.split(',')"
                          :initial-index="imgIndex"
                          preview-teleported
                          close-on-press-esc
                          hide-on-click-modal
                          class="thumb-img"
                        />
                      </div>
                    </template>
                  <el-icon class="btn-add-photo" @click="addPhotoToTask(statusTask.id)"><Camera /></el-icon>
                  <el-input style="margin-left: 5px;width:130px;" @paste="(e) => handleInputPaste(e, statusTask.id)" placeholder="粘贴图片(Ctrl+V)"></el-input>
                </div>
              </el-descriptions-item>
              <el-descriptions-item :span="1" width="150px" label="项目名" >
                <span class="clickable-field" @click.stop="openEditFieldDialog(statusTask, 'name', '修改任务名称', updateStatusTask)">{{ statusTask.name || '点击添加标题' }}</span>
              </el-descriptions-item>
              <el-descriptions-item :span="1" label="备注信息" >
                <span class="clickable-field" @click.stop="openEditFieldDialog(statusTask, 'description', '修改任务描述', updateStatusTask)">{{ statusTask.description || '点击添加描述' }}</span>
              </el-descriptions-item>
              <el-descriptions-item :span="1" width="250px" label="操作" >
                 <el-switch
                  v-model="statusTask.is_completed"
                  size="large"
                  active-text="完成"
                  inactive-text="未完成"
                  @change="updateStatusTask(statusTask)"
                />
                <el-icon class="btn-del-task" @click="deleteTask(statusTask.task_id)"><Delete /></el-icon>
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
            <el-button  @click="handleCloseOrderDetailDialog">
              关闭
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

    <!-- 添加任务模态框 -->
    <el-dialog
      v-model="showAddTaskDialog"
      title="添加任务"
      width="400px"
    >
      <el-form :model="newTaskForm" label-width="120px">
        <el-form-item label="任务名称" required>
          <el-input v-model="newTaskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="newTaskForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddTaskDialog = false">取消</el-button>
          <el-button type="primary" @click="addTask">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 通用修改字段模态框 -->
    <el-dialog
      v-model="editFieldDialog.visible"
      :title="editFieldDialog.title"
      width="400px"
    >
      <el-input
        v-model="editFieldDialog.value"
        :type="'textarea'"
        :rows="4"
        :placeholder="`请输入${editFieldDialog.title}`"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editFieldDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveFieldEdit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 图片预览确认弹窗 -->
    <el-dialog
      v-model="previewImageDialogVisible"
      title="剪贴板图片预览"
      width="50%"
      :before-close="handleDialogClose"
    >
      <div style="text-align: center; padding: 20px;">
        <el-image
          v-if="clipboardImageUrl"
          :src="clipboardImageUrl"
          style="max-width: 100%; max-height: 400px;"
          fit="contain"
        />
        <div v-else style="color: #999; padding: 50px;">未检测到剪贴板中的图片</div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="previewImageDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmUploadClipboardImage">确认上传</el-button>
        </span>
      </template>
    </el-dialog>

  </div>

</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, List, DocumentCopy, Camera, Delete, ArrowRight } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';
import { cursorTo } from 'node:readline';

// 获取路由实例
const router = useRouter();

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

// 任务相关
const newTaskForm = ref({
  name: '',
  description: '',
  category: '',
  status_log_id: null
});
const currentTaskStatusLogId = ref(null);
const showAddTaskDialog = ref(false);

// 用于跟踪状态日志的展开/折叠状态
const expandedStatusLogs = ref<{[key: number]: boolean}>({});

// 剪贴板图片相关
const previewImageDialogVisible = ref(false); // 预览弹窗显示状态
const clipboardImageUrl = ref(''); // 剪贴板图片预览URL
const clipboardImageFile = ref<File | null>(null); // 剪贴板图片文件对象
const currentClipboardTaskId = ref<number | null>(null); // 当前处理的taskId
const lastClipboardImage = ref<File | null>(null); // 最近一次剪贴板操作的图片


// ===================== 计算属性 =====================
// 判断是否为移动端
const isMobile = computed(() => windowWidth.value < 768);


// 获取用户角色
const userRole = ref('');

// 切换状态日志的展开/折叠状态
const toggleStatusLog = (statusLogId: number) => {
  const currentState = expandedStatusLogs.value[statusLogId];
  expandedStatusLogs.value[statusLogId] = !(currentState === true);
};

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
// 通用修改字段相关
const editFieldDialog = ref({
  visible: false,
  title: '',
  value: '',
  object: null,
  field: '',
  updateCallback: null
});

// 通用修改字段函数
const openEditFieldDialog = (obj: any, field: string, title: string, updateCallback?: any) => {
  editFieldDialog.value = {
    visible: true,
    title: title,
    value: obj[field] || '',
    object: obj,
    field: field,
    updateCallback: updateCallback
  };
};

// 更新状态日志状态
const updateStatusLogStatus = async (statusLog: any, field: string, newValue: string) => {
  try {
    const payload: any = {};
    payload[field] = newValue;

    const response: any = await request.put(`/api/order-status-logs/${statusLog.id}`, payload);

    if (response && response.code === 200) {
      ElMessage.success('状态日志更新成功');
    }
  } catch (error) {
    console.error('更新状态日志失败:', error);
    ElMessage.error('更新状态日志失败');
    // 如果API调用失败，回滚本地更改
    statusLog[field] = editFieldDialog.value.value; // 原来的值
  }
};

// 保存修改的字段
const saveFieldEdit = async () => {
  if (!editFieldDialog.value.object || !editFieldDialog.value.field) {
    ElMessage.error('缺少对象或字段信息');
    return;
  }

  const obj = editFieldDialog.value.object;
  const field = editFieldDialog.value.field;
  const newValue = editFieldDialog.value.value;
  const updateCallback = editFieldDialog.value.updateCallback;

  // 更新对象的字段值
  obj[field] = newValue;

  // 如果有自定义回调函数，则执行它
  if (updateCallback && typeof updateCallback === 'function') {
    await updateCallback(obj, field, newValue);
  }

  // 关闭对话框
  editFieldDialog.value.visible = false;
  ElMessage.success(`${editFieldDialog.value.title}修改成功`);
};

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

// 跳转到订单进度报告页面
const goToReport = (row: any) => {
  // 检查是否有订单状态ID
  if (row.status_id) {
    // 在新标签页中打开报告页面
    const url = `/order-status-report?orderId=${row.status_id}`;
    window.open(url, '_blank');
  } else {
    ElMessage.warning('该订单尚无状态记录，无法生成报告');
  }
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
  // 从statusLogs中查找对应的状态日志，获取其status作为category
  const statusLog = statusLogs.value.find((log: any) => log.id === statusLogId);
  const category = statusLog ? statusLog.status : '默认分类';

  // 设置新任务表单的初始值
  newTaskForm.value = {
    name: '新任务',
    description: '请输入任务描述',
    category: category,
    status_log_id: statusLogId
  };

  // 显示添加任务模态框
  showAddTaskDialog.value = true;
  currentTaskStatusLogId.value = statusLogId;
};

// 添加任务
const addTask = async () => {
  if (!newTaskForm.value.name || newTaskForm.value.name.trim() === '') {
    ElMessage.warning('任务名称不能为空');
    return;
  }

  try {
    const response: any = await request.post('/api/order-status/' + currentOrderStatusId.value + '/tasks', {
      status_log_id: currentTaskStatusLogId.value,
      name: newTaskForm.value.name.trim(),
      category: newTaskForm.value.category,
      description: newTaskForm.value.description
    });

    if (response) {
      ElMessage.success('任务添加成功');
      // 将服务器返回的任务对象转换为前端期望的结构
      const taskItem = {
        task_id: response.id,                 // 使用id作为task_id
        id: response.id,                      // 保留id
        name: response.name,
        category: response.category,
        description: response.description,
        is_completed: response.is_completed,
        photo_path: response.photo_path,
        thumb_photo_path: response.thumb_photo_path,
        status_log_id: response.status_log_id,
        create_time: response.create_time,
        update_time: response.update_time,
        sort_order: response.sort,           // 将sort转换为sort_order
        parent_id: response.status_log_id,   // 将status_log_id作为parent_id
        item_type: 'sub'                     // 固定为sub类型
      };
      tasks.value.push(taskItem);

      // 关闭模态框并重置表单
      showAddTaskDialog.value = false;
      newTaskForm.value = {
        name: '',
        description: '',
        category: '',
        status_log_id: null
      };
    }
  } catch (error) {
    console.error('添加任务失败:', error);
    ElMessage.error('添加任务失败');
  }
};

// 更新状态任务
const updateStatusTask = async (task: any) => {
  try {
    const response: any = await request.put(`/api/order-status/${currentOrderStatusId.value}/tasks/${task.id || task.task_id}`, {
      is_completed: task.is_completed,
      name: task.name,
      description: task.description
    });
    if (response) {
      // 找到对应的任务并更新其数据
      const taskIndex = tasks.value.findIndex((t: any) => t.id === (task.id || task.task_id));
      if (taskIndex > -1) {
        // 将服务器返回的任务对象转换为前端期望的结构
        const taskItem = {
          task_id: response.id,
          id: response.id,
          name: response.name,
          category: response.category,
          description: response.description,
          is_completed: response.is_completed,
          photo_path: response.photo_path,
          thumb_photo_path: response.thumb_photo_path,
          status_log_id: response.status_log_id,
          create_time: response.create_time,
          update_time: response.update_time,
          sort_order: response.sort,
          parent_id: response.status_log_id,
          item_type: 'sub'
        };
        tasks.value[taskIndex] = taskItem;
      }
      ElMessage.success('任务更新成功');
    }

  } catch (error) {
    console.error('更新任务失败:', error);
    ElMessage.error('更新任务失败');
  }

};

// 添加照片到任务
const addPhotoToTask = async (taskId: number, file?: File) => {
  // 如果传入了文件参数（如剪贴板图片），则直接上传
  if (file) {
    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      ElMessage.error('请选择图片文件');
      return;
    }

    // 验证文件类型（参考React版本的扩展名校验）
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];

    if (!allowedImageExts.includes(ext)) {
      ElMessage.error(`不支持的图片格式：${ext}，支持的格式：${allowedImageExts.join(', ')}`);
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

        // 重新加载任务列表以获取最新的图片路径（因为需要重新构建任务对象结构）
        if (selectedOrderDetail.value || selectedOrder.value) {
          const orderId = selectedOrderDetail.value?.id || selectedOrder.value?.id;
          if (orderId) {
            await loadOrderStatusDetails();
          }
        }
      }
    } catch (error) {
      console.error('图片上传失败:', error);
      ElMessage.error('图片上传失败');
    }
  } else {
    // 如果没有传入文件参数，则使用文件选择器
    // 创建一个隐藏的文件输入元素
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (event: any) => {
      const selectedFile = event.target.files[0];
      if (!selectedFile) return;

      // 检查文件类型
      if (!selectedFile.type.startsWith('image/')) {
        ElMessage.error('请选择图片文件');
        return;
      }

      // 验证文件类型（参考React版本的扩展名校验）
      const ext = selectedFile.name.split('.').pop()?.toLowerCase() || '';
      const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];

      if (!allowedImageExts.includes(ext)) {
        ElMessage.error(`不支持的图片格式：${ext}，支持的格式：${allowedImageExts.join(', ')}`);
        return;
      }

      // 创建FormData对象
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('task_id', taskId.toString());

      try {
        const response: any = await request.post(`/api/order-status/${currentOrderStatusId.value}/tasks/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        if (response) {
          ElMessage.success('图片上传成功');

          // 重新加载任务列表以获取最新的图片路径（因为需要重新构建任务对象结构）
          if (selectedOrderDetail.value || selectedOrder.value) {
            const orderId = selectedOrderDetail.value?.id || selectedOrder.value?.id;
            if (orderId) {
              await loadOrderStatusDetails();
            }
          }
        }
      } catch (error) {
        console.error('图片上传失败:', error);
        ElMessage.error('图片上传失败');
      }
    };
    input.click();
  }
};

// 删除状态日志
const deleteStatusLog = async (statusLogId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此状态日志吗？删除后将无法恢复，相关的任务也会被删除。', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    const response: any = await request.delete(`/api/order-status-logs/${statusLogId}`);

    // request.ts会自动解包data，对于DELETE请求，如果成功但data为undefined，
    // 拦截器会返回undefined，所以我们需要特殊处理这种情况
    // 检查请求是否成功完成（没有抛出异常）
    ElMessage.success('状态日志删除成功');
    // 从本地数据中移除该状态日志
    statusLogs.value = statusLogs.value.filter((log: any) => log.id !== statusLogId);
    // 同时移除与该状态日志关联的任务
    tasks.value = tasks.value.filter((task: any) => task.status_log_id !== statusLogId);
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除状态日志失败:', error);
      ElMessage.error('删除状态日志失败');
    }
  }
};

// 删除任务
const deleteTask = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？删除后将无法恢复，相关的图片也会被删除。', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // 先查找任务，支持id和task_id两种查找方式
    let taskIndex = tasks.value.findIndex((task: any) => task.id === taskId);
    if (taskIndex === -1) {
      taskIndex = tasks.value.findIndex((task: any) => task.task_id === taskId);
    }

    if (taskIndex === -1) {
      ElMessage.error('任务不存在');
      return;
    }

    const task = tasks.value[taskIndex];
    const actualTaskId = task.id || task.task_id; // 使用实际的任务ID

    // 尝试从服务器删除
    try {
      await request.delete(`/api/order-status/${currentOrderStatusId.value}/tasks/${actualTaskId}`);

      // 服务器删除成功后，从本地移除任务
      tasks.value.splice(taskIndex, 1);
      ElMessage.success('任务删除成功');
    } catch (serverError) {
      // 检查错误类型
      if (serverError.response && serverError.response.status === 404) {
        // 服务器返回404，说明该任务可能不存在（可能已经被删除或未正确保存）
        // 仍然从本地移除任务
        tasks.value.splice(taskIndex, 1);
        ElMessage.success('任务已从本地移除');
      } else {
        // 其他服务器错误
        console.error('删除任务失败:', serverError);
        ElMessage.error('删除任务失败');
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error);
      ElMessage.error('删除任务失败');
    }
  }
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
      // 获取所有状态日志
      statusLogs.value = response.status_logs || [];
      // 提取所有任务项 - 根据API返回的结构，tasks是按status_log_id分组的类别数组
      // 每个category都有status_log_id和children数组，需要将children中的任务展开并添加对应的status_log_id
      const allTasks: any[] = [];
      response.tasks.forEach((category: any) => {
        const statusLogId = category.status_log_id;
        if (category.children && Array.isArray(category.children)) {
          category.children.forEach((task: any) => {
            // 确保任务项包含status_log_id，用于与状态日志关联
            task.status_log_id = statusLogId;
            // 将服务器返回的任务对象转换为前端期望的结构
            const taskItem = {
              task_id: task.id || task.task_id,             // 使用id作为task_id
              id: task.id || task.task_id,                  // 保留id
              name: task.name,
              category: task.category,
              description: task.description,
              is_completed: task.is_completed,
              photo_path: task.photo_path,
              thumb_photo_path: task.thumb_photo_path,
              status_log_id: task.status_log_id || statusLogId,
              create_time: task.create_time,
              update_time: task.update_time,
              sort_order: task.sort || task.sort_order,     // 支持两种字段名
              parent_id: task.status_log_id || statusLogId, // 将status_log_id作为parent_id
              item_type: task.item_type || 'sub'            // 固定为sub类型或使用原值
            };
            allTasks.push(taskItem);
          });
        }
      });
      tasks.value = allTasks;

      // 初始化状态日志的展开/折叠状态，默认为折叠
      const newExpandedStatusLogs: {[key: number]: boolean} = {};
      statusLogs.value.forEach((log: any) => {
        // 如果之前有保存的状态则使用，否则默认为折叠（false）
        newExpandedStatusLogs[log.id] = expandedStatusLogs.value[log.id] || false;
      });
      expandedStatusLogs.value = newExpandedStatusLogs;
    }
  } catch (error) {
    console.error('加载订单状态详情失败:', error);
  }
};

// ===================== 生命周期 =====================
// 组件挂载
onMounted(async () => {
  window.addEventListener('resize', handleResize);
  // 添加粘贴事件监听器，用于捕获剪贴板中的图片
  window.addEventListener('paste', handlePasteEvent);
  await fetchUserInfo();
  fetchOrders();
});

// 组件卸载
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  // 移除粘贴事件监听器
  window.removeEventListener('paste', handlePasteEvent);
});

// 粘贴事件处理器
const handlePasteEvent = (e: ClipboardEvent) => {
  try {
    let file = null;

    // 方案1：使用 clipboardData.items
    if (e.clipboardData && e.clipboardData.items) {
      for (let i = 0; i < e.clipboardData.items.length; i++) {
        const item = e.clipboardData.items[i];
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          file = item.getAsFile();
          break;
        }
      }
    }

    // 方案2：使用 clipboardData.files
    if (!file && e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      const candidate = e.clipboardData.files[0];
      if (candidate.type.startsWith('image/')) {
        file = candidate;
      }
    }

    if (file) {
      // 验证文件类型
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];

      if (allowedImageExts.includes(ext)) {
        // 保存最近的剪贴板图片
        lastClipboardImage.value = file;
      }
    }
  } catch (error) {
    console.warn('处理粘贴事件时出错:', error);
  }
};

// ===================== 剪贴板功能 =====================

/**
 * 关闭弹窗时清理URL
 */
const handleDialogClose = () => {
  // 释放创建的URL对象，避免内存泄漏
  if (clipboardImageUrl.value) {
    URL.revokeObjectURL(clipboardImageUrl.value);
    clipboardImageUrl.value = '';
  }
  clipboardImageFile.value = null;
  previewImageDialogVisible.value = false;
};

/**
 * 从剪贴板读取图片（参考React版本优化，增加多方案兼容）
 */
const pasteImageFromClipboard = async (taskId: number) => {
  try {
    let file = null;

    // 首先尝试使用全局监听器捕获的图片
    if (lastClipboardImage.value) {
      file = lastClipboardImage.value;
      // 使用后清除，避免重复使用
      lastClipboardImage.value = null;
    }

    // 如果全局监听器没有捕获到图片，则尝试使用 Clipboard API
    if (!file) {
      // 方案1：优先使用 Clipboard API (现代浏览器)
      try {
        if (navigator.clipboard && window.ClipboardItem) {
          const clipboardItems = await navigator.clipboard.read();
          // 遍历剪贴板项查找图片
          for (const item of clipboardItems) {
            const types = item.types;
            for (const type of types) {
              if (type.startsWith('image/')) {
                const blob = await item.getType(type);
                // 创建File对象，包含时间戳避免重名
                const ext = type.split('/')[1];
                file = new File([blob], `paste-${Date.now()}.${ext}`, {
                  type: blob.type
                });
                break;
              }
            }
            if (file) break;
          }
        }
      } catch (clipboardApiError) {
        console.warn('Clipboard API 访问失败，尝试备用方案:', clipboardApiError);
      }
    }

    // 未找到图片，提示用户
    if (!file) {
      ElMessage.warning('剪贴板中未检测到图片，请先复制图片后再尝试\n或使用 Ctrl+V 快捷键复制图片');
      return;
    }

    // 验证文件类型（参考React版本的扩展名校验）
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];

    if (!allowedImageExts.includes(ext)) {
      ElMessage.error(`不支持的图片格式：${ext}，支持的格式：${allowedImageExts.join(', ')}`);
      return;
    }

    // 存储文件对象并创建预览URL
    clipboardImageFile.value = file;
    clipboardImageUrl.value = URL.createObjectURL(file);

    // 记录当前处理的taskId
    currentClipboardTaskId.value = taskId;

    // 打开预览弹窗
    previewImageDialogVisible.value = true;

  } catch (error) {
    console.error('读取剪贴板图片失败：', error);

    // 分类处理错误提示
    if (error.name === 'NotAllowedError') {
      ElMessage.error('请允许浏览器访问剪贴板权限后重试');
    } else if (error.name === 'NotFoundError') {
      ElMessage.warning('剪贴板中未找到图片');
    } else {
      ElMessage.error('读取剪贴板图片失败：' + error.message);
    }
  }
};

/**
 * 处理输入框的粘贴事件
 */
const handleInputPaste = (e: ClipboardEvent, taskId: number) => {
  try {
    let file = null;

    // 方案1：使用 clipboardData.items
    if (e.clipboardData && e.clipboardData.items) {
      for (let i = 0; i < e.clipboardData.items.length; i++) {
        const item = e.clipboardData.items[i];
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          file = item.getAsFile();
          break;
        }
      }
    }

    // 方案2：使用 clipboardData.files
    if (!file && e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      const candidate = e.clipboardData.files[0];
      if (candidate.type.startsWith('image/')) {
        file = candidate;
      }
    }

    if (file) {
      // 验证文件类型
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];

      if (allowedImageExts.includes(ext)) {
        // 直接设置图片文件和任务ID，并弹出预览框
        clipboardImageFile.value = file;
        clipboardImageUrl.value = URL.createObjectURL(file);
        currentClipboardTaskId.value = taskId;
        previewImageDialogVisible.value = true;
        ElMessage.success(`已检测到图片: ${file.name}，正在预览...`);
      } else {
        ElMessage.warning(`检测到文件但格式不支持: ${ext}，仅支持: ${allowedImageExts.join(', ')}`);
      }
    } else {
      // 检查是否是文本内容
      const pastedText = e.clipboardData?.getData('text') || '';
      if (pastedText) {
        ElMessage.info('检测到文本内容，此功能主要用于图片粘贴');
      } else {
        ElMessage.warning('剪贴板中未检测到图片');
      }
    }
  } catch (error) {
    console.warn('处理粘贴事件时出错:', error);
    ElMessage.error('处理粘贴事件失败');
  }
};

/**
 * 确认上传剪贴板图片
 */
const confirmUploadClipboardImage = async () => {
  if (!clipboardImageFile.value) {
    ElMessage.warning('没有可上传的图片');
    previewImageDialogVisible.value = false;
    return;
  }

  if (!currentClipboardTaskId.value) {
    ElMessage.error('未指定上传目标任务');
    previewImageDialogVisible.value = false;
    return;
  }

  try {
    // 使用现有的addPhotoToTask方法上传剪贴板图片
    await addPhotoToTask(currentClipboardTaskId.value, clipboardImageFile.value);

    ElMessage.success('图片上传成功');
    previewImageDialogVisible.value = false;

    // 清理资源
    handleDialogClose();

  } catch (error) {
    console.error('图片上传失败：', error);
    ElMessage.error('图片上传失败：' + error.message);
  }
};
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

.btn-del-status {
  background-color: #f56c6c;
  padding: 6px 12px;
  color: rgb(255, 255, 255);
  font-size: 16px;
  margin-left: 15px;
}

.btn-del-task {
  background-color: #ff8888;
  padding: 5px 10px;
  color: rgb(255, 255, 255);
  font-size: 12px;
  margin-left: 25px;
}

.btn-del-photo{
  background-color: #f56c6c;
  padding: 4px 8px;
  color: rgb(255, 255, 255);
  font-size: 14px;
  margin-left: 5px;
  border-radius: 3px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-header {
  display: flex;
  justify-content: space-between;
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

.el-card {
  margin-bottom: 10px;
}

.sub-card {
  background-color: rgba(216, 213, 255, 0.1);
  border:rgba(0, 0, 0, 0.1) solid 1px;
  padding: 15px;
  border-radius: 3px;

}

.task-img-container {
  display: flex;
  align-items: center;
  justify-content: flex-start; /* 内容靠左 */
  overflow-x: auto;
  white-space: nowrap;
  padding: 5px 10px;
  border:rgba(167, 167, 167, 0.1) solid 1px;
  background-color: rgba(167, 167, 167, 0.1);
  border-radius: 2px;
}

/* 状态日志卡片 */
.status-log-card {
  margin-bottom: 15px;
}

.status-log-card .el-card__header {
  cursor: pointer;
  padding: 12px 20px;
}

.status-log-card .el-card__body {
  padding: 15px;
}

/* 展开/折叠图标 */
.expand-icon {
  transition: transform 0.3s;
  margin:0px 25px;
  padding: 15px 5px;
  color: black;
  cursor: pointer;
  background-color: rgba(0, 0, 0, 0.1);
}

.expand-icon:hover{
  background-color: #ebeef5;
}

.expand-icon.expanded {
  transform: rotate(90deg);
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

/* 移动端适配 */
@media (min-width: 768px) {
  .status-log-card .el-card__header {
    padding: 12px 20px;
  }

  .status-log-card .el-card__body {
    padding: 20px;
  }
}

.card-title{
  font-weight: 400;
  font-size: 20px;
}

.thumb-img{
  /* padding:2px; */
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: 5px;
  border: rgba(123, 175, 235, 0.2) solid 3px;
}
</style>