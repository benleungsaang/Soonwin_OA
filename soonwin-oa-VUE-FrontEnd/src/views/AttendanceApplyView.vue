<template>
  <div class="attendance-apply-container">
    <!-- 公共头部 -->
    <CommonHeader title="申请考勤操作" />

    <!-- 申请表单 -->
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>考勤操作申请</span>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" style="max-width: 800px;">
        <!-- 操作类型选择 -->
        <el-form-item label="操作类型" prop="operation_type" required>
          <el-radio-group v-model="form.operation_type" @change="onOperationTypeChange">
            <el-radio :value="OperationType.LEAVE">请假</el-radio>
            <!-- <el-radio :value="OperationType.OVERTIME">加班</el-radio> -->
            <el-radio :value="OperationType.MAKE_UP">补卡</el-radio>
            <!-- <el-radio :value="OperationType.APPEAL">申诉</el-radio> -->
            <el-radio :value="OperationType.BUSINESS_TRIP">出差</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 动态扩展信息 -->
        <template v-if="form.operation_type === OperationType.LEAVE">
          <!-- 请假类型 -->
          <el-form-item label="请假类型" prop="extend_info.leave_type" required>
            <el-select v-model="form.extend_info.leave_type"
            placeholder="请选择请假类型"
        >
              <el-option label="事假" value="personal"></el-option>
              <el-option label="病假" value="sick"></el-option>
              <el-option label="年假" value="annual"></el-option>
              <el-option label="调休" value="compensatory"></el-option>
              <el-option label="婚假" value="marriage"></el-option>
              <el-option label="产假" value="maternity"></el-option>
              <el-option label="陪产假" value="paternity"></el-option>
              <el-option label="丧假" value="bereavement"></el-option>
            </el-select>
          </el-form-item>
        </template>

        <template v-if="form.operation_type === OperationType.MAKE_UP">
          <!-- 补卡类型 -->
          <el-form-item label="补卡类型" prop="extend_info.make_up_type" required>
            <el-radio-group v-model="form.extend_info.make_up_type">
              <el-radio value="clockin">上班打卡</el-radio>
              <el-radio value="clockout">下班打卡</el-radio>
            </el-radio-group>
          </el-form-item>
        </template>

        <template v-if="form.operation_type === OperationType.BUSINESS_TRIP">
          <!-- 出差地点和目的 -->
          <el-form-item label="出差地点" prop="extend_info.trip_place" required>
            <el-input v-model="form.extend_info.trip_place" placeholder="请输入出差地点"></el-input>
          </el-form-item>
          <el-form-item label="出差目的" prop="extend_info.trip_purpose" required>
            <el-input v-model="form.extend_info.trip_purpose" placeholder="请输入出差目的"></el-input>
          </el-form-item>
        </template>

        <!-- 时间选择 -->
        <el-form-item label="时间范围" prop="time_range">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            :default-time="defaultTimeRange"
            style="width: 100%;"
            @change="onTimeRangeChange"
          />
        </el-form-item>

        <!-- 自动计算时长 -->
        <el-form-item label="时长(小时)">
          <el-input :value="durationHours" disabled placeholder="自动计算"></el-input>
        </el-form-item>

        <!-- 原因/事由 -->
        <el-form-item label="原因/事由" prop="reason" required>
          <el-input
            v-model="form.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入请假/加班/补卡/申诉/出差的原因"
          />
        </el-form-item>

        <!-- 附件上传 -->
        <el-form-item label="附件上传">
          <ImageUploadPreview
            :upload-immediately="false"
            @upload-success="onFilesSelected"
          />
          <div style="margin: 10px; color: #999; font-size: 12px;">图片上传</div>

          <!-- 已选择附件列表 -->
          <div v-if="selectedFiles.length > 0" class="selected-files-list">
            <div
              v-for="(file, index) in selectedFiles"
              :key="index"
              class="selected-file-item"
            >
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
              <el-button
                size="small"
                type="danger"
                @click="removeSelectedFile(index)"
                style="margin-left: 10px;"
              >
                删除
              </el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <!-- 底部操作按钮 -->
      <div class="form-footer">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="submitForm">提交申请</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus';
