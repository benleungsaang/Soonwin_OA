<template>
  <el-dialog
    :title="dialogTitle"
    v-model="isDialogVisible"
    width="80%"
    top="5vh"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    @close="handleClose"
  >
    <div v-loading="loading" class="log-container">
      <!-- 工具栏 -->
      <div class="log-toolbar">
        <el-button
          type="danger"
          size="small"
          @click="clearAllLogs"
          :icon="Loading"
          title="清空所有日志"
          v-if="isAdmin"
        >
          清空日志
        </el-button>
        <el-button
          type="warning"
          size="small"
          @click="resetStats"
          :icon="Refresh"
          title="复位新增数字统计"
          v-if="isAdmin && logType === 'inquiry'"
        >
          复位统计
        </el-button>
        <el-button
          type="info"
          size="small"
          @click="recalculateData"
          :icon="Refresh"
          title="重新计算统计数据"
          v-if="isAdmin && logType === 'inquiry'"
        >
          重新计算数据
        </el-button>
        <div v-if="statistics.last_reset_time" class="stat-label-time">
          复位统计自 {{ statistics.last_reset_time }} 起
        </div>
      </div>

      <!-- 统计卡片 - 调整结构适配一行显示 -->
      <el-card class="statistics-card" shadow="never" v-if="showStatistics">
        <div class="statistics-content">
          <!-- 所有统计项放在一个行容器中，实现一行显示 -->
          <div class="stat-row single-row">
            <!-- 累计主类型 -->
            <div class="stat-item-unified">
              <span class="stat-label-unified">累计{{ mainTypeText }}</span>
              <span class="stat-value-unified">{{ statistics.total_main || 0 }}</span>
            </div>
            <!-- 累计子类型 -->
            <div class="stat-item-unified">
              <span class="stat-label-unified">累计{{ subTypeText }}</span>
              <span class="stat-value-unified">{{ statistics.total_sub || 0 }}</span>
            </div>
            <!-- 月度主类型 -->
            <div class="stat-item-unified monthly">
              <span class="stat-label-unified">月度{{ mainTypeText }}</span>
              <span class="stat-value-unified monthly">{{ statistics.monthly_main || 0 }}</span>
            </div>
            <!-- 月度子类型 -->
            <div class="stat-item-unified monthly">
              <span class="stat-label-unified">月度{{ subTypeText }}</span>
              <span class="stat-value-unified monthly">{{ statistics.monthly_sub || 0 }}</span>
            </div>
            <!-- 新增主类型 -->
            <div class="stat-item-unified highlight">
              <span class="stat-label-unified">新增{{ mainTypeText }}</span>
              <span class="stat-value-unified highlight">{{ statistics.new_main || 0 }}</span>
            </div>
            <!-- 新增子类型 -->
            <div class="stat-item-unified highlight">
              <span class="stat-label-unified">新增{{ subTypeText }}</span>
              <span class="stat-value-unified highlight">{{ statistics.new_sub || 0 }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 日志列表 -->
      <div v-for="log in logs" :key="log.id" class="log-item">
        <el-card class="log-card" shadow="hover">
          <div class="log-header">
            <div class="log-operation-type">
              <span class="operation-type-text">{{ getOperationTypeText(log.operation_type) }}</span>
            </div>
            <div class="log-header-right">
              <!-- 恢复按钮 -->
              <el-button
                v-if="['delete', 'update', 'delete_communication', 'update_communication'].includes(log.operation_type) && isAdmin"
                link
                @click="handleRestoreLog(log.id)"
                class="log-btn"
                :title="'恢复数据'"
                style="background-color: green;"
              >
                <el-icon><Refresh /></el-icon>
              </el-button>

              <!-- 跳转按钮 -->
              <el-button
                v-if="log.module === logType && log.biz_id && log.operation_type !== 'delete' && handleJump"
                link
                style="background-color: gray"
                @click="handleJump(parseInt(log.biz_id))"
                class="log-btn"
                :title="`跳转至${mainTypeText}详情`"
              >
                <el-icon><OfficeBuilding /></el-icon>
              </el-button>

              <!-- 删除日志按钮 -->
              <el-button
                link
                style="background-color: #f56c6c;"
                @click="handleDeleteLog(log.id)"
                class="log-btn"
                :title="'删除日志'"
                v-if="isAdmin"
              >
                <el-icon><Delete /></el-icon>
              </el-button>

              <div class="log-time">{{ log.create_time }}</div>
            </div>
          </div>
          <div class="log-body">
            <div class="log-user">
              <span class="user-label">操作人:</span>
              <span class="user-value">{{ log.operator_info.id }}</span>
            </div>
            <div class="log-details">
              <span class="details-label">操作详情:</span>
              <span class="details-value">{{ formatOperationDetailsForLog(log) }}</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 空状态 -->
      <div v-if="logs.length === 0 && !loading" class="empty-log">
        暂无{{ logTypeText }}日志记录
      </div>

      <!-- 分页 -->
      <div class="log-pagination" style="margin-top: 20px; display: flex; justify-content: center;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 30, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange" @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import request from '@/utils/request';
import { formatBusinessLog } from '@/utils/logFormatter';
import { Loading, Refresh, OfficeBuilding, Delete } from '@element-plus/icons-vue';
import { isCurrentUserAdmin as checkIsCurrentUserAdmin } from '@/utils/authUtils';

// 定义Props
interface Props {
  modelValue: boolean;
  logType: string; // 日志类型：inquiry/video/image/user 等
  showStatistics?: boolean; // 是否显示统计卡片
  handleJump?: (id: number) => void; // 跳转详情的回调函数
}

const props = withDefaults(defineProps<Props>(), {
  showStatistics: true,
  handleJump: undefined  // 改为undefined，避免默认空函数
});

// 定义Emits
const emit = defineEmits(['update:modelValue', 'close']);

// 响应式数据
const loading = ref(false);
const logs = ref<any[]>([]);
const currentPage = ref(1);
const pageSize = ref(30);
const total = ref(0);
const statistics = ref({
  total_main: 0,
  total_sub: 0,
  new_main: 0,
  new_sub: 0,
  monthly_main: 0,
  monthly_sub: 0,
  last_reset_time: null
});

// 计算属性
const isAdmin = computed(() => checkIsCurrentUserAdmin());
const logTypeText = computed(() => {
  const typeMap: Record<string, string> = {
    'inquiry': '询盘',
    'video': '视频',
    'image': '图片',
    'user': '人员'
  };
  return typeMap[props.logType] || props.logType;
});

const mainTypeText = computed(() => {
  const typeMap: Record<string, string> = {
    'inquiry': '询盘',
    'video': '视频',
    'image': '图片',
    'user': '人员'
  };
  return typeMap[props.logType] || props.logType;
});

const subTypeText = computed(() => {
  const typeMap: Record<string, string> = {
    'inquiry': '沟通',
    'video': '操作',
    'image': '操作',
    'user': '操作'
  };
  return typeMap[props.logType] || '操作';
});

const dialogTitle = computed(() => `${logTypeText.value}操作日志`);

// 使用计算属性来处理对话框显示状态
const isDialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:modelValue', value);
  }
});

