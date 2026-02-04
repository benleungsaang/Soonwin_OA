<template>
  <div class="order-status-container">
    <CommonHeader title="订单进度" />

    <!-- 订单列表 -->
    <div class="order-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>待处理订单列表</span>
          </div>
        </template>

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
              <div style="cursor: pointer; display: flex; flex-direction: column; align-items: center;" @click.stop="showOrderDetails(scope.row)">
                <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                  <div :style="{width: `${getOrderStatusProgress(scope.row.id)}%`, height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
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

    <!-- 订单进度详情弹窗（整合了订单详情和进度管理） -->
    <el-dialog
      v-model="orderDetailDialogVisible"
      :title="`订单进度详情 - ${selectedOrderDetail?.contract_no || selectedOrder?.contract_no || ''}`"
      :width="isMobile ? '95%' : '80%'"
      :before-close="handleCloseOrderDetailDialog"
    >
      <div v-if="selectedOrderDetail || selectedOrder">
        <!-- 订单基础信息 -->
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

            <el-descriptions
              title="当前进度"
              border
            >
              <el-descriptions-item label="当前进度">{{ formatDate((selectedOrderDetail || selectedOrder).ship_time) }}</el-descriptions-item>
              <el-descriptions-item label="添加进度"><el-icon class="btn-add-status"><Plus /></el-icon></el-descriptions-item>
            </el-descriptions>

            <!-- 订单状态和时间选择器 -->
            <!-- <div class="status-controls">
                <span>订单当前进度：{{ OrderStatusLog.status || '无' }}</span>
            </div> -->
          </div>
        </el-card>
        <!-- 新订单状态展示框 -->
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

        <!-- 任务项区域 -->
        <el-card class="status-tasks-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span style="font-size: 30px;">任务项</span>
              <div>
                <el-button
                  type="danger"
                  style="font-size: 20px; padding: 15px; margin-right: 10px;"
                  @click="clearAllTasks"
                >
                  <el-icon><Delete /></el-icon> 清空任务项
                </el-button>
                <el-button
                  type="success"
                  style="font-size: 20px; padding: 15px;"
                  @click="showAddTaskDialog('category')"
                >
                  <el-icon><Plus /></el-icon> 添加类别
                </el-button>
              </div>
            </div>
          </template>

          <!-- 任务项列表 -->
          <div v-for="category in groupedTasks" :key="category.id" class="status-category">
            <div class="category-item">
              <div class="category-header" @click="toggleExpand(category.id)" style="cursor: pointer;">
                <div class="category-title-container">
                  <div style="display: flex; align-items: center;">
                    <el-icon :class="{'is-expanded': isTaskExpanded(category.id)}" style="margin-right: 8px; transition: transform 0.2s;">
                      <ArrowRight />
                    </el-icon>
                    <span
                      v-if="!category.isEditing"
                      class="category-title"
                      @click.stop="startEditing(category, 'category')"
                      style="cursor: pointer;"
                    >
                      {{ category.category }}
                    </span>
                  </div>
                  <div class="category-progress">
                    <div style="margin-left: 10px; width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                      <div :style="{width: `${category.progress}%`, height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                    </div>
                    <span class="progress-text">{{ getCategoryTaskFraction(category) }}</span>
                  </div>
                </div>
                <!-- 类别的标题后的删除及添加按钮 -->
                <el-button
                  type="danger"
                  size="small"
                  @click.stop="deleteTask(category)"
                  style="margin-right: 10px;"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  @click.stop="addSubTaskToCategory(category.id, category.category)"
                  style="margin-right: 10px;"
                >
                  <el-icon><Plus /></el-icon>
                </el-button>
              </div>
              <!-- 子任务内容，只有在展开时才显示 -->
              <div v-show="isTaskExpanded(category.id)" class="sub-tasks">
                <div
                  v-for="subTask in category.children"
                  :key="subTask.id"
                  class="sub-task"
                >
                  <div class="sub-task-header">
                    <div class="sub-task-name-container">
                      <span
                        v-if="!subTask.isEditing"
                        class="sub-task-name"
                        @click="startEditing(subTask, 'sub')"
                        style="cursor: pointer;"
                      >
                        {{ subTask.name }}
                      </span>
                    </div>
                    <div class="sub-task-actions">
      <el-switch
        v-model="subTask.is_completed"
        active-text="完成"
        inactive-text="未完成"
        @change="updateStatusTask(subTask)"
      />
                      <!-- 小项的标题后的删除按钮 -->
                      <el-button
                        type="danger"
                        size="small"
                        @click="deleteTask(subTask)"
                        style="margin-left:10px;"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div class="sub-task-content">
                    <InspectionImageUpload
                      v-if="subTask.is_completed"
                      :inspection-result="subTask.is_completed ? 'normal' : 'pending'"
                      :photo-path="subTask.photo_path"
                      :description="subTask.description"
                      @update:photo-path="(value) => { subTask.photo_path = value; updateStatusTask(subTask); }"
                      @update:description="(value) => { subTask.description = value; updateStatusTask(subTask); }"
                      @photo-updated="() => updateStatusTask(subTask)"
                      @preview-image="showImagePreview"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- 添加的独立任务项（没有类别的） -->
          <div v-for="task in standaloneTasks" :key="task.id" class="standalone-task">
            <div class="sub-task-header">
              <div class="sub-task-name-container">
                <span
                  v-if="!task.isEditing"
                  class="sub-task-name"
                  @click="startEditing(task, 'sub')"
                  style="cursor: pointer;"
                >
                  {{ task.name }}
                </span>
                <el-input
                  v-else
                  v-model="task.editingValue"
                  @blur="finishEditing(task, 'sub')"
                  @keyup.enter="finishEditing(task, 'sub')"
                />
              </div>
              <div class="sub-task-actions">
                <el-switch
                  v-model="task.is_completed"
                  active-text="完成"
                  inactive-text="未完成"
                  @change="updateStatusTask(task)"
                />
              </div>
            </div>

            <div class="sub-task-content" v-if="task.is_completed">
              <InspectionImageUpload
                :inspection-result="task.is_completed ? 'normal' : 'pending'"
                :photo-path="task.photo_path"
                :description="task.description"
                @update:photo-path="(value) => { task.photo_path = value; updateStatusTask(task); }"
                @update:description="(value) => { task.description = value; updateStatusTask(task); }"
                @photo-updated="() => updateStatusTask(task)"
                @preview-image="showImagePreview"
              />
            </div>
          </div>

          <!-- 在所有大项最后添加+按钮 -->
          <div class="add-new-category-section">
            <el-button
              size="default"
              @click="addNewCategory"
              style="width: 98%;
              border-radius: 5px;
              border:1px solid #d3dce6;
              padding:10px; margin-top: 5px;font-size: 25px;  background-color:#ffffff; width: 100%;"
            >
              <el-icon><Plus /></el-icon> 添加新类别
            </el-button>
          </div>
        </el-card>
        <!-- 底部操作区域 -->
        <div class="bottom-actions">
          <div class="progress-summary">
            <p>任务项进度：{{ realTimeProgress.completed_tasks }} / {{ realTimeProgress.total_tasks }}</p>
          </div>
          <div class="action-buttons">
            <el-button
              type="success"
              @click="generateReport"
            >
              <el-icon style="margin-right: 5px;"><List /></el-icon>生成报告
            </el-button>
            <el-button
              type="primary"
              @click="saveAndClose"
            >
              保存
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 添加任务项对话框 -->
    <el-dialog
      v-model="addTaskDialogVisible"
      title="添加任务项"
      :width="isMobile ? '90%' : '500px'"
      :before-close="closeAddTaskDialog"
    >
      <el-form :model="newTaskForm" :rules="taskRules" ref="taskFormRef" label-width="100px" @keyup.enter="confirmAddTask">
        <el-form-item label="类型" prop="taskType">
          <el-radio-group v-model="newTaskForm.taskType">
            <el-radio value="category">类别</el-radio>
            <el-radio value="sub">任务</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          label="类别"
          prop="parentCategory"
          v-if="newTaskForm.taskType === 'sub'"
        >
          <el-select
            v-model="newTaskForm.parentCategory"
            placeholder="请选择类别"
            style="width: 100%"
            @keyup.enter="confirmAddTask"
          >
            <el-option
              v-for="item in categories"
              :key="item.id"
              :label="item.category"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          label="名称"
          prop="taskName"
        >
          <el-input
            v-model="newTaskForm.taskName"
            :placeholder="newTaskForm.taskType === 'category' ? '请输入类别名称，如：配件、外观等' : '请输入任务名称，如：部件1、角度1等'"
            required
            @keyup.enter="confirmAddTask"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeAddTaskDialog">取消</el-button>
          <el-button type="primary" @click="confirmAddTask">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改任务项标题对话框 -->
    <el-dialog
      v-model="editTaskTitleDialogVisible"
      :title="titleEditingType === 'category' ? '修改类别标题' : '修改任务标题'"
      :width="isMobile ? '90%' : '500px'"
      :before-close="closeEditTaskTitleDialog"
    >
      <el-input
        v-model="titleEditingValue"
        :placeholder="titleEditingType === 'category' ? '请输入类别标题' : '请输入任务标题'"
        maxlength="200"
        show-word-limit
        @keyup.enter="confirmEditTaskTitle"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeEditTaskTitleDialog">取消</el-button>
          <el-button type="primary" @click="confirmEditTaskTitle">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="imagePreviewVisible"
      :show-close="true"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
      :width="isMobile ? '90%' : 'auto'"
      top="5vh"
      class="image-preview-dialog"
      :fullscreen="isMobile"
    >
      <div style="text-align: center;">
        <img :src="previewImageUrl" style="max-width: 100%; max-height: 80vh; object-fit: contain;" />
      </div>
    </el-dialog>

  </div>

  <!-- 全屏加载提示 -->
  <div v-if="fullScreenLoading" class="fullscreen-loading-overlay">
    <div class="loading-content">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <p>正在上传数据，请稍候...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, onUnmounted } from 'vue';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { Delete, Plus, Close, List, ArrowRight, Loading, Camera } from '@element-plus/icons-vue';