import { OperationType, OperationStatus, AttendanceOperationForm } from '@/types/attendance';
import { submitOperation, uploadAttendanceAttachment } from '@/api/attendance';
import CommonHeader from '@/components/CommonHeader.vue';
import ImageUploadPreview from '@/components/ImageUploadPreview.vue';
import { getCurrentUserEmpId, getCurrentUserName } from '@/utils/authUtils';
import { Upload, Document } from '@element-plus/icons-vue';

// 路由实例
const router = useRouter();

// 默认时间设置
const defaultStartTime = new Date(2000, 1, 1, 8, 30, 0); // '08:30:00'
const defaultEndTime = new Date(2000, 1, 1, 17, 30, 0); // '17:30:00'

// 时间范围默认值
const defaultTimeRange: [Date, Date] = [defaultStartTime, defaultEndTime];

// 时间范围
const timeRange = ref<[string, string] | null>(null);

// 表单数据
const form = ref<AttendanceOperationForm>({
  emp_id: '',
  name: '',
  operation_type: OperationType.LEAVE,
  start_time: '',
  end_time: '',
  reason: '',
  extend_info: {
    leave_type: 'personal',  // 默认请假类型为事假
    make_up_type: 'clockin',  // 默认请假类型为事假
  },
});

// 表单引用
const formRef = ref<FormInstance>();

// 上传附件相关
const selectedFiles = ref<File[]>([]);

// 表单验证规则
const rules = computed<FormRules>(() => {
  const baseRules: FormRules = {
    operation_type: [
      { required: true, message: '请选择操作类型', trigger: 'change' }
    ],
    reason: [
      { required: true, message: '请输入原因/事由', trigger: 'blur' }
    ]
  };

  // 只在请假操作时验证请假类型
  switch (form.value.operation_type) {
    case OperationType.LEAVE:
      baseRules['extend_info.leave_type'] = [
        { required: true, message: '请选择请假类型', trigger: 'change' }
      ];
      break;
    case OperationType.MAKE_UP:
      baseRules['extend_info.make_up_type'] = [
        { required: true, message: '请选择补卡类型', trigger: 'change' }
      ];
      break;
    case OperationType.BUSINESS_TRIP:
      baseRules['extend_info.trip_place'] = [
        { required: true, message: '请输入出差地点', trigger: 'blur' }
      ];
      baseRules['extend_info.trip_purpose'] = [
        { required: true, message: '请输入出差目的', trigger: 'blur' }
      ];
      break;
  }

  return baseRules;
});

// 计算时长（小时）- 按系统设置的默认时间范围计算
const durationHours = computed(() => {
  if (form.value.start_time && form.value.end_time) {
    const start = new Date(form.value.start_time);
    const end = new Date(form.value.end_time);
    
    // 计算总时长
    const totalDiffMs = end.getTime() - start.getTime();
    const totalDiffHours = totalDiffMs / (1000 * 60 * 60);
    
    // 如果时间范围跨天，需要分天计算
    const duration = calculateWorkingHours(start, end);
    
    form.value.duration = duration;
    return duration.toFixed(2);
  }
  form.value.duration = undefined;
  return '';
});

// 按工作时间计算时长（每天最多7.5小时，中午12-13点不算）
const calculateWorkingHours = (startTime: Date, endTime: Date): number => {
  if (startTime > endTime) {
    return 0;
  }
  
  let current = new Date(startTime);
  let totalHours = 0;
  
  // 计算跨越的每一天
  while (current < endTime) {
    // 获取当天的开始和结束工作时间
    const dayStart = new Date(current);
    dayStart.setHours(0, 0, 0, 0); // 当天零点
    
    const dayEnd = new Date(current);
    dayEnd.setHours(23, 59, 59, 999); // 当天23:59:59
    
    // 实际计算工作时间的区间
    const actualStart = current > dayStart ? current : dayStart;
    const actualEnd = endTime < dayEnd ? endTime : dayEnd;
    
    // 计算当天的工作时长
    const dayHours = calculateWorkingHoursForDay(actualStart, actualEnd);
    totalHours += dayHours;
    
    // 移动到下一天
    const nextDay = new Date(current);
    nextDay.setDate(nextDay.getDate() + 1);
    nextDay.setHours(0, 0, 0, 0);
    
    if (current >= nextDay) {
      // 防止无限循环
      break;
    }
    current = nextDay;
  }
  
  return totalHours;
};

