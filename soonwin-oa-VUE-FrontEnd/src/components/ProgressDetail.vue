<template>
  <div class="progress-detail">
    <!-- 订单基础信息卡片 -->
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>订单基础数据</span>
        </div>
      </template>
      <el-descriptions :column="isMobile ? 1 : 2" border>
        <el-descriptions-item label="合同编号">{{ orderInfo.contract_no }}</el-descriptions-item>
        <el-descriptions-item label="订单编号">{{ orderInfo.order_no }}</el-descriptions-item>
        <el-descriptions-item label="包装机单号">{{ orderInfo.machine_no }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ orderInfo.machine_name }}</el-descriptions-item>
        <el-descriptions-item label="机型">{{ orderInfo.machine_model }}</el-descriptions-item>
        <el-descriptions-item label="主机数量">{{ orderInfo.machine_count }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ orderInfo.order_time }}</el-descriptions-item>
        <el-descriptions-item label="出货时间">{{ orderInfo.ship_time }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
                <!-- 进度状态管理 -->
                <el-card class="mb-4">
                  <template #header>
                    <div class="card-header">
                      <span>当前状态：{{ currentStatus || '无' }}</span>
                      <div>
                        <el-button type="primary" size="default" @click="showCreateStatusDialog">
                          <el-icon><Plus /></el-icon>
                          创建
                        </el-button>
                        <el-button v-if="currentStatus" type="warning" size="default" @click="showSwitchStatusDialog">
                          <el-icon><Switch /></el-icon>
                          切换
                        </el-button>
                        <el-button v-if="currentStatus" type="danger" @click="clearProgressStatusHandler" :loading="saving">
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-button>
                      </div>
                    </div>
                  </template>

      <el-descriptions v-if="currentStatus" :column="isMobile ? 1 : 2" border>
        <el-descriptions-item label="当前状态">{{ currentStatus }}</el-descriptions-item>
        <el-descriptions-item
            label="当前进度"
            style="display: flex; align-items: center; white-space: nowrap; flex-wrap: nowrap;">
          <!-- 进度条容器 -->
          <div style="width: 200px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; flex-shrink: 0;">
            <div
              :style="{width: `${progressStat.rate}%`, height: '100%'}"
              style="background: #67c23a; border-radius: 4px;">
            </div>
          </div>
          <!-- 进度文字 -->
          <span style="margin-left: 10px; flex-shrink: 0;">{{ progressStat.completed }}/{{ progressStat.total }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ currentStatusStartTime }}</el-descriptions-item>
        <el-descriptions-item label="预计完成">{{ currentStatusStartTime }}</el-descriptions-item>


      </el-descriptions>

                </el-card>
    <!-- 新建进度状态对话框 -->
    <!-- 创建状态对话框 -->
    <el-dialog v-model="showAddStatusDialog" title="新建进度状态" width="500px">
      <el-form :model="newStatusForm" label-width="120px">
        <el-form-item label="状态名称">
          <el-autocomplete
            v-model="newStatusValue"
            :fetch-suggestions="queryStatus"
            placeholder="请输入或选择进度状态"
            clearable
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="newStatusStartTime"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="预计完成时间">
          <el-date-picker
            v-model="newStatusExpectedCompleteTime"
            type="date"
            placeholder="选择预计完成日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddStatusDialog = false">取消</el-button>
          <el-button type="primary" @click="addNewStatus()">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 切换状态对话框 -->
    <el-dialog v-model="showSwitchStatusDialogVisible" title="切换进度状态" width="400px">
      <el-form :model="switchStatusForm" label-width="100px">
        <el-form-item label="选择状态">
          <el-select
            v-model="newStatusValue"
            placeholder="请选择要切换到的状态"
            style="width: 100%;"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSwitchStatusDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="switchToStatus()">确认</el-button>
        </span>
      </template>
    </el-dialog>    <!-- 进度项管理 -->
    <el-card v-if="currentStatus" title="当前状态进度项">

                  <template #header>

                    <div class="card-header">
                      <span>当前状态：{{ currentStatus }}</span>
            <el-button type="primary" @click="showAddItemForm = true">
              <el-icon><Plus /></el-icon>
              进度项
            </el-button>

                    </div>

                  </template>

      <!-- 进度项列表 -->
      <el-table :data="progressItems" border stripe>
        <el-table-column prop="title" label="项目" show-overflow-tooltip />
        <el-table-column label="文件" width="150">
          <template #default="scope">
            <el-button
              type="text"
              @click="viewMedia(scope.row.media_files)"
              v-if="scope.row.media_files.length"
            >
              <el-icon><Picture /></el-icon>
              查看文件({{ scope.row.media_files.length }})
            </el-button>
            <span v-else>无</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="150">
          <template #default="scope">
            {{ scope.row.create_time }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === '已完成' ? 'success' : 'warning'">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-icon class="opera-btn" style="background-color: #409eff" @click="editItem(scope.row)"><Edit /></el-icon>
            <el-icon class="opera-btn" style="background-color: #f56c6c" @click="deleteItem(scope.row.id)"><Delete /></el-icon>

          </template>
        </el-table-column>
      </el-table>

      <!-- 进度项增改表单弹窗 -->
      <el-dialog v-model="showAddItemForm" :title="editItemData ? '编辑进度项' : '新增进度项'" width="600px">
        <ProgressItemForm
          :progress-id="progressId"
          :edit-item="editItemData"
          @success="handleItemSuccess"
        />
      </el-dialog>

      <!-- 多媒体文件查看弹窗 -->
      <el-dialog v-model="showMediaDialog" title="文件预览" width="80%" :fullscreen="isFullscreen">
        <div class="media-list">
          <div
            class="media-item"
            v-for="media in currentMediaList"
            :key="media.id"
          >
            <img
              v-if="media.file_type === 'image'"
              :src="media.file_url"
              :alt="media.file_name"
              class="media-img"
              @click="toggleFullscreen"
            />
            <video
              v-else-if="media.file_type === 'video'"
              :src="media.file_url"
              controls
              class="media-video"
            ></video>
            <div v-else class="media-other">
              <el-icon><Document /></el-icon>
              <span>{{ media.file_name }}</span>
            </div>
            <div class="media-name">{{ media.file_name }}</div>
          </div>
        </div>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRoute, useRouter } from 'vue-router';