import { uploadFile } from '@/utils/upload';
import InspectionImageUpload from '@/components/InspectionImageUpload.vue';
import CommonHeader from '@/components/CommonHeader.vue';

// 响应式数据
const orders = ref<any[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const detailDialogVisible = ref(false);
const orderDetailDialogVisible = ref(false);
const addTaskDialogVisible = ref(false);
const editTaskTitleDialogVisible = ref(false); // 新增：修改标题对话框
const selectedOrder = ref<any>({});
const selectedOrderDetail = ref<any>(null);
const selectedStatus = ref<any>(null);
const tasks = ref<any[]>([]);
const token = ref(localStorage.getItem('oa_token') || '');
const isEditingMode = ref(false);
const hasUnsavedChangesFlag = ref(false); // 跟踪是否有未保存的更改
const windowWidth = ref(window.innerWidth);
const expandedTasks = ref<Set<number>>(new Set()); // 跟踪展开的类别
const fullScreenLoading = ref(false); // 全屏加载状态

// 订单状态相关

const size = ref<'default' | 'large' | 'small'>('default');

const localCurrentStatus = computed({

  get: () => selectedStatus.value?.current_status || null,

  set: (value) => {

    if (selectedStatus.value) {

      selectedStatus.value.current_status = value;

    }

  }

});

const localCurrentStatusTime = computed({

  get: () => selectedStatus.value?.current_status_time ? new Date(selectedStatus.value.current_status_time) : null,

  set: (value) => {

    if (selectedStatus.value) {

      if (value === null || value === undefined) {

        selectedStatus.value.current_status_time = null;

      } else if (value instanceof Date) {

        selectedStatus.value.current_status_time = value.toISOString().split('T')[0];

      } else {

        selectedStatus.value.current_status_time = value;

      }

    }

  }

});



const selectedStatusValue = computed({



  get: () => {

    // 返回当前状态和时间的组合值

    if (selectedStatus.value) {

      const status = selectedStatus.value.current_status || 1; // 默认为1-下单

      const time = selectedStatus.value.current_status_time || '没有日期';

      return `${status}_${time}`;

    }

    return null;

  },



  set: (value) => {

    if (value && selectedStatus.value) {

      const parts = value.split('_');

      if (parts.length >= 2) {

        const status = parseInt(parts[0]);

        let time = parts.slice(1).join('_');



        selectedStatus.value.current_status = status;

        if (time !== '没有日期') {

          selectedStatus.value.current_status_time = time;

        } else {

          selectedStatus.value.current_status_time = null;

        }

      }

    }

  }

});





const statusOptions = computed(() => {

  const currentTimeValue = selectedStatus.value?.current_status_time || '没有日期';

  return [

    {

      value: 1,

      label: '下单',

      timeDisplay: currentTimeValue,

      combinedValue: `1_${currentTimeValue}`

    },

    {

      value: 2,

      label: '排产',

      timeDisplay: currentTimeValue,

      combinedValue: `2_${currentTimeValue}`

    },

    {

      value: 3,

      label: '完成生产',

      timeDisplay: currentTimeValue,

      combinedValue: `3_${currentTimeValue}`

    },

    {

      value: 4,

      label: '验收阶段',

      timeDisplay: currentTimeValue,

      combinedValue: `4_${currentTimeValue}`

    },

    {

      value: 5,

      label: '发货',

      timeDisplay: currentTimeValue,

      combinedValue: `5_${currentTimeValue}`

    },

  ];

});

const shortcuts = [
  {
    text: '今天',
    value: new Date(),
  },
  {
    text: '昨天',
    value: () => {
      const date = new Date();
      date.setTime(date.getTime() - 3600 * 1000 * 24);
      return date;
    },
  },
  {
    text: '一周前',
    value: () => {
      const date = new Date();
      date.setTime(date.getTime() - 3600 * 1000 * 24 * 7);
      return date;
    },
  },
];

const disabledDate = (time: Date) => {
  return time.getTime() > Date.now();
};

// 标题编辑相关变量
const titleEditingTask = ref<any>(null); // 当前正在编辑的项目
const titleEditingValue = ref(''); // 编辑框的值
const titleEditingType = ref<'category' | 'sub'>('sub'); // 编辑类型

// 新任务项表单
const newTaskForm = ref({
  taskType: 'sub', // 'category' 或 'sub'
  parentCategory: null as number | null,
  taskName: '',
  category: '' // 用于类别的名称
});

// 计算属性：判断是否为移动端
const isMobile = computed(() => {
  return windowWidth.value < 768;
});

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

const taskRules = {
  taskType: [
    { required: true, message: '请选择类型', trigger: 'change' }
  ],
  taskName: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ]
};