// 监听logType变化，当类型改变时重新加载数据
watch(
  () => props.logType,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal && props.modelValue) {
      currentPage.value = 1;
      loadLogs();
    }
  }
);

// 监听modelValue变化，当值变为true时加载数据
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && props.logType) {  // 只在显示时加载数据
      currentPage.value = 1;
      loadLogs();
    }
  },
  { immediate: true }  // 立即执行以处理初始值
);

// 加载日志数据
const loadLogs = async () => {
  if (!props.modelValue) return;  // 使用props.modelValue代替props.visible

  loading.value = true;
  try {
    const response = await request.get(`/api/${props.logType}-logs`, {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    });

    // 处理日志数据
    logs.value = response.list || [];
    total.value = response.total || 0;

    // 处理统计数据
    if (response.statistics) {
      statistics.value = {
        total_main: response.statistics[`total_${props.logType === 'inquiry' ? 'inquiries' : props.logType + 's'}`] || response.statistics.total_main || 0,
        total_sub: response.statistics[`total_${props.logType === 'inquiry' ? 'communications' : 'operations'}`] || response.statistics.total_sub || 0,
        new_main: response.statistics[`new_${props.logType === 'inquiry' ? 'inquiries' : props.logType + 's'}`] || response.statistics.new_main || 0,
        new_sub: response.statistics[`new_${props.logType === 'inquiry' ? 'communications' : 'operations'}`] || response.statistics.new_sub || 0,
        monthly_main: response.statistics[`monthly_${props.logType === 'inquiry' ? 'inquiries' : props.logType + 's'}`] || response.statistics.monthly_main || 0,
        monthly_sub: response.statistics[`monthly_${props.logType === 'inquiry' ? 'communications' : 'operations'}`] || response.statistics.monthly_sub || 0,
        last_reset_time: response.statistics.last_reset_time || null
      };
    }
  } catch (error: any) {
    console.error(`加载${logTypeText.value}日志失败:`, error);
    // 检查是否是权限错误
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      ElMessage.error('您没有权限查看日志');
      // 关闭对话框，因为用户没有权限
      emit('update:visible', false);
    } else {
      ElMessage.error(`加载${logTypeText.value}日志失败`);
    }
  } finally {
    loading.value = false;
  }
};

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  loadLogs();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadLogs();
};

// 格式化操作类型文本
const getOperationTypeText = (operationType: string) => {
  const baseMap: Record<string, string> = {
    'create': `创建${mainTypeText.value}`,
    'update': `更新${mainTypeText.value}`,
    'delete': `删除${mainTypeText.value}`,
    'restore': '恢复操作',
    'reset_stats': '复位统计数字'
  };

  // 针对视频的特殊处理
  if (props.logType === 'video') {
    baseMap['physical_delete'] = '物理删除视频';
    baseMap['restore'] = '恢复视频';
  }

  // 针对询盘的沟通记录特殊处理
  if (props.logType === 'inquiry') {
    baseMap['create_communication'] = '创建沟通记录';
    baseMap['update_communication'] = '更新沟通记录';
    baseMap['delete_communication'] = '删除沟通记录';
  }

  return baseMap[operationType] || operationType;
};