// 计算单天的工作时长（每天最多7.5小时，中午12-13点不算）
const calculateWorkingHoursForDay = (dayStart: Date, dayEnd: Date): number => {
  // 如果跨天，则只计算当天的时长
  const startDay = new Date(dayStart);
  startDay.setHours(0, 0, 0, 0);
  
  const endDay = new Date(dayEnd);
  endDay.setHours(0, 0, 0, 0);
  
  if (startDay.getTime() !== endDay.getTime()) {
    // 如果跨天，则重新调整为单天范围
    const actualDayEnd = new Date(dayStart);
    actualDayEnd.setHours(23, 59, 59, 999);
    return calculateWorkingHoursForDay(dayStart, actualDayEnd);
  }
  
  // 工作时间段：00:00-12:00 和 13:00-24:00
  const workStart1 = new Date(dayStart);
  workStart1.setHours(0, 0, 0, 0); // 当天 00:00:00
  const workEnd1 = new Date(dayStart);
  workEnd1.setHours(12, 0, 0, 0); // 当天 12:00:00
  
  const workStart2 = new Date(dayStart);
  workStart2.setHours(13, 0, 0, 0); // 当天 13:00:00
  const workEnd2 = new Date(dayStart);
  workEnd2.setHours(23, 59, 59, 999); // 当天 23:59:59
  
  let hours = 0;
  
  // 计算第一个工作时间段 (00:00-12:00) 的有效时间
  if (dayStart < workEnd1 && dayEnd > workStart1) {
    const start = dayStart > workStart1 ? dayStart : workStart1;
    const end = dayEnd < workEnd1 ? dayEnd : workEnd1;
    const diff = end.getTime() - start.getTime();
    hours += diff / (1000 * 60 * 60);
  }
  
  // 计算第二个工作时间段 (13:00-24:00) 的有效时间
  if (dayStart < workEnd2 && dayEnd > workStart2) {
    const start = dayStart > workStart2 ? dayStart : workStart2;
    const end = dayEnd < workEnd2 ? dayEnd : workEnd2;
    const diff = end.getTime() - start.getTime();
    hours += diff / (1000 * 60 * 60);
  }
  
  // 每天最多7.5小时
  return Math.min(hours, 7.5);
};

// 时间范围变化处理
const onTimeRangeChange = (value: [string, string] | null) => {
  if (value) {
    form.value.start_time = value[0];
    form.value.end_time = value[1];
  } else {
    form.value.start_time = '';
    form.value.end_time = '';
  }
};

// 操作类型改变时的处理
const onOperationTypeChange = async (value: string) => {
  // 清空扩展信息中与当前操作类型无关的字段
  if (value !== OperationType.LEAVE) {
    delete form.value.extend_info.leave_type;
  }
  if (value !== OperationType.MAKE_UP) {
    delete form.value.extend_info.make_up_type;
  }
  if (value !== OperationType.BUSINESS_TRIP) {
    delete form.value.extend_info.trip_place;
    delete form.value.extend_info.trip_purpose;
  }

  // 如果当前有表单引用，清除相关字段的验证状态
  if (formRef.value) {
    // 清除所有扩展信息字段的验证状态
    await formRef.value.clearValidate([
      'extend_info.leave_type',
      'extend_info.make_up_type',
      'extend_info.trip_place',
      'extend_info.trip_purpose'
    ]);
  }

  // 为请假类型设置默认值
  if (value === OperationType.LEAVE && !form.value.extend_info.leave_type) {
    form.value.extend_info.leave_type = 'personal';
  }
  if (value === OperationType.MAKE_UP && !form.value.extend_info.make_up_type) {
    form.value.extend_info.make_up_type = 'clockin';
  }


};