// 图片预览相关变量
const imagePreviewVisible = ref(false);
const previewImageUrl = ref('');


// 计算属性
const groupedTasks = computed(() => {
  // 首先获取所有状态日志作为类别
  const statusLogs = [...new Set(tasks.value.filter((task: any) => !task._toBeDeleted).map((task: any) => task.status_log_id))];

  return statusLogs.map((statusLogId: number) => {
    // 根据status_log_id获取该状态下的所有任务
    const children = tasks.value.filter((child: any) =>
      child.status_log_id === statusLogId && child.item_type === 'sub' && !child._toBeDeleted
    );

    // 获取该状态的名称（这里可能需要从别的地方获取，或者使用状态ID作为类别名）
    const firstChild = children.length > 0 ? children[0] : null;
    const category = firstChild ? firstChild.category : `状态阶段 ${statusLogId}`;

    return {
      id: statusLogId, // 使用status_log_id作为类别ID
      category: category,
      item_type: 'category',
      children: children,
      completed_children: children.filter((child: any) => child.is_completed).length,
      total_children: children.length,
      progress: children.length > 0
        ? Math.round((children.filter((child: any) => child.is_completed).length / children.length) * 100)
        : 0
    };
  });
});

const standaloneTasks = computed(() => {
  return tasks.value.filter((task: any) => task.item_type === 'sub' && task.parent_id === null && !task._toBeDeleted);
});

const categories = computed(() => {
  return tasks.value.filter((task: any) => task.item_type === 'category' && !task._toBeDeleted);
});

// 获取用户角色
const userRole = ref('');
const isUserAdmin = computed(() => userRole.value === 'admin');
const isUserGeneral = computed(() => userRole.value !== 'admin');

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



// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
};

// 显示订单详情
const showOrderDetails = async (row: any) => {
  selectedOrderDetail.value = { ...row };
  orderDetailDialogVisible.value = true;

  // 获取或创建进度数据
  await refreshStatusData();
};

// 关闭订单详情对话框
const handleCloseOrderDetailDialog = () => {
  orderDetailDialogVisible.value = false;
  selectedOrderDetail.value = null;
  selectedStatus.value = null;
  tasks.value = [];
};

// 显示添加任务项对话框
const showAddTaskDialog = (type: 'category' | 'sub') => {
  newTaskForm.value = {
    taskType: type,
    parentCategory: null,
    taskName: '',
    category: type === 'category' ? '' : (categories.value.length > 0 ? categories.value[0].category : '')
  };
  // 如果是子任务且有可用的状态日志，自动选择第一个
  if (type === 'sub' && categories.value.length > 0) {
    newTaskForm.value.parentCategory = categories.value[0].id; // 这是status_log_id
  }
  addTaskDialogVisible.value = true;
};


// 关闭添加任务项对话框
const closeAddTaskDialog = () => {
  addTaskDialogVisible.value = false;
};

// 确认添加任务项
const confirmAddTask = () => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    ElMessage.error('请先选择一个订单');
    return;
  }

  // 验证名称输入框不能为空
  if (!newTaskForm.value.taskName || newTaskForm.value.taskName.trim() === '') {
    ElMessage.error('任务名称不能为空');
    return;
  }

  // 如果是子项，验证是否选择了父项（如果存在父项）
  if (newTaskForm.value.taskType === 'sub' && categories.value.length > 0 && !newTaskForm.value.parentCategory) {
    ElMessage.error('请选择类别');
    return;
  }

  const newLocalTask = createNewTask(
    newTaskForm.value.taskType as 'category' | 'sub',
    newTaskForm.value.taskName,
    newTaskForm.value.taskType === 'category' ? newTaskForm.value.taskName : newTaskForm.value.category,
    newTaskForm.value.taskType === 'sub' ? newTaskForm.value.parentCategory : null
  );

  if (!newLocalTask) return;

  // 关闭对话框
  closeAddTaskDialog();
  ElMessage.success('任务项已添加到本地');
};

// 获取进度数据

const refreshStatusData = async () => {

  const orderId = selectedOrderDetail.value ? selectedOrderDetail.value.id : selectedOrder.value.id;
  const orderNo = (selectedOrderDetail.value || selectedOrder.value).order_no;

  try {

    // 检查是否已有进度记录
    let statusId = (selectedOrderDetail.value || selectedOrder.value).status_id;

    if (!statusId) {
      // 优先使用order_no，如果为空则使用order_id
      const params = orderNo ? { order_no: orderNo } : { order_id: orderId };

      const statusRes: any = await request.get('/api/order-status', {
        params: params
      });

      if (statusRes && statusRes.id) { // 如果直接返回了进度记录ID
        statusId = statusRes.id;

        // 更新订单列表中的ID
        if (selectedOrderDetail.value) selectedOrderDetail.value.status_id = statusId;
        if (selectedOrder.value) selectedOrder.value.status_id = statusId;

      } else if (statusRes.list && statusRes.list.length > 0) { // 如果返回了列表
        statusId = statusRes.list[0].id;

        // 更新订单列表中的ID
        if (selectedOrderDetail.value) selectedOrderDetail.value.status_id = statusId;
        if (selectedOrder.value) selectedOrder.value.status_id = statusId;
      }
    }



    if (statusId) {

      const response: any = await request.get(`/api/order-status/${statusId}`);

      selectedStatus.value = response;



      // 初始化tasks并保存原始状态，保留本地新建的项目和删除标记

      // 注意：后端返回的数据中，tasks包含类别和嵌套的子任务，需要扁平化处理

      const serverTasks = [];



      // 遍历后端返回的tasks，包括category和其children

      (response.tasks || []).forEach((task: any) => {

        // 添加类别

        serverTasks.push({

          ...task,

          original_is_completed: task.is_completed,

          original_description: task.description,

          original_photo_path: task.photo_path,

          is_local_new: false // 标记为非本地新建

        });



        // 添加子任务（如果存在）

        if (task.children && Array.isArray(task.children)) {

          task.children.forEach((child: any) => {

            serverTasks.push({

              ...child,

              original_is_completed: child.is_completed,

              original_description: child.description,

              original_photo_path: child.photo_path,

              is_local_new: false // 标记为非本地新建

            });

          });

        }

      });



      // 保留本地状态：删除标记、本地新建项目等

      const preservedTasks = [];



      // 处理现有的服务器项目，保留本地状态

      for (const serverTask of serverTasks) {

        const existingTask = tasks.value.find((task: any) => task.id === serverTask.id);

        if (existingTask) {

          // 保留本地的删除标记和其他状态

          preservedTasks.push({

            ...serverTask,

            _toBeDeleted: existingTask._toBeDeleted, // 保留删除标记

            _photo_needs_move: existingTask._photo_needs_move, // 保留照片移动标记

            _modified: existingTask._modified, // 保留修改标记

            photo_path: existingTask._toBeDeleted ? existingTask.photo_path : serverTask.photo_path // 如果要删除，保留原路径

          });

        } else {

          preservedTasks.push(serverTask);

        }

      }



      // 保留本地新建的项目

      const localNewTasks = tasks.value.filter((task: any) => task.is_local_new);



      // 保留仍标记为删除但不在服务器数据中的项目（可能已被服务器删除）

      const locallyDeletedTasks = tasks.value.filter((task: any) =>

        task._toBeDeleted === true && !serverTasks.find((serverTask: any) => serverTask.id === task.id)

      );



      // 合并所有项目

      tasks.value = [...preservedTasks, ...localNewTasks, ...locallyDeletedTasks];



      // 默认将所有类别设置为折叠状态

      expandedTasks.value.clear();

    }

  } catch (error) {

    console.error('获取进度详情失败:', error);

    ElMessage.error('获取进度详情失败');

  }

};