import {Plus, Refresh, Edit, Delete,Picture,Document,Switch} from '@element-plus/icons-vue';import { OrderBasicInfo, ProgressItem, ProgressStat } from '@/types/order';
import {
  getOrderProgress,
  updateProgressStatus,
  deleteProgressItem,
  deleteOrderProgress,
  clearProgressStatus,
  createProgressStatus
} from '@/api/progress';
import ProgressItemForm from './ProgressItemForm.vue';

const route = useRoute();
const router = useRouter();
const orderId = ref(route.params.id as string);

// 响应式数据
const orderInfo = ref<OrderBasicInfo>({} as OrderBasicInfo);
const progressId = ref<string>(''); // 进度表ID
const currentStatus = ref('');
const currentStatusStartTime = ref<string | null>(null);
const currentStatusExpectedCompleteTime = ref<string | null>(null);
const currentStatusActualCompleteTime = ref<string | null>(null);
const progressItems = ref<ProgressItem[]>([]);
const progressStat = ref<ProgressStat>({ completed: 0, total: 0, rate: 0 });
const windowWidth = ref(window.innerWidth);
const saving = ref(false); // 保存按钮加载状态
const showAddStatusDialog = ref(false); // 显示新建进度状态对话框
const showSwitchStatusDialogVisible = ref(false); // 显示切换进度状态对话框
const newStatusValue = ref(''); // 新建进度状态的值
const statusOptions = ref<{value: string, label: string}[]>([]); // 进度状态选项
const newStatusStartTime = ref<string>(''); // 新状态开始时间
const newStatusExpectedCompleteTime = ref<string | null>(null); // 新状态预计完成时间

// 弹窗控制
const showAddItemForm = ref(false);
const showMediaDialog = ref(false);
const editItemData = ref<ProgressItem | null>(null);
const currentMediaList = ref<ProgressItem['media_files']>([]);
const isFullscreen = ref(false);