// 格式化操作详情
const formatOperationDetailsForLog = (log: any) => {
  try {
    return formatBusinessLog(log);
  } catch (error) {
    console.error('格式化日志详情失败:', error);
    if (log && log.operation_details) {
      if (typeof log.operation_details === 'object') {
        return JSON.stringify(log.operation_details);
      }
      return log.operation_details;
    }
    return '格式化失败';
  }
};

// 删除日志
const handleDeleteLog = async (logId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条日志记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await request.delete(`/api/${props.logType}-logs/${logId}`);
    ElMessage.success('日志删除成功');

    // 重新加载日志
    loadLogs();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除日志失败:', error);
      ElMessage.error('删除日志失败');
    }
  }
};

// 恢复日志数据
const handleRestoreLog = async (logId: number) => {
  try {
    await ElMessageBox.confirm('确定要恢复这条记录吗？此操作将还原被删除或修改的数据。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    const response = await request.post(`/api/${props.logType}-logs/${logId}/restore`);
    ElMessage.success(response.msg || '数据恢复成功');

    // 重新加载日志
    loadLogs();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复日志失败:', error);
      ElMessage.error('恢复日志失败');
    }
  }
};

// 清空所有日志
const clearAllLogs = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要清空所有${logTypeText.value}操作日志吗？此操作不可恢复！`,
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    await request.delete(`/api/${props.logType}-logs`);
    ElMessage.success('日志清空成功');

    // 重新加载日志
    loadLogs();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空日志失败:', error);
      ElMessage.error('清空日志失败');
    }
  }
};

// 复位统计数字
const resetStats = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要复位新增数字统计吗？此操作会将新增统计归零并记录复位时间。',
      '确认复位',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    const response = await request.post(`/api/reset-${props.logType}-stats`);
    ElMessage.success(response.message || response.msg || '统计数字复位成功');

    // 重新加载统计数据
    loadLogs();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('统计数字复位失败:', error);
      ElMessage.error('统计数字复位失败');
    }
  }
};

// 重新计算数据
const recalculateData = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重新计算统计数据吗？此操作会根据当前实际数据重新统计，可能会影响现有统计数据。',
      '确认重新计算',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    const response = await request.post(`/api/recalculate-stats`);
    ElMessage.success(response.data?.message || response.msg || '统计数据重新计算成功');

    // 重新加载统计数据
    loadLogs();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('统计数据重新计算失败:', error);
      ElMessage.error('统计数据重新计算失败');
    }
  }
};

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false);
};
</script>

<style scoped>
.log-container {
  max-height: 60vh;
  overflow-y: auto;
}

.statistics-card {
  margin-bottom: 15px;
  background-color: #f8f9fa;
}

/* 核心调整：统计内容一行显示 */
.statistics-content {
  width: 100%;
}

/* 单行布局的统计行 */
.stat-row.single-row {
  display: flex;
  align-items: center;
  justify-content: space-around; /* 均匀分布所有统计项 */
  padding: 12px 0;
  width: 100%;
  border: none; /* 移除原有的底部边框 */
  flex-wrap: wrap; /* 适配小屏幕，自动换行 */
  gap: 15px; /* 统计项之间的间距 */
}

/* 统计项样式调整 */
.stat-item-unified {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
  flex: 1; /* 让每个统计项均分宽度 */
  max-width: 120px; /* 限制最大宽度，避免拉伸过宽 */
}

.stat-label-unified {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
  text-align: center;
}

.stat-value-unified {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  text-align: center;
}

.stat-value-unified.highlight {
  color: #e6a23c;
  font-size: 20px;
}

.stat-value-unified.monthly {
  color: #909399;
  font-size: 16px;
}

.stat-label-time {
  font-size: 12px;
  color: #909399;
  background-color: #f4f4f5;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 10px;
}

.log-toolbar {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 10px;
  align-items: center;
}

.log-item {
  margin-bottom: 10px;
}

.log-card {
  padding: 12px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.log-operation-type {
  display: inline-block;
  padding: 2px 8px;
  background-color: #ecf5ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 12px;
}

.operation-type-text {
  font-weight: 500;
}

.log-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-btn {
  cursor: pointer;
  color: white;
  transition: color 0.2s;
  padding: 4px 8px;
  border-radius: 4px;
}

.log-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.log-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.log-user {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}

.user-label {
  color: #909399;
}

.user-value {
  font-weight: 500;
}

.log-details {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  font-size: 13px;
  line-height: 1.4;
}

.details-label {
  color: #909399;
  flex-shrink: 0;
}

.details-value {
  color: #606266;
  word-break: break-word;
  flex: 1;
}

.empty-log {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

/* 响应式适配：小屏幕时调整统计项大小 */
@media (max-width: 768px) {
  .stat-item-unified {
    min-width: 60px;
    max-width: 80px;
  }
  .stat-value-unified {
    font-size: 16px;
  }
  .stat-value-unified.highlight {
    font-size: 18px;
  }
}
</style>