// 更新订单状态
const updateOrderStatus = async () => {
  if (!selectedStatus.value || !localCurrentStatus.value) {
    ElMessage.warning('请选择订单状态');
    return;
  }

  try {
    // 显示加载提示
    fullScreenLoading.value = true;

    // 准备更新数据
    const statusData = {
      status: localCurrentStatus.value,
      status_time: localCurrentStatusTime.value instanceof Date
        ? localCurrentStatusTime.value.toISOString().split('T')[0]
        : localCurrentStatusTime.value
    };

    // 调用API更新订单状态
    const response: any = await request.put(`/api/order-status/${selectedStatus.value.id}/status`, statusData);

    if (response) {
      // 更新本地数据
      selectedStatus.value.current_status = localCurrentStatus.value;
      selectedStatus.value.current_status_time = statusData.status_time;

      // 更新订单详情中的状态信息
      if (selectedOrderDetail.value) {
        selectedOrderDetail.value.current_status = localCurrentStatus.value;
        selectedOrderDetail.value.current_status_time = statusData.status_time;
      }

      if (selectedOrder.value) {
        selectedOrder.value.current_status = localCurrentStatus.value;
        selectedOrder.value.current_status_time = statusData.status_time;
      }

      ElMessage.success('订单状态更新成功');
    }
  } catch (error) {
    console.error('更新订单状态失败:', error);
    ElMessage.error('更新订单状态失败');
  } finally {
    // 关闭加载提示
    fullScreenLoading.value = false;
  }
};

// 开始编辑标题 - 弹出对话框
const startEditing = async (task: any, type: 'category' | 'sub') => {
  try {
    // 使用ElMessageBox.prompt弹出输入框，类似addNewCategory的方式
    const result = await ElMessageBox.prompt(
      `请输入${type === 'category' ? '类别' : '任务'}名称`,
      `修改${type === 'category' ? '类别' : '任务'}标题`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: type === 'category' ? task.category : task.name,
        inputPattern: /\S+/,
        inputErrorMessage: `${type === 'category' ? '类别' : '任务'}名称不能为空`,
        inputPlaceholder: `请输入${type === 'category' ? '类别' : '任务'}名称`
      }
    );

    const newName = result.value.trim();
    if (!newName) {
      ElMessage.warning(`${type === 'category' ? '类别' : '任务'}名称不能为空`);
      return;
    }

    // 直接更新项目名称
    if (type === 'category') {
      task.category = newName;
      task.name = newName; // 同时更新名称字段，保持一致性
    } else {
      task.name = newName;
    }

    // 标记项目为已修改，以便在缓存时发送到服务器
    task._modified = true;

    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;

    ElMessage.success(`${type === 'category' ? '类别' : '任务'}已更新到本地，点击"缓存"或"保存"按钮后会同步到服务器`);
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel' && error.type !== 'cancel') {
      console.error('编辑标题失败:', error);
    }
  }
};

// 关闭编辑标题对话框（保持兼容性，虽然不再使用）
const closeEditTaskTitleDialog = () => {
  editTaskTitleDialogVisible.value = false;
  titleEditingTask.value = null;
  titleEditingValue.value = '';
  titleEditingType.value = 'sub';
};

// 确认编辑标题（保持兼容性，虽然不再使用）
const confirmEditTaskTitle = async () => {
  if (!titleEditingTask.value) {
    ElMessage.error('没有选中要编辑的项目');
    return;
  }

  const updatedValue = titleEditingValue.value.trim();
  if (!updatedValue) {
    ElMessage.error('标题不能为空');
    return;
  }

  const originalValue = titleEditingType.value === 'category'
    ? titleEditingTask.value.category
    : titleEditingTask.value.name;

  if (updatedValue === originalValue) {
    // 如果值没有改变，直接关闭对话框
    closeEditTaskTitleDialog();
    return;
  }

  // 从原始tasks数组中找到相同的项目进行修改
  const originalTask = tasks.value.find((task: any) => task.id === titleEditingTask.value.id);
  if (originalTask) {
    // 本地更新原始项目数据
    if (titleEditingType.value === 'category') {
      originalTask.category = updatedValue;
      // 如果是类别，同时更新名称字段
      originalTask.name = updatedValue;
    } else {
      originalTask.name = updatedValue;
    }

    // 标记项目为已修改，以便在缓存时发送到服务器
    originalTask._modified = true;
  }

  ElMessage.success('标题已更新到本地，点击"缓存"或"保存"按钮后会同步到服务器');
  closeEditTaskTitleDialog();
};

// 完成编辑（保留原函数，用于其他编辑场景）
const finishEditing = async (task: any, type: 'category' | 'sub') => {
  if (!task.isEditing) return;

  const updatedValue = task.editingValue.trim();
  if (updatedValue && updatedValue !== (type === 'category' ? task.category : task.name)) {
    if (type === 'category') {
      task.category = updatedValue;
      // 如果是类别，同时更新名称字段
      task.name = updatedValue;
    } else {
      task.name = updatedValue;
    }

    // 标记项目为已修改，但不立即发送到服务器
    task._modified = true;

    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;

    ElMessage.success('项目已更新到本地');
  }

  task.isEditing = false;
  task.editingValue = '';
};