// 进度条颜色
const progressColor = computed(() => {
  if (progressStat.value.rate < 30) return '#909399'; // 灰色
  if (progressStat.value.rate < 70) return '#e6a23c'; // 橙色
  if (progressStat.value.rate < 100) return '#409eff'; // 蓝色
  return '#67c23a'; // 绿色
});

// 计算属性：判断是否为移动端
const isMobile = computed(() => {
  return windowWidth.value < 768;
});

// 进度状态建议
const statusSuggestions = [
  { value: '下单' },
  { value: '采购' },
  { value: '排产' },
  { value: '生产' },
  { value: '发货' },
  { value: '完成' }
];

// 进度状态查询函数
const queryStatus = (queryString: string, cb: (arg: any) => void) => {
  let results = queryString ? statusSuggestions.filter(createFilter(queryString)) : statusSuggestions;
  // 如果输入的不是预设值，也允许使用
  if (queryString && !statusSuggestions.some(s => s.value === queryString)) {
    results = [...results, { value: queryString }];
  }
  cb(results);
};

const createFilter = (queryString: string) => {
  return (status: { value: string }) => {
    return status.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0;
  };
};

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

// 获取进度详情
const fetchProgressDetail = async () => {
  try {
    // request.ts会自动解包data，所以这里直接返回解包后的数据
    const data = await getOrderProgress(orderId.value);
    orderInfo.value = data.order_info;

    // 获取进度表ID
    if (data.progress_info && data.progress_info.id) {
      progressId.value = data.progress_info.id;
    }

    // 只有当后端返回的状态不为null/undefined时才设置，否则保持空值
    currentStatus.value = data.progress_info.current_status || '';

    // 设置当前状态的时间信息，获取与当前状态匹配的状态详情
    if (data.progress_info.status_details && data.progress_info.status_details.length > 0) {
      // 查找与当前状态匹配的状态详情
      const currentStatusDetail = data.progress_info.status_details.find(detail => detail.status === currentStatus.value);
      if (currentStatusDetail) {
        currentStatusStartTime.value = currentStatusDetail.start_time ? currentStatusDetail.start_time.split(' ')[0] : null;
        currentStatusExpectedCompleteTime.value = currentStatusDetail.expected_complete_time ? currentStatusDetail.expected_complete_time.split(' ')[0] : null;
        currentStatusActualCompleteTime.value = currentStatusDetail.actual_complete_time ? currentStatusDetail.actual_complete_time.split(' ')[0] : null;
      } else {
        // 如果找不到当前状态的详情，使用最后一个状态的详情
        const latestStatusDetail = data.progress_info.status_details[data.progress_info.status_details.length - 1];
        currentStatusStartTime.value = latestStatusDetail.start_time ? latestStatusDetail.start_time.split(' ')[0] : null;
        currentStatusExpectedCompleteTime.value = latestStatusDetail.expected_complete_time ? latestStatusDetail.expected_complete_time.split(' ')[0] : null;
        currentStatusActualCompleteTime.value = latestStatusDetail.actual_complete_time ? latestStatusDetail.actual_complete_time.split(' ')[0] : null;
      }
    }

    // 设置进度状态选项，从status_details中提取状态值
    if (data.progress_info.status_details) {
      statusOptions.value = data.progress_info.status_details.map(detail => ({
        value: detail.status,
        label: detail.status
      }));
      // 确保currentStatus的值在选项中
      if (statusOptions.value.length > 0 && !statusOptions.value.some(opt => opt.value === currentStatus.value)) {
        statusOptions.value.push({ value: currentStatus.value, label: currentStatus.value });
      }
    }

    // 过滤出与当前状态相关的进度项
    // 由于后端API目前没有直接提供按状态过滤的进度项，我们暂时显示所有进度项
    // 后续可根据需要在后端API中添加按状态过滤的功能
    progressItems.value = data.progress_items;
    progressStat.value = data.progress_stat;
  } catch (error) {
    ElMessage.error('获取进度详情失败');
    console.error(error);
  }
};
// 新建进度状态
const addNewStatus = async () => {
  if (!newStatusValue.value.trim()) {
    ElMessage.warning('请输入进度状态名称');
    return;
  }

  if (!newStatusStartTime.value) {
    ElMessage.warning('请选择开始时间');
    return;
  }

  try {
    // 检查是否已存在相同的选项
    const exists = statusOptions.value.some(option => option.value === newStatusValue.value);
    if (!exists) {
      statusOptions.value.push({
        value: newStatusValue.value,
        label: newStatusValue.value
      });
    }

    // 创建新的状态详情记录，包含开始时间和预计完成时间
    const statusData = {
      status: newStatusValue.value,
      start_time: newStatusStartTime.value,
      expected_complete_time: newStatusExpectedCompleteTime.value
    };

    // 调用API创建状态详情
    await createProgressStatus(orderId.value, statusData);

    // 设置为新添加的状态
    currentStatus.value = newStatusValue.value;

        // 关闭对话框并重置输入值
        showAddStatusDialog.value = false;
        newStatusValue.value = '';
        newStatusStartTime.value = ''; // 重置为初始状态，下次打开对话框时会设为今天
        newStatusExpectedCompleteTime.value = null;

        ElMessage.success('进度状态创建成功');

        // 重新加载数据
        fetchProgressDetail();
      } catch (error) {
        ElMessage.error('创建进度状态失败: ' + (error.message || error));
        console.error(error);
      }
    };// 切换状态 - 选择一个现有的状态详情