// 处理文件选择
const onFilesSelected = (files: File[], mediaFiles: any[]) => {
  // 将新选择的文件添加到已选择的文件列表
  selectedFiles.value = [...selectedFiles.value, ...files];
  ElMessage.success(`已添加 ${files.length} 个附件文件`);
};

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 移除已选择的文件
const removeSelectedFile = (index: number) => {
  selectedFiles.value.splice(index, 1);
};

// 提交表单
const submitForm = async () => {
  // 验证表单（不包括时间范围，因为我们会单独检查）
  if (!formRef.value) return;

  // 检查时间范围是否已选择
  if (!timeRange.value || !timeRange.value[0] || !timeRange.value[1]) {
    ElMessage.error('请选择时间范围');
    return;
  }

  try {
    // 验证表单其他字段
    await formRef.value.validate();
  } catch (error) {
    console.error('表单验证失败:', error);
    ElMessage.error('请检查表单填写内容');
    return;
  }

  // 确保时间范围已设置到表单数据
  if (timeRange.value) {
    form.value.start_time = timeRange.value[0];
    form.value.end_time = timeRange.value[1];
  }

  try {
    // 如果有附件需要上传
    let attachmentPaths: string[] = [];
    if (selectedFiles.value.length > 0) {
      // 上传附件
      attachmentPaths = await uploadAttachments(selectedFiles.value);
    }

    // 设置附件
    if (attachmentPaths.length > 0) {
      form.value.attachment = attachmentPaths;
    }

    // 设置操作状态为已提交
    form.value.operation_status = OperationStatus.SUBMITTED;

    // 提交申请
    const response = await submitOperation(form.value);

    if (response) {
      ElMessage.success('申请提交成功');
      // 跳转到考勤系统主页
      router.push('/attendance-system');
    } else {
      ElMessage.error('申请提交失败');
    }
  } catch (error) {
    console.error('提交申请失败:', error);
    ElMessage.error('申请提交失败');
  }
};

// 上传附件文件
const uploadAttachments = async (files: File[]): Promise<string[]> => {
  const uploadPromises = files.map(async (file) => {
    try {
      // 使用API函数上传附件
      const response = await uploadAttendanceAttachment(file, form.value.emp_id, form.value.operation_type);

      // 检查响应状态
      if (response) {
        // 返回文件路径
        return response.path;
      } else {
        throw new Error(`文件 ${file.name} 上传失败`);
      }
    } catch (error) {
      console.error(`上传文件 ${file.name} 失败:`, error);
      throw new Error(`文件 ${file.name} 上传失败`);
    }
  });

  try {
    return await Promise.all(uploadPromises);
  } catch (error) {
    console.error('上传附件失败:', error);
    throw error;
  }
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 页面挂载时初始化表单数据
onMounted(() => {
  // 获取当前用户信息
  const empId = getCurrentUserEmpId();
  const userName = getCurrentUserName();

  if (empId) {
    form.value.emp_id = empId;
  }

  if (userName) {
    form.value.name = userName;
  }

  // 设置默认时间范围
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 8, 30, 0);
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 17, 30, 0);

  timeRange.value = [
    todayStart.toISOString().slice(0, 19).replace('T', ' '),
    todayEnd.toISOString().slice(0, 19).replace('T', ' ')
  ];

  // 同时设置到表单
  form.value.start_time = timeRange.value[0];
  form.value.end_time = timeRange.value[1];
});</script>

<style scoped>
.attendance-apply-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.form-card {
  max-width: 900px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.form-footer {
  text-align: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #dcdfe6;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
  background-color: #fafafa;
}

.upload-area:hover {
  border-color: #409eff;
}

.upload-area.drag-over {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-content .el-icon {
  font-size: 48px;
  color: #8c939d;
  margin-bottom: 16px;
}

.upload-content p {
  margin: 0 0 8px;
  font-size: 14px;
  color: #606266;
}

.upload-hint {
  color: #909399 !important;
  font-size: 12px !important;
}

.selected-files-list {
  margin-top: 15px;
}

.selected-file-item {
  display: flex;
  align-items: center;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.file-name {
  flex: 1;
  margin-left: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
  white-space: nowrap;
}
</style>