// 清空所有任务项
const clearAllTasks = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空当前订单的全部任务项数据吗？此操作将删除所有类别和任务数据及对应图片等。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 调用后端API清空任务项
    if (selectedStatus.value) {
      const response: any = await request.post(`/api/order-status/${selectedStatus.value.id}/clear`);

      if (response && response.total_deleted !== undefined) {
        // 清空本地数据
        tasks.value = [];
        // 更新进度信息
        if (selectedStatus.value) {
          selectedStatus.value.total_tasks = 0;
          selectedStatus.value.completed_tasks = 0;
          selectedStatus.value.progress_percent = 0;
        }

        // 标记有未保存的更改
        hasUnsavedChangesFlag.value = true;

        ElMessage.success(`成功清空任务项数据，共删除 ${response.total_deleted} 个项目`);
      } else {
        ElMessage.error('清空任务项失败');
      }
    } else {
      ElMessage.error('当前没有进度记录');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空任务项失败:', error);
      ElMessage.error('清空任务项失败');
    }
  }
};

// 删除任务项
const deleteTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务项 "${task.item_type === 'category' ? task.category : task.name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 在tasks.value中找到原始项目对象
    const originalTask = tasks.value.find((i: any) => i.id === task.id);
    if (!originalTask) {
      console.error(`找不到ID为 ${task.id} 的原始项目`);
      return;
    }

    // 如果是类别（状态阶段），需要同时标记该阶段下的所有子任务为待删除
    if (task.item_type === 'category') {
      const childTasks = tasks.value.filter((i: any) => i.status_log_id === task.id);
      for (const childTask of childTasks) {
        childTask._toBeDeleted = true; // 标记子任务为待删除
      }
    }

    // 不再直接删除照片文件，而是在保存时由后端统一处理
    // 标记照片也需要删除，由后端处理
    originalTask._photo_needs_delete = true;

    // 标记原始项目为待删除，而不是立即从数组中移除
    originalTask._toBeDeleted = true; // 添加标记表示待删除

    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;

    ElMessage.success('任务项已标记为删除，将在保存时提交到服务器');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务项失败:', error);
      ElMessage.error('删除任务项失败');
    }
  }
};

// 缓存数据
const cacheData = async () => {
  try {
    // 显示全屏加载提示
    fullScreenLoading.value = true;

    if (!selectedStatus.value) {
      // 如果没有进度记录，先创建进度记录
      const orderId = selectedOrderDetail.value ? selectedOrderDetail.value.id : selectedOrder.value.id;
      const newStatus: any = await request.post('/api/order-status', {
        order_id: orderId,
        remarks: '订单进度记录'
      });
      const statusId = newStatus.id;
      selectedStatus.value = newStatus;

      // 更新订单列表中的ID
      if (selectedOrderDetail.value) selectedOrderDetail.value.status_id = statusId;
      if (selectedOrder.value) selectedOrder.value.status_id = statusId;
    }

    // 在构建发送数据之前，准备图片移动标记
    // 不再调用handlePhotoFiles，因为图片移动将由后端处理
    // 但我们需要确保需要移动的标记被发送到后端
    const tasksToProcess = tasks.value
      .filter((task: any) => !(task.is_local_new && task._toBeDeleted))  // 过滤掉本地新建且被删除的项目
      .map((task: any) => {
        // 确保即使未定义也要包含 _toBeDeleted 属性
        const taskToSend: any = {
          id: task.id,
          order_status_id: task.order_status_id,
          status_log_id: task.status_log_id,
          category: task.category,
          name: task.name,
          item_type: task.item_type,
          is_completed: task.is_completed,
          photo_path: task.photo_path,  // 发送原始路径
          description: task.description,
          sort: task.sort,
          is_local_new: task.is_local_new,
          // 添加图片移动标记，让后端知道需要移动图片
          _photo_needs_move: task._photo_needs_move || false,
          // 添加需要删除的照片路径
          photos_to_delete: task.photos_to_delete || []
        };

        // 显式添加 _toBeDeleted 属性，确保它被发送到服务器
        taskToSend._toBeDeleted = task._toBeDeleted || false;

        return taskToSend;
      });

    // 使用批量API处理所有项目
    const batchResult: any = await request.post(`/api/order-status/${selectedStatus.value.id}/tasks/batch`, {
      tasks: tasksToProcess
    });

    // 更新本地数据，将服务器返回的ID和状态同步
    if (batchResult.created_tasks) {
      batchResult.created_tasks.forEach((serverTask: any) => {
        // 根据服务器返回的原始信息更新本地项目
        // 查找对应的本地项目
        const localTaskIndex = tasks.value.findIndex((task: any) =>
          task.is_local_new &&
          task.name === serverTask.name &&
          task.category === serverTask.category &&
          task.item_type === serverTask.item_type
        );

        if (localTaskIndex !== -1) {
          const localTask = tasks.value[localTaskIndex];
          const oldId = localTask.id; // 保存旧ID用于更新子项的parent_id

          localTask.id = serverTask.id;
          localTask.is_local_new = false;
          localTask.original_is_completed = localTask.is_completed;
          localTask.original_description = localTask.description;
          localTask.original_photo_path = localTask.photo_path;

          // 如果这是一个类别项目，更新所有引用它的子任务的parent_id
          if (localTask.item_type === 'category') {
            tasks.value.forEach(task => {
              if (task.parent_id === oldId) {
                task.parent_id = serverTask.id; // 更新子任务的parent_id为新的服务器ID
              }
            });
          }
        }
      });
    }

    // 从本地tasks中移除已删除的项目
    if (batchResult.deleted_tasks && batchResult.deleted_tasks.length > 0) {
      for (const deletedTask of batchResult.deleted_tasks) {
        const taskIndex = tasks.value.findIndex((task: any) => task.id === deletedTask.id);
        if (taskIndex !== -1) {
          tasks.value.splice(taskIndex, 1);
        }
      }
    }

    // 更新进度记录的进度信息（使用批量API返回的进度）
    if (selectedStatus.value && batchResult.progress !== undefined) {
      selectedStatus.value.progress_percent = batchResult.progress;
      selectedStatus.value.completed_tasks = batchResult.completed_tasks;
      selectedStatus.value.total_tasks = batchResult.total_tasks;

      // 更新订单列表中的进度信息
      if (selectedOrderDetail.value) {
        selectedOrderDetail.value.progress_percent = batchResult.progress;
        selectedOrderDetail.value.completed_tasks = batchResult.completed_tasks;
        selectedOrderDetail.value.total_tasks = batchResult.total_tasks;
      }
      if (selectedOrder.value) {
        selectedOrder.value.progress_percent = batchResult.progress;
        selectedOrder.value.completed_tasks = batchResult.completed_tasks;
        selectedOrder.value.total_tasks = batchResult.total_tasks;
      }
    }

    // 缓存成功后，重新获取数据以确保页面显示最新状态
    await refreshStatusData();

    // 同时更新订单列表中的进度信息，确保列表视图也能显示最新进度
    if (selectedOrderDetail.value || selectedOrder.value) {
      const currentOrder = selectedOrderDetail.value || selectedOrder.value;
      const orderInList = orders.value.find((order: any) => order.id === currentOrder.id);
      if (orderInList && selectedStatus.value) {
        orderInList.progress_percent = batchResult.progress || 0;
        orderInList.completed_tasks = batchResult.completed_tasks || 0;
        orderInList.total_tasks = batchResult.total_tasks || 0;
      }
    }

    hasUnsavedChangesFlag.value = false; // 缓存成功后重置未保存更改标志
    ElMessage.success('数据已缓存');
    return true;
  } catch (error) {
    console.error('缓存数据失败:', error);
    ElMessage.error('缓存数据失败');
    return false;
  } finally {
    // 确保无论成功或失败都关闭全屏加载提示
    fullScreenLoading.value = false;
  }
};



