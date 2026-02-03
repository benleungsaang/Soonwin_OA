<template>
  <el-form :model="itemForm" :rules="itemRules" ref="itemFormRef" label-width="100px">
    <el-form-item label="进度项标题" prop="title">
      <el-input v-model="itemForm.title" placeholder="请输入进度项标题" />
    </el-form-item>
    <el-form-item v-if="isEditMode" label="状态" prop="status">
      <el-select v-model="itemForm.status" placeholder="请选择状态">
        <el-option label="未完成" value="未完成" />
        <el-option label="已完成" value="已完成" />
      </el-select>
    </el-form-item>
    <!-- 仅在编辑模式下显示备注和附件上传 -->
    <el-form-item v-if="isEditMode" label="备注信息">
      <el-input v-model="itemForm.remark" type="textarea" rows="3" placeholder="请输入备注信息" />
    </el-form-item>
    <el-form-item v-if="isEditMode" label="附件上传">
      <MediaUpload
        :item-id="itemForm.id"
        :existing-media="existingMedia"
        @upload-success="handleMediaUpload"
        @delete-success="handleMediaDelete"
      />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="submitForm">提交</el-button>
      <el-button @click="resetForm">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { ProgressItem } from '@/types/order';
import { addProgressItem, updateProgressItem } from '@/api/progress';
import MediaUpload from './MediaUpload.vue';

// 接收props
interface Props {
  progressId?: string;
  editItem: ProgressItem | null;
}

const props = withDefaults(defineProps<Props>(), {
  progressId: '',
  editItem: null
});

// 计算属性：判断是否为编辑模式
const isEditMode = computed(() => !!props.editItem);

// 抛出事件
const emit = defineEmits<{
  (e: 'success'): void;
}>();

// 表单相关
const itemFormRef = ref<FormInstance>();
const itemForm = ref<Partial<ProgressItem>>({
  id: '',
  title: '',
  status: '未完成',
  remark: ''
});
const existingMedia = ref<ProgressItem['media_files']>([]);

// 表单校验规则
const itemRules: FormRules = {
  title: [{ required: true, message: '请输入进度项标题', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
};

// 初始化表单（编辑模式）
const initForm = () => {
  if (props.editItem) {
    itemForm.value = {
      id: props.editItem.id,
      title: props.editItem.title,
      status: props.editItem.status,
      remark: props.editItem.remark
    };
    existingMedia.value = [...props.editItem.media_files];
  } else {
    itemForm.value = {
      id: '',
      title: '',
      status: '未完成', // 默认为未完成
      remark: ''
    };
    existingMedia.value = [];
  }
};

// 提交表单
const submitForm = async () => {
  if (!itemFormRef.value) return;
  try {
    await itemFormRef.value.validate();

    // 新增/编辑进度项
    if (props.editItem) {
      await updateProgressItem(itemForm.value);
      ElMessage.success('进度项编辑成功');
    } else {
      // 检查是否有有效的progressId
      if (!props.progressId) {
        ElMessage.error('进度表ID不能为空，无法创建进度项');
        return;
      }

      // 新增模式下，提交进度项数据
      await addProgressItem({
        ...itemForm.value,
        progress_id: props.progressId
      } as Partial<ProgressItem>);
      ElMessage.success('进度项新增成功');
    }
    emit('success');
  } catch (error) {
    ElMessage.error('提交失败，请检查表单');
    console.error(error);
  }
};

// 重置表单
const resetForm = () => {
  if (itemFormRef.value) {
    itemFormRef.value.resetFields();
  }
  initForm();
};

// 处理文件上传成功
const handleMediaUpload = (media: ProgressItem['media_files'][0]) => {
  existingMedia.value.push(media);
};

// 处理文件删除成功
const handleMediaDelete = (mediaId: string) => {
  const index = existingMedia.value.findIndex(m => m.id === mediaId);
  if (index !== -1) {
    existingMedia.value.splice(index, 1);
  }
};

watch(() => props.editItem, () => {
  initForm();
}, { immediate: true });

onMounted(() => {
  initForm();
});
</script>