const switchToStatus = async () => {
  if (!newStatusValue.value.trim()) {
    ElMessage.warning('请选择要切换到的进度状态');
    return;
  }

  try {
    // 更新进度状态，这会自动更新OrderProgress的current_status
    const statusData = {
      status: newStatusValue.value,
      start_time: currentStatusStartTime.value,
      expected_complete_time: currentStatusExpectedCompleteTime.value,
      actual_complete_time: currentStatusActualCompleteTime.value
    };

    await updateProgressStatus(orderId.value, statusData);

    // 设置为切换到的状态
    currentStatus.value = newStatusValue.value;

    // 关闭对话框并重置输入值
    showSwitchStatusDialogVisible.value = false;
    newStatusValue.value = '';

    ElMessage.success('已切换到指定状态');

    // 重新加载数据
    fetchProgressDetail();
  } catch (error) {
    ElMessage.error('切换状态失败: ' + (error.message || error));
    console.error(error);
  }
};
// 更新当前进度状态 - 保存到后端
const saveProgressStatus = async () => {
  try {
    const statusData = {
      status: currentStatus.value,
      start_time: currentStatusStartTime.value,
      expected_complete_time: currentStatusExpectedCompleteTime.value,
      actual_complete_time: currentStatusActualCompleteTime.value
    };
    await updateProgressStatus(orderId.value, statusData);
    ElMessage.success('进度状态保存成功');
    fetchProgressDetail(); // 重新加载数据
  } catch (error) {
    ElMessage.error('保存进度状态失败');
    console.error(error);
  }
};

// 查看多媒体文件
const viewMedia = (mediaList: ProgressItem['media_files']) => {
  currentMediaList.value = mediaList;
  showMediaDialog.value = true;
  isFullscreen.value = false;
};

// 编辑进度项
const editItem = (item: ProgressItem) => {
  editItemData.value = item;
  showAddItemForm.value = true;
};

// 删除进度项
const deleteItem = async (itemId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个进度项吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await deleteProgressItem(itemId);
    ElMessage.success('进度项删除成功');
    fetchProgressDetail(); // 重新加载数据
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除进度项失败');
      console.error(error);
    }
  }
};

// 进度项增改成功后的回调
const handleItemSuccess = () => {
  showAddItemForm.value = false;
  editItemData.value = null;
  fetchProgressDetail(); // 重新加载数据
};

// 切换全屏

const toggleFullscreen = () => {

  isFullscreen.value = !isFullscreen.value;

};

// 添加一个标志来区分创建状态和切换状态
const isSwitchingStatus = ref(false);

// 显示切换状态对话框
const showSwitchStatusDialog = () => {
  // 显示切换状态对话框
  showSwitchStatusDialogVisible.value = true;
  // 设置为当前状态，用户可以从现有状态中选择
  newStatusValue.value = currentStatus.value;
};