// 保存并关闭
const saveAndClose = async () => {
  try {
    // 检查是否有未保存的更改，如果没有则直接关闭
    if (!hasUnsavedChangesFlag.value) {
      orderDetailDialogVisible.value = false;
      ElMessage.info('没有未保存的更改');
      return;
    }

    // 显示全屏加载提示
    fullScreenLoading.value = true;

    // 首先执行验证和保存
    const result = await cacheData();
    // 只有在保存成功后才关闭对话框
    if (result === true) {
      orderDetailDialogVisible.value = false;
    }
  } catch (error) {
    console.error('保存数据失败:', error);
    ElMessage.error('保存数据失败');
  } finally {
    // 确保无论成功或失败都关闭全屏加载提示
    fullScreenLoading.value = false;
  }
};

// 打开编辑任务项对话框
const openEditTaskDialog = (task: any) => {
  // 设置编辑表单的值
  newTaskForm.value = {
    taskType: task.item_type,
    parentCategory: task.parent_id, // 对于子项，设置父项ID
    taskName: task.item_type === 'category' ? task.category : task.name, // 对于类别，使用category，对于子项，使用name
    category: task.category
  };

  // 如果是子项，需要查找父项类别
  if (task.item_type === 'sub' && task.parent_id) {
    const parentTask = tasks.value.find((i: any) => i.id === task.parent_id);
    if (parentTask) {
      newTaskForm.value.category = parentTask.category;
    }
  }

  // 打开对话框
  addTaskDialogVisible.value = true;
};

// 创建新的任务项的辅助函数
const createNewTask = (taskType: 'category' | 'sub', taskName: string, taskCategory: string, statusLogId: number | null, options: any = {}) => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    ElMessage.error('请先选择一个订单');
    return null;
  }

  const newLocalTask: any = {
    id: Date.now(), // 使用时间戳作为临时ID
    order_status_id: selectedStatus.value?.id || null,
    status_log_id: statusLogId, // 状态日志ID，对应后端的status_log_id
    category: taskCategory,
    name: taskName,
    item_type: taskType,
    is_completed: false,
    photo_path: null,
    description: null,
    sort: 0, // 使用sort字段
    create_time: new Date().toISOString(),
    update_time: new Date().toISOString(),
    // 用于标识这是本地新建的项目
    is_local_new: true,
    ...options // 合并其他选项
  };
  // 添加到本地tasks数组
  tasks.value.push(newLocalTask);

  // 标记有未保存的更改
  hasUnsavedChangesFlag.value = true;

  return newLocalTask;
};

// 添加新的状态阶段
const addNewCategory = async () => {
  try {
    const result = await ElMessageBox.prompt('请输入状态名称', '添加状态阶段', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '状态名称不能为空',
      inputPlaceholder: '请输入状态名称，如：下单、排产、完成生产等'
    });

    const taskName = result.value.trim();
    if (!taskName) {
      ElMessage.warning('状态名称不能为空');
      return;
    }

    // 对于状态阶段，我们实际上需要创建一个状态日志记录
    // 但是由于这是前端界面，我们将创建一个虚拟的类别项
    const newLocalTask: any = {
      id: -Date.now(), // 使用负数作为临时ID，标识这是状态日志（类别）项
      order_status_id: selectedStatus.value?.id || null,
      status_log_id: -Date.now(), // 使用负数作为临时ID
      category: taskName,
      name: taskName, // 对于状态日志，名称和类别相同
      item_type: 'category',
      is_completed: false,
      photo_path: null,
      description: null,
      sort: 0,
      create_time: new Date().toISOString(),
      update_time: new Date().toISOString(),
      // 用于标识这是本地新建的项目
      is_local_new: true
    };

    // 添加到本地tasks数组
    tasks.value.push(newLocalTask);

    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;

    ElMessage.success('状态阶段已添加');
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel' && error.type !== 'cancel') {
      console.error('添加状态阶段失败:', error);
    }
  }
};


// 直接添加子任务到指定类别
const addSubTaskToCategory = async (categoryId: number | null, category?: string) => {
  try {
    const result = await ElMessageBox.prompt('请输入任务名称', '添加任务', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '任务名称不能为空',
      inputPlaceholder: '请输入任务名称，如：部件1、角度1等'
    });

    const taskName = result.value.trim();
    if (!taskName) {
      ElMessage.warning('任务名称不能为空');
      return;
    }

    const newLocalTask: any = {
      id: Date.now(), // 使用时间戳作为唯一ID
      order_status_id: selectedStatus.value?.id || null,
      status_log_id: categoryId || 1, // 使用传入的类别ID作为状态日志ID
      category: category || '未分类',
      name: taskName, // 使用用户输入的名称
      item_type: 'sub',
      is_completed: false,
      photo_path: null,
      description: null,
      sort: 0,
      create_time: new Date().toISOString(),
      update_time: new Date().toISOString(),
      is_local_new: true
    };

    // 添加到本地tasks数组
    tasks.value.push(newLocalTask);

    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;

    ElMessage.success('已添加新任务项');
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel' && error.type !== 'cancel') {
      console.error('添加任务失败:', error);
    }
  }
};
// 设置类别输入框ref
const categoryInputRefs = ref({});
const setCategoryInputRef = (el: any, id: any) => {
  if (el) {
    categoryInputRefs.value[id] = el;
  }
};

// 设置子任务输入框ref
const subTaskInputRefs = ref({});
const setSubTaskInputRef = (el: any, id: any) => {
  if (el) {
    subTaskInputRefs.value[id] = el;
  }
};

// 检查是否有变更
const hasUnsavedChanges = () => {
  return tasks.value.some(task =>
    task.is_completed !== task.original_is_completed ||
    task.description !== task.original_description ||
    task.photo_path !== task.original_photo_path
  );
};
// 关闭对话框
const closeDialog = async () => {
  // 检查是否有未保存的更改
  if (hasUnsavedChanges()) {
    try {
      const result = await ElMessageBox.confirm(
        '当前有未保存的更改，是否保存？',
        '提示',
        {
          confirmButtonText: '保存',
          cancelButtonText: '不保存',
          type: 'warning'
        }
      );

      if (result === 'confirm') {
        await cacheData();
      }
    } catch (error) {
      // 用户点击了取消，不关闭对话框
      return;
    }
  }

  orderDetailDialogVisible.value = false;
};

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    // 使用新的专门用于进度的API
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

