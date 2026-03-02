<template>
  <div class="attendance-system-container">
    <!-- 公共头部 -->
    <CommonHeader title="考勤系统" />

    <!-- 功能选择卡片 -->
    <el-card class="function-card">
      <template #header>
        <div class="card-header">
          <span>考勤系统功能</span>
        </div>
      </template>

      <div class="function-grid">
        <!-- 申请考勤操作 - 所有用户可见 -->
        <el-button
          type="primary"
          class="function-btn"
          @click="goToApplyAttendance"
        >
          <el-icon style="margin-right: 5px;"><DocumentAdd /></el-icon> 申请考勤操作
        </el-button>

        <!-- 考勤数据JSON导出 - 仅管理员可见 -->
        <el-button
          v-if="isCurrentUserAdmin"
          type="success"
          class="function-btn"
          @click="goToJsonExportAttendance"
        >
          <el-icon style="margin-right: 5px;"><Download /></el-icon> 导出考勤JSON
        </el-button>
      </div>
    </el-card>

    <!-- 考勤统计信息（仅管理员） -->
    <el-card v-if="isCurrentUserAdmin" class="stats-card">
      <template #header>
        <div class="card-header">
          <span>考勤统计</span>
        </div>
      </template>

      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-number">{{ stats.totalOperations }}</div>
          <div class="stat-label">总申请数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ stats.pendingApproval }}</div>
          <div class="stat-label">待审批</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ stats.approved }}</div>
          <div class="stat-label">已批准</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ stats.rejected }}</div>
          <div class="stat-label">已驳回</div>
        </div>
      </div>
    </el-card>

    <!-- 考勤操作列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>考勤操作列表</span>
        </div>
      </template>

      <el-table
        :data="operations"
        style="width: 100%"
        v-loading="loading"
        @row-click="showOperationDetail"
      >
        <!-- <el-table-column v-if="isCurrentUserAdmin" prop="emp_id" label="工号" width="120" />
        <el-table-column v-if="isCurrentUserAdmin" prop="name" label="姓名" width="120" /> -->
        <el-table-column prop="name" label="姓名" width="120">
          <template #default="scope">
            {{ scope.row.name }}
          </template>
        </el-table-column>
        <el-table-column prop="operation_type" label="操作类型" width="120">
          <template #default="scope">
            {{ getOperationTypeLabel(scope.row.operation_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="事由" width="200" show-overflow-tooltip />
        <el-table-column prop="start_time" label="开始时间" width="150">
          <template #default="scope">
            {{ formatDate(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="150">
          <template #default="scope">
            {{ formatDate(scope.row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长(小时)" width="100" />
        <el-table-column prop="operation_status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.operation_status)">
              {{ getStatusLabel(scope.row.operation_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="申请时间" width="150">
          <template #default="scope">
            {{ formatDate(scope.row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click.stop="showOperationDetail(scope.row)"
            >
              <el-icon style="margin-right: 5px;"><Search /></el-icon> 查看
            </el-button>
            <!-- 删除按钮：管理员可删除所有，本人可删除自己的 -->
            <el-button
              v-if="canDelete(scope.row)"
              size="small"
              type="danger"
              @click.stop="deleteOperation(scope.row)"
            >
              <el-icon style="margin-right: 5px;"><Delete /></el-icon> 删除
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

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`考勤申请详情 - ${selectedOperation?.reason || ''}`"
      :width="isMobile ? '95%' : '60%'"
      :before-close="closeDetailDialog"
    >
      <div v-if="selectedOperation">
        <el-descriptions :column="isMobile ? 1 : 2" border>
          <el-descriptions-item label="操作类型">
            {{ getOperationTypeLabel(selectedOperation.operation_type) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="isCurrentUserAdmin" label="员工姓名">
            {{ selectedOperation.name }} ( id: {{ selectedOperation.emp_id }} )
          </el-descriptions-item>
          <!-- <el-descriptions-item v-if="isCurrentUserAdmin" label="员工工号">
            {{ selectedOperation.emp_id }}
          </el-descriptions-item> -->
          <el-descriptions-item label="开始时间">
            {{ formatDate(selectedOperation.start_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ formatDate(selectedOperation.end_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="时长(小时)">
            {{ selectedOperation.duration }}
          </el-descriptions-item>
          <el-descriptions-item :span="2" label="事由">
            {{ selectedOperation.reason }}
          </el-descriptions-item>
          <!-- <el-descriptions-item :span="2" label="扩展信息">
            <pre>{{ JSON.stringify(selectedOperation.extend_info, null, 2) }}</pre>
          </el-descriptions-item> -->
          <el-descriptions-item :span="2" label="附件">
            <div v-if="selectedOperation.attachment && selectedOperation.attachment.length > 0">
              <div class="attachment-preview-container">
                <div
                  v-for="(file, index) in selectedOperation.attachment"
                  :key="index"
                  class="attachment-item"
                >
                  <!-- 判断是否为图片 -->
                  <div v-if="isImageFile(file)" class="image-attachment">
                    <el-image
                      :src="file"
                      :preview-src-list="getImageAttachments(selectedOperation.attachment)"
                      :initial-index="getImageIndex(selectedOperation.attachment, file)"
                      preview-teleported
                      close-on-press-esc
                      hide-on-click-modal
                      style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px; cursor: pointer;"
                      :alt="getFileName(file)"
                      @click="handleImageClick(file)"
                    />
                    <!-- <div class="file-name">{{ getFileName(file) }}</div> -->
                  </div>
                  <!-- 非图片文件 -->
                  <div v-else class="other-attachment">
                    <el-link
                      :href="file"
                      type="primary"
                      :underline="false"
                      target="_blank"
                      style="display: flex; align-items: center; margin-bottom: 5px;"
                    >
                      <el-icon style="margin-right: 5px;"><Document /></el-icon>
                      {{ getFileName(file) }}
                    </el-link>
                  </div>
                </div>
              </div>
            </div>
            <div v-else>无附件</div>
          </el-descriptions-item>
          <el-descriptions-item label="申请时间">
            {{ formatDate(selectedOperation.create_time) }}
          </el-descriptions-item>
          <!-- <el-descriptions-item label="更新时间">
            {{ formatDate(selectedOperation.update_time) }}
          </el-descriptions-item> -->
          </el-descriptions>
        <br>
        <el-descriptions
        title="审批信息"
        :column="isMobile ? 1 : 2"
        border>
          <el-descriptions-item v-if="selectedOperation.approver_name" label="审批人">
            {{ selectedOperation.approver_name }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedOperation.approve_time" label="审批时间">
            {{ formatDate(selectedOperation.approve_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <div style="display: flex; align-items: center; gap: 10px;">
              <el-tag :type="getStatusTagType(selectedOperation.operation_status)">
                {{ getStatusLabel(selectedOperation.operation_status) }}
              </el-tag>
              <!-- 审批按钮仅对管理员显示 -->
              <el-button
                v-if="isCurrentUserAdmin && canApprove(selectedOperation)"
                size="small"
                type="warning"
                @click="showApprovalModal(selectedOperation)"
              >
                <el-icon style="margin-right: 5px;"><Memo /></el-icon> 审批
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedOperation.approve_opinion" :span="2" label="审批意见">
            {{ selectedOperation.approve_opinion }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 审批意见弹窗 -->
    <el-dialog
      v-model="approvalDialogVisible"
      :title="approvalDialogTitle"
      width="500px"
    >
      <el-form :model="approvalForm">
        <el-form-item label="审批操作" required>
          <el-radio-group v-model="approvalForm.action">
            <el-radio :value="OperationStatus.APPROVED" >批准</el-radio>
            <el-radio :value="OperationStatus.REJECTED" >驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input
            v-model="approvalForm.opinion"
            type="textarea"
            :rows="4"
            placeholder="请输入审批意见（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeApprovalDialog">取消</el-button>
          <el-button type="primary" @click="confirmApproval">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { DocumentAdd, Search, Document, Delete, Memo, Download } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';
import { hasModulePermission, ModuleNames, getCurrentUserRole, getCurrentUserEmpId } from '@/utils/authUtils';
import { getOperations, approveOperation as apiApproveOperation, deleteOperation as apiDeleteOperation } from '@/api/attendance';
import { OperationType, OperationStatus, AttendanceOperation } from '@/types/attendance';

// 路由实例
const router = useRouter();

// 考勤统计信息
const stats = ref({
  totalOperations: 0,
  pendingApproval: 0,
  approved: 0,
  rejected: 0
});

// 考勤操作列表相关
const operations = ref<AttendanceOperation[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const detailDialogVisible = ref(false);
const selectedOperation = ref<AttendanceOperation | null>(null);
const windowWidth = ref(window.innerWidth);

// 审批相关
const approvalDialogVisible = ref(false);
const approvalDialogTitle = ref('');
const approvalForm = ref({
  opinion: '',
  action: '' as 'approved' | 'rejected'
});

// 计算属性：判断当前用户是否为管理员
const isCurrentUserAdmin = computed(() => {
  return getCurrentUserRole() === 'admin';
});

// 计算属性：判断是否为移动端
const isMobile = computed(() => windowWidth.value < 768);

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

// 跳转到考勤操作申请页面
const goToApplyAttendance = () => {
  router.push('/attendance/apply');
};

// 加载考勤统计信息
const loadStats = () => {
  try {
    // 使用已加载的operations数据
    const allOperations = operations.value;

    // 统计信息
    stats.value.totalOperations = allOperations.length;
    stats.value.pendingApproval = allOperations.filter(op =>
      op.operation_status === 'approving' || op.operation_status === 'submitted'
    ).length;
    stats.value.approved = allOperations.filter(op => op.operation_status === 'approved').length;
    stats.value.rejected = allOperations.filter(op => op.operation_status === 'rejected').length;
  } catch (error) {
    console.error('加载考勤统计信息失败:', error);
  }
};

// 审批操作后更新统计信息
const updateStatsAfterApproval = (oldStatus: string, newStatus: string) => {
  // 减少旧状态的计数
  if (oldStatus === 'submitted' || oldStatus === 'approving') {
    stats.value.pendingApproval--;
  } else if (oldStatus === 'approved') {
    stats.value.approved--;
  } else if (oldStatus === 'rejected') {
    stats.value.rejected--;
  }

  // 增加新状态的计数
  if (newStatus === 'submitted' || newStatus === 'approving') {
    stats.value.pendingApproval++;
  } else if (newStatus === 'approved') {
    stats.value.approved++;
  } else if (newStatus === 'rejected') {
    stats.value.rejected++;
  }
};
// 获取考勤操作列表
const fetchOperations = async () => {
  loading.value = true;

  try {
    const response = await getOperations({});
    operations.value = response || [];
    total.value = operations.value.length;
  } catch (error) {
    console.error('获取考勤操作列表失败:', error);
    ElMessage.error('获取考勤操作列表失败');
  } finally {
    loading.value = false;
  }
};

// 格式化日期
const formatDate = (dateString: string | null) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN');
};

// 获取操作类型标签
const getOperationTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    [OperationType.LEAVE]: '请假',
    [OperationType.OVERTIME]: '加班',
    [OperationType.MAKE_UP]: '补卡',
    [OperationType.APPEAL]: '申诉',
    [OperationType.BUSINESS_TRIP]: '出差',
    [OperationType.ADJUST]: '调整'
  };
  return labels[type] || type;
};

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    [OperationStatus.DRAFT]: 'info',
    [OperationStatus.SUBMITTED]: 'warning',
    [OperationStatus.APPROVING]: 'warning',
    [OperationStatus.APPROVED]: 'success',
    [OperationStatus.REJECTED]: 'danger',
    [OperationStatus.CANCELLED]: 'info'
  };
  return types[status] || 'info';
};

// 获取状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    [OperationStatus.DRAFT]: '草稿',
    [OperationStatus.SUBMITTED]: '待审批',
    [OperationStatus.APPROVING]: '审批中',
    [OperationStatus.APPROVED]: '已批准',
    [OperationStatus.REJECTED]: '已驳回',
    [OperationStatus.CANCELLED]: '已撤销'
  };
  return labels[status] || status;
};

// 判断是否可以审批
const canApprove = (row: AttendanceOperation) => {
  return row.operation_status === OperationStatus.SUBMITTED || row.operation_status === OperationStatus.APPROVING;
};

// 显示操作详情
const showOperationDetail = (row: AttendanceOperation) => {
  selectedOperation.value = { ...row };
  detailDialogVisible.value = true;
};

// 显示审批模态框
const showApprovalModal = (row: AttendanceOperation) => {
  selectedOperation.value = { ...row };
  approvalForm.value.opinion = '';
  approvalForm.value.action = 'approved'; // 默认选择批准
  approvalDialogTitle.value = `审批 - ${row.reason}`;
  approvalDialogVisible.value = true;
};

// 审批操作
const approveOperation = (row: AttendanceOperation, action: 'approved' | 'rejected') => {
  selectedOperation.value = { ...row };
  approvalForm.value.opinion = '';
  approvalForm.value.action = action;
  approvalDialogTitle.value = action === 'approved' ? '批准操作' : '驳回操作';
  approvalDialogVisible.value = true;
};

// 确认审批
const confirmApproval = async () => {
  if (!selectedOperation.value) {
    ElMessage.error('未选择要审批的操作');
    return;

  }



  if (!approvalForm.value.action) {

    ElMessage.error('请选择审批操作');

    return;

  }



  try {

        const response = await apiApproveOperation(selectedOperation.value.id, {

          status: approvalForm.value.action === 'approved' ? OperationStatus.APPROVED : OperationStatus.REJECTED,

          opinion: approvalForm.value.opinion

        });



    if (response) {

      ElMessage.success(approvalForm.value.action === 'approved' ? '批准成功' : '驳回成功');

      approvalDialogVisible.value = false;

      // 重置表单

      approvalForm.value.opinion = '';

      approvalForm.value.action = 'approved';



      // 使用后端返回的完整数据更新详情框，这样可以确保所有信息都同步

      if (selectedOperation.value && response) {

        // 将返回的更新后数据复制到当前选中的操作

        Object.assign(selectedOperation.value, response);

      }

      // 直接更新本地列表中的对应项
      const index = operations.value.findIndex(op => op.id === selectedOperation.value?.id);
      if (index !== -1) {
        // 更新本地操作数据
        Object.assign(operations.value[index], response);
        // 直接更新统计信息
        updateStatsAfterApproval(selectedOperation.value.operation_status, response.operation_status);
      }

    } else {

      ElMessage.error(approvalForm.value.action === 'approved' ? '批准失败' : '驳回失败');

    }

  } catch (error) {

    console.error('审批操作失败:', error);

    ElMessage.error(approvalForm.value.action === 'approved' ? '批准失败' : '驳回失败');

  }

};

// 关闭详情弹窗
const closeDetailDialog = () => {
  detailDialogVisible.value = false;
  selectedOperation.value = null;
};

// 关闭审批弹窗
const closeApprovalDialog = () => {
  approvalDialogVisible.value = false;
  // 重置表单
  approvalForm.value.opinion = '';
        approvalForm.value.action = 'approved';  selectedOperation.value = null;
};

// 判断是否可以删除
const canDelete = (row: AttendanceOperation) => {
  // 管理员可以删除所有记录
  if (isCurrentUserAdmin.value) {
    return true;
  }
  // 普通用户只能删除自己的记录，并且状态为草稿或已提交（未审批）
  return row.emp_id === getCurrentUserEmpId() &&
         (row.operation_status === OperationStatus.DRAFT ||
          row.operation_status === OperationStatus.SUBMITTED);
};

// 删除考勤操作
const deleteOperation = async (row: AttendanceOperation) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除考勤申请 "${row.reason}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await apiDeleteOperation(row.id);

    ElMessage.success('删除成功');
    // 重新获取列表
    fetchOperations();
    // 如果是管理员页面，也重新加载统计信息
    if (isCurrentUserAdmin.value) {
      loadStats();
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除考勤操作失败:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 分页相关方法
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  fetchOperations();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  fetchOperations();
};

// 页面挂载时加载数据
onMounted(async () => {
  window.addEventListener('resize', handleResize);
  await fetchOperations(); // 加载考勤操作列表
  if (isCurrentUserAdmin.value) {
    loadStats(); // 加载统计信息（仅管理员）
  }
});

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// 跳转到考勤JSON导出页面
const goToJsonExportAttendance = () => {
  router.push('/attendance/json-export');
};

// 判断是否为图片文件
const isImageFile = (file: string) => {
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];
  const fileExtension = file.toLowerCase().substring(file.lastIndexOf('.'));
  return imageExtensions.includes(fileExtension);
};

// 获取图片附件列表
const getImageAttachments = (attachments: string[]) => {
  return attachments.filter(file => isImageFile(file));
};

// 获取图片在附件列表中的索引
const getImageIndex = (attachments: string[], currentFile: string) => {
  const imageAttachments = getImageAttachments(attachments);
  return imageAttachments.indexOf(currentFile);
};

// 获取文件名
const getFileName = (file: string) => {
  return file.split('/').pop() || file;
};

// 处理图片点击事件
const handleImageClick = (file: string) => {
  // 这个事件由 el-image 组件自己处理预览
  // 当前函数可以用于其他交互逻辑
};
</script>

<style scoped>
.attendance-system-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.function-card {
  margin-bottom: 20px;
}

.list-card {
  margin-top: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.function-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

.function-btn {
  width: 100%;
  height: 80px;
  font-size: 16px;
}

.stats-card {
  margin-top: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

/* 附件预览容器样式 */
.attachment-preview-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.attachment-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 10px;
}

.image-attachment {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.file-name {
  margin-top: 5px;
  font-size: 12px;
  text-align: center;
  word-break: break-all;
  max-width: 100px;
  color: #606266;
}

.other-attachment {
  display: flex;
  align-items: center;
}

.other-attachment .el-link {
  width: 100%;
}

@media (max-width: 768px) {
  .function-grid {
    grid-template-columns: 1fr;
  }

  .el-form-item {
    margin-bottom: 10px;
  }
}
</style>