// 显示创建状态对话框
const showCreateStatusDialog = () => {
  showAddStatusDialog.value = true;
  // 初始化日期值
  newStatusStartTime.value = new Date().toISOString().split('T')[0]; // 默认为当前日期
  newStatusExpectedCompleteTime.value = new Date().toISOString().split('T')[0]; // 默认为当前日期
  newStatusValue.value = '';
};

// 删除当前进度状态

const clearProgressStatusHandler = async () => {

  try {

    await ElMessageBox.confirm(

      '确定要删除当前进度状态吗？此操作将删除当前状态的详细信息及相关进度项。',

      '删除确认',

      {

        confirmButtonText: '确定删除',

        cancelButtonText: '取消',

        type: 'warning'

      }

    );

    await clearProgressStatus(orderId.value);

    ElMessage.success('当前状态已删除');

    // 重新加载数据

    fetchProgressDetail();

  } catch (error) {

    if (error !== 'cancel') {

      ElMessage.error('删除当前状态失败: ' + (error.message || error));

      console.error(error);

    }

  }

};



onMounted(() => {

  fetchProgressDetail();

  // 监听窗口大小变化

  window.addEventListener('resize', handleResize);

});



// 监听订单ID变化（路由参数变化）

watch(() => route.params.id, (newVal) => {

  if (newVal) {

    orderId.value = newVal as string;

    fetchProgressDetail();

  }

});



// 组件卸载时移除监听器

onUnmounted(() => {

  window.removeEventListener('resize', handleResize);

});
</script>

<style scoped>
.progress-detail {
  padding: 20px;
}

.mb-2 {
  margin-bottom: 10px;
}

.mb-4 {
  margin-bottom: 20px;
}

.label {
  font-weight: bold;
  color: #666;
  margin-right: 5px;
}

.info-item {
  margin-bottom: 10px;
  display: flex;
}

.status-control, .progress-stat {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.item-actions {
  display: flex;
  justify-content: flex-end;
}

.media-list {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.media-item {
  width: 200px;
  text-align: center;
}

.media-img, .media-video {
  width: 100%;
  height: 150px;
  object-fit: cover;
  cursor: pointer;
}

.media-img:hover {
  transform: scale(1.05);
  transition: transform 0.3s;
}

.media-other {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 150px;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.media-other .el-icon {
  font-size: 24px;
  color: #909399;
  margin-bottom: 5px;
}

.media-name {
  margin-top: 5px;
  font-size: 12px;
  color: #666;
  word-break: break-all;
}

<style scoped>
.progress-detail {
  padding: 20px;
}

.mb-2 {
  margin-bottom: 10px;
}

.mb-4 {
  margin-bottom: 20px;
}

.label {
  font-weight: bold;
  color: #666;
  margin-right: 5px;
  width: 120px;
  display: inline-block;
}

.info-item {
  margin-bottom: 10px;
  display: flex;
}

.status-control, .progress-stat {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.item-actions {
  display: flex;
  justify-content: flex-end;
}

.media-list {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.media-item {
  width: 200px;
  text-align: center;
}

.media-img, .media-video {
  width: 100%;
  height: 150px;
  object-fit: cover;
  cursor: pointer;
}

.media-img:hover {
  transform: scale(1.05);
  transition: transform 0.3s;
}

.media-other {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 150px;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.media-other .el-icon {
  font-size: 24px;
  color: #909399;
  margin-bottom: 5px;
}

.media-name {
  margin-top: 5px;
  font-size: 12px;
  color: #666;
  word-break: break-all;
}

/* 双列表单样式 */
.form-row {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}
.el-icon{
  margin-right: 5px;
}
.card-header {
  /* 启用 flex 布局 */
  display: flex;
  /* 让子元素两端对齐 */
  justify-content: space-between;
  /* 垂直方向居中对齐（视觉更美观） */
  align-items: center;
}

/* 可选：如果文字部分希望左对齐更紧凑，可给文字容器加样式 */
.card-header span {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.opera-btn{
  padding: 5px 10px;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}
</style>