// 获取订单进度
const getOrderStatusProgress = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  return order ? (order.progress_percent || 0) : 0;
};

const getOrderStatusStatus = (orderId: number) => {
  const progress = getOrderStatusProgress(orderId);
  if (progress === 100) return 'success';
  if (progress > 0) return 'warning';
  return '';
};

// 获取订单进度的分数格式 (如: "1/3")
const getOrderStatusFraction = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  if (!order) return '0/0';

  const completedTasks = order.completed_tasks || 0;
  const totalTasks = order.total_tasks || 0;

  return `${completedTasks}/${totalTasks}`;
};

// 获取类别进度的分数格式 (如: "1/3")
const getCategoryTaskFraction = (category: any) => {
  if (!category.total_children) return '0/0';

  return `${category.completed_children}/${category.total_children}`;
};

// 开始进度
const startStatus = async (row: any) => {
  selectedOrder.value = row;
  selectedOrderDetail.value = null; // 清除之前选择的详情

  // 获取或创建进度数据
  orderDetailDialogVisible.value = true;
  await refreshStatusData();
};

// 查看进度报告
const viewStatusReport = async (order: any) => {
  try {
    // 获取或创建进度记录
    let statusId = order.status_id;
    if (!statusId) {
      const newStatus: any = await request.post('/api/order-status', {
        order_id: order.id,
        remarks: '订单进度记录'
      });
      statusId = newStatus.id;
      order.status_id = statusId;
    }

    // 跳转到进度报告页面（在新窗口打开）
    window.open(`/api/status/${statusId}/report`, '_blank');
  } catch (error) {
    console.error('查看进度报告失败:', error);
    ElMessage.error('查看进度报告失败');
  }
};

// 关闭详情对话框
const handleCloseDetailDialog = () => {
  detailDialogVisible.value = false;
  selectedStatus.value = null;
  tasks.value = [];
};



// 更新任务项
const updateStatusTask = async (task: any) => {
  // 在本地更新项目，不立即验证，验证将在保存时进行
  task._modified = true;
  hasUnsavedChangesFlag.value = true; // 标记有未保存的更改
  ElMessage.success('任务项已更新到本地');
};

// 切换类别的展开/折叠状态
const toggleExpand = (taskId: number) => {
  if (expandedTasks.value.has(taskId)) {
    expandedTasks.value.delete(taskId);
  } else {
    expandedTasks.value.add(taskId);
  }
};

// 检查类别是否展开
const isTaskExpanded = (taskId: number): boolean => {
  return expandedTasks.value.has(taskId);
};

// 显示图片预览

const showImagePreview = (imageUrl: string) => {

  previewImageUrl.value = imageUrl;

  imagePreviewVisible.value = true;

};




// 分页相关方法
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchOrders();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchOrders();
};

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    // 这里需要一个获取用户信息的API，如果不存在则需要创建
    // 临时从token中解析用户信息
    const tokenStr = localStorage.getItem('oa_token');
    if (tokenStr) {
      // 简单解析JWT token获取用户角色
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

// 组件挂载时获取数据
onMounted(async () => {
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize);

  await fetchUserInfo();
  fetchOrders();
});

// 组件卸载前移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// 生成报告
const generateReport = async (order?: any) => {
  let statusId;

  // 如果传入了订单参数，则使用该订单的进度记录
  if (order) {
    // 尝试获取或创建订单的进度记录
    try {
      let currentStatusId = order.status_id;

      // 如果订单没有进度记录，先创建一个
      if (!currentStatusId) {
        const newStatus: any = await request.post('/api/order-status', {
          order_id: order.id,
          remarks: '进度报告'
        });
        currentStatusId = newStatus.id;

        // 更新订单列表中的ID
        order.status_id = currentStatusId;
      }

      statusId = currentStatusId;
    } catch (error) {
      console.error('获取或创建进度记录失败:', error);
      ElMessage.error('获取或创建进度记录失败');
      return;
    }
  } else {
    // 否则使用当前选中的进度记录
    if (!selectedStatus.value || !selectedStatus.value.id) {
      ElMessage.warning('请先保存进度记录');
      return;
    }
    statusId = selectedStatus.value.id;
  }

  // 检查是否有未保存的更改，如果有则先缓存
  if (order && hasUnsavedChangesFlag.value) {
    // 在生成报告前先调用缓存以确保更新最新时间
    try {
      await cacheData();
      // 短暂延迟以确保后端处理完成
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('缓存数据失败:', error);
      ElMessage.error('生成报告前缓存数据失败，仍将尝试生成报告');
    }
  } else {
    ElMessage.info('数据已是最新，无需重复保存');
  }

  // 在新窗口中打开报告页面
  window.open(`/api/order-status/${statusId}/report`, '_blank');
};

// 路由
const router = useRouter();
</script>

<style scoped>
.el-icon{
  padding: 8px 15px;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}
.btn-add-status{
  background-color: #33c44b;
}
.btn-add-photo{
  color: gray;
  background-color: rgba(156, 156, 156, 0.1);
  font-size: 16px;
  margin-left: 15px;
}

.btn-add-task{
  padding: 6px 12px;
  color: gray;
  background-color: rgba(156, 156, 156, 0.3);
  font-size: 16px;
  margin-left: 15px;
}

.order-status-container {
  padding: 10px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .order-status-container {
    padding: 20px;
  }
}

.header {
  margin-bottom: 15px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .header {
    margin-bottom: 20px;
  }
}

.header-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .header-content {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .card-header {
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
  }
}

.progress-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  padding: 5px 10px;
  background-color: rgba(156, 156, 156, 0.1);
  border-radius: 5px;
}

.order-list-section {
  margin-bottom: 15px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .order-list-section {
    margin-bottom: 20px;
  }
}

/* 为表格行添加鼠标指针样式 */
:deep(.el-table .el-table__row) {
  cursor: pointer;
}

:deep(.el-table .el-table__row:hover > td) {
  background-color: #f5f7fa;
}

/* 可编辑标题样式 */
.category-title-container, .sub-task-name-container {
  display: inline-flex;
  align-items: center;
  flex: 1;
  flex-wrap: wrap;
}

.category-title, .sub-task-name {
  cursor: pointer;
  word-break: break-word;
}

.category-title:hover, .sub-task-name:hover {
  background-color: #777777;
  color: white;
  /* padding: 2px 4px;
  border-radius: 3px; */
}

.add-sub-task {
  padding: 10px 0 0 10px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .add-sub-task {
    padding: 10px 0 0 20px;
  }
}

.category-title-container, .sub-task-name-container {
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  gap: 5px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .category-title-container, .sub-task-name-container {
    flex-direction: row;
    align-items: center;
  }
}

.category-title-container .el-input, .sub-task-name-container .el-input {
  width: 100%;
  margin-right: 10px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .category-title-container .el-input, .sub-task-name-container .el-input {
    width: 200px;
  }
}

.pagination {
  margin-top: 15px;
  text-align: center;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .pagination {
    margin-top: 20px;
  }
}

.order-info-card {
  margin-bottom: 15px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .order-info-card {
    margin-bottom: 20px;
  }
}

.order-info-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.status-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 250px;
}

.date-picker-container {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 250px;
}

.status-label, .date-label {
  font-weight: bold;
  white-space: nowrap;
}

/* 移动端适配 */
@media (max-width: 767px) {
  .status-controls {
    flex-direction: column;
    align-items: flex-start;
  }

  .status-selector, .date-picker-container {
    width: 100%;
  }
}

.status-tasks-card {
  margin-bottom: 15px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .status-tasks-card {
    margin-bottom: 20px;
  }
}

.status-category {
  margin-bottom: 15px;
  border: 1px solid #ebeef5;
  border-radius: 15px;
  padding: 10px;
  background-color: rgb(112, 85, 85,0.1);
}

/* 移动端适配 */
@media (min-width: 768px) {
  .status-category {
    margin-bottom: 10px;
    padding: 3px;
  }
}

.category-item {
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  padding: 8px;
  background-color: white;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .category-item {
    border-radius: 15px !important;
    padding: 10px;
  }
}

.category-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

/* 移动端适配 - 在移动端也使用横向布局，因为有足够空间 */
@media (max-width: 767px) {
  .category-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

@media (min-width: 768px) {
  .category-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.category-title {
  font-weight: bold;
  font-size: 14px;
  word-break: break-word;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .category-title {
    font-size: 16px;
  }
}

.category-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px;
  background-color: white;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .category-item {
    padding: 10px;
  }
}

.category-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

/* 移动端适配 - 在移动端也使用横向布局，因为有足够空间 */
@media (max-width: 767px) {
  .category-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

@media (min-width: 768px) {
  .category-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.category-title {
  font-weight: bold;
  font-size: 14px;
  word-break: break-word;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .category-title {
    font-size: 16px;
  }
}

.category-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  min-width: auto;
  width: 100%;
}

/* 移动端适配 - 在移动端也使用横向布局，因为有足够空间 */
@media (max-width: 767px) {
  .category-progress {
    flex-direction: row;
    align-items: center;
    width: auto;
    min-width: 150px; /* 确保进度条有足够的显示空间 */
  }
}

@media (min-width: 768px) {
  .category-progress {
    flex-direction: row;
    align-items: center;
    width: auto;
    min-width: 150px; /* 确保进度条有足够的显示空间 */
  }
}

.progress-text {
  font-size: 12px;
  color: #606266;
  text-align: left;
  width: 100%;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .progress-text {
    text-align: left;
    width: auto;
  }
}

/* 专门针对进度条的样式，使用更高的优先级 */
:deep(.el-progress-bar__outer) {
  height: 20px !important;
  border-radius: 10px !important;
  background-color: #ebeef5 !important;
}

:deep(.el-progress-bar__inner) {
  height: 20px !important;
  border-radius: 10px !important;
  line-height: 20px !important;
}

/* 确保整个进度条容器的样式 */
:deep(.el-progress) {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
}

/* 针对特定组件的样式 */
.category-progress :deep(.el-progress) {
  width: 100% !important;
  min-width: auto !important;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .category-progress :deep(.el-progress) {
    width: 200px !important;
    min-width: 200px !important;
  }
}

.sub-tasks {
  padding-left: 10px;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .sub-tasks {
    padding-left: 20px;
  }
}

.sub-task {
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fafafa;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .sub-task {
    margin-bottom: 15px;
    padding: 10px;
  }
}

.sub-task-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

/* 移动端适配 - 在移动端也使用横向布局，因为有足够空间 */
@media (min-width: 768px) {
  .sub-task-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.sub-task-name {
  font-weight: 500;
  word-break: break-word;
}

.sub-task-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  width: 100%;
}

/* 移动端适配 - 在移动端也使用横向布局，因为有足够空间 */
@media (max-width: 767px) {
  .sub-task-actions {
    flex-direction: row;
    align-items: center;
    width: auto;
  }
}

@media (min-width: 768px) {
  .sub-task-actions {
    flex-direction: row;
    align-items: center;
    width: auto;
  }
}

.sub-task-content {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #dcdfe6;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

/* 移动端适配 - 在移动端也使用横向布局，因为有足够空间 */
@media (max-width: 767px) {
  .sub-task-content {
    flex-direction: row;
    gap: 20px;
    align-items: center;
  }
}

@media (min-width: 768px) {
  .sub-task-content {
    flex-direction: row;
    gap: 20px;
    align-items: center;
  }
}

.sub-task-content > div {
  flex-shrink: 0;
  width: 100%;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .sub-task-content > div {
    width: auto;
  }
}

.upload-section {
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
}

.photo-grid {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  width: 100%;
}

.photo-preview {
  position: relative;
  display: inline-block;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: visible; /* 改为visible以显示超出部分的删除图标 */
}

/* 移动端适配 */
@media (min-width: 768px) {
  .photo-preview {
    width: 100px;
    height: 100px;
  }
}

.delete-photo-icon {
  position: absolute;
  top: -6px;
  right: -6px;
  background: red;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  z-index: 10; /* 增加z-index确保在顶层 */
}

.photo-preview img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  z-index: 1;
  position: relative;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .photo-preview img {
    width: 100px;
    height: 100px;
  }
}

.defect-section {
  margin-top: 10px;
  width: 100%;
}

.photo-preview {
  margin-top: 10px;
}

.bottom-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

/* 移动端适配 - 在移动端也使用横向布局，因为有足够空间 */
@media (max-width: 767px) {
  .bottom-actions {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
  }
}

@media (min-width: 768px) {
  .bottom-actions {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding-top: 20px;
  }
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

/* 移动端适配 - 在移动端也进行优化显示 */
@media (max-width: 767px) {
  .action-buttons {
    flex-wrap: nowrap;
    overflow-x: auto;
    justify-content: flex-start;
    gap: 6px;
  }
}

@media (min-width: 768px) {
  .action-buttons {
    gap: 10px;
    justify-content: flex-start;
  }
}

.standalone-task {
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #f5f7fa;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .standalone-task {
    margin-bottom: 15px;
    padding: 10px;
  }
}

.progress-cell {
  cursor: pointer;
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

  .el-table {
    font-size: 12px;
  }

  .el-table th {
    padding: 4px 0;
  }

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

  .el-textarea__inner {
    font-size: 12px;
  }

  .el-input__inner {
    font-size: 12px;
  }
}
</style>