<template>
  <div
    class="image-upload-preview-container"
    :class="{ 'tooltip-disabled': confirmDialogVisible }"
  >
    <!-- 图片拖拽区域 -->
    <div
      class="drop-area"
      :class="{ 'drag-over': isDragOver }"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      @click="triggerFileSelect"
      @mouseenter.stop
      @mouseleave.stop
    >
      <el-icon><Camera /></el-icon>
      <input
        ref="fileInputRef"
        type="file"
        multiple
        accept="image/*"
        style="display: none"
        @change="handleFileSelect"
      />
    </div>

    <!-- 图片上传确认对话框 -->
    <el-dialog
      v-model="confirmDialogVisible"
      title="确认上传图片"
      width="80%"
      :before-close="closeConfirmDialog"
      @mouseenter.stop
      @mouseleave.stop
      append-to-body
      :modal-append-to-body="true"
    >
      <!-- 重构：标题栏添加选中数量提示 -->
      <template #header>
        <div class="dialog-header-custom">
          <span class="dialog-title">确认上传图片</span>
          <span class="selected-count-text">当前已选择 {{ selectedCount }} 张图片</span>
        </div>
      </template>

      <div class="confirm-dialog-content">
        <!-- 修复：最多4列的网格布局 -->
        <div class="confirm-grid">
          <div
            v-for="(image, index) in selectedImages"
            :key="index"
            class="confirm-image-item"
          >
            <el-image
              :src="image.url"
              :preview-src-list="previewList"
              :initial-index="index"
              preview-teleported
              hide-on-click-modal
              close-on-press-esc
              class="confirm-preview-image"
            />
            <!-- 重构信息区域：内容居中 -->
            <div class="confirm-image-info">
              <el-checkbox v-model="image.selected" class="info-checkbox" />
              <span class="file-name">{{ image.file.name }}</span>
              <span class="file-size">{{ formatFileSize(image.file.size) }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeConfirmDialog">取消</el-button>
          <!-- 合并全选/取消全选按钮 -->
          <el-button @click="toggleSelectAll">{{ isAllSelected ? '取消全选' : '全选' }}</el-button>
          <el-button type="primary" @click="confirmUpload">确认上传</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Camera } from '@element-plus/icons-vue';
import request from '@/utils/request';

// 定义组件的 props
interface Props {
  taskId?: number;
}

const props = withDefaults(defineProps<Props>(), {
  taskId: undefined
});

// 定义组件的事件
const emit = defineEmits<{
  'upload-success': [files: File[]];
  'upload-failure': [error: any];
}>();

// 响应式数据
const selectedImages = ref<{ file: File; url: string; selected: boolean }[]>([]);
const isDragOver = ref(false);
const confirmDialogVisible = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

// 计算属性：生成预览列表
const previewList = computed(() => {
  return selectedImages.value
    .filter(image => image.selected)
    .map(image => image.url);
});

// 计算属性：当前选中的图片数量
const selectedCount = computed(() => {
  return selectedImages.value.filter(image => image.selected).length;
});

// 计算属性：判断是否全选
const isAllSelected = computed(() => {
  // 空列表时返回false
  if (selectedImages.value.length === 0) return false;
  // 检查所有图片是否都被选中
  return selectedImages.value.every(image => image.selected);
});

// 处理拖拽相关事件
const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = true;
};

const handleDragLeave = (e: DragEvent) => {
  // 使用relatedTarget检查鼠标是否移出拖拽区域
  if (!e.currentTarget || !e.relatedTarget || !(e.currentTarget as HTMLElement).contains(e.relatedTarget as Node)) {
    isDragOver.value = false;
  }
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = false;

  if (e.dataTransfer?.files) {
    handleFiles(e.dataTransfer.files);
  }
};

// 触发文件选择器
const triggerFileSelect = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};

// 处理文件选择
const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files) {
    handleFiles(target.files);
  }
};

// 处理文件
const handleFiles = (files: FileList) => {
  if (files.length === 0) return;

  // 验证文件类型
  const validFiles: File[] = [];
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (file.type.startsWith('image/')) {
      validFiles.push(file);
    } else {
      ElMessage.warning(`文件 ${file.name} 不是图片格式，已跳过`);
    }
  }

  if (validFiles.length === 0) return;

  // 将文件转换为预览对象
  const newImages = validFiles.map(file => ({
    file,
    url: URL.createObjectURL(file),
    selected: true // 默认全选
  }));

  // 添加到已选择的图片列表
  selectedImages.value = [...selectedImages.value, ...newImages];

  ElMessage.success(`已选择 ${newImages.length} 张图片`);

  // 核心修改：处理完文件后直接打开确认对话框
  confirmDialogVisible.value = true;
};

// 关闭确认对话框（修改：关闭时清空图片）
const closeConfirmDialog = () => {
  confirmDialogVisible.value = false;
  // 清空已选择的图片，避免重复添加
  clearSelectedImages();
};

// 切换全选/取消全选状态
const toggleSelectAll = () => {
  const targetState = !isAllSelected.value;
  selectedImages.value.forEach(image => {
    image.selected = targetState;
  });
};

// 确认上传
const confirmUpload = async () => {
  if (!props.taskId) {
    ElMessage.error('未指定任务ID');
    return;
  }

  // 获取选中的文件
  const selectedFiles = selectedImages.value
    .filter(image => image.selected)
    .map(image => image.file);

  if (selectedFiles.length === 0) {
    ElMessage.warning('请至少选择一张图片');
    return;
  }

  try {
    // 创建FormData对象并添加所有选定的文件
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file); // 后端使用getlist获取多个文件
    });
    formData.append('task_id', props.taskId.toString());

    // 调用后端批量上传API
    const response: any = await request.post('/api/order-status/upload-multiple-images', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    ElMessage.success(`${selectedFiles.length} 张图片上传成功`);
    emit('upload-success', selectedFiles);

    // 清空已选择的图片
    clearSelectedImages();
    closeConfirmDialog();
  } catch (error) {
    console.error('上传失败:', error);
    ElMessage.error('图片上传失败');
    emit('upload-failure', error);
  }
};

// 清空已选择的图片
const clearSelectedImages = () => {
  // 释放URL对象
  selectedImages.value.forEach(image => {
    URL.revokeObjectURL(image.url);
  });
  selectedImages.value = [];
};

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 组件卸载时清理URL对象
onUnmounted(() => {
  clearSelectedImages();
});
</script>

<style scoped>
.image-upload-preview-container {
  position: relative;
  z-index: 1;
}

/* 禁用tooltip的样式 - 增强版 */
.image-upload-preview-container.tooltip-disabled {
  pointer-events: none;
  /* 彻底阻止tooltip触发 */
  z-index: -1;
}

/* 确保拖拽区域可以响应点击 */
.image-upload-preview-container.tooltip-disabled .drop-area {
  pointer-events: auto;
  z-index: 10;
  position: relative;
}

.drop-area {
  padding: 5px 15px;
  border-radius: 5px;
  border: 2px dashed #d9d9d9;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
  background-color: #fafafa;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-area:hover {
  border-color: #409eff;
}

.drop-area.drag-over {
  border-color: #409eff;
  background-color: rgba(64, 158, 255, 0.05);
}

/* 自定义对话框头部样式 */
.dialog-header-custom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 10px 0;
}

.dialog-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

/* 选中数量提示文本样式 - 保留原有样式 */
.selected-count-text {
  font-size: 14px;
  color: #606266;
  margin-left: 10px;
}

.confirm-dialog-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px 0;
}

/* 修复：最多4列的网格布局 - 更可靠的实现方式 */
.confirm-grid {
  display: grid;
  /* 核心修复：最多4列，自动适配 */
  grid-template-columns: repeat(min(4, auto-fill), minmax(180px, 1fr));
  gap: 20px;
  margin-top: 10px;
  justify-content: flex-start;
}

.confirm-image-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
}

.confirm-preview-image {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 4px;
  margin: 5px 0;
}

/* 重构信息区域样式 - 内容居中 */
.confirm-image-info {
  width: 100%;
  font-size: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  justify-content: center; /* 水平居中 */
  text-align: center; /* 文本居中 */
}

/* 复选框样式调整 */
.info-checkbox {
  flex-shrink: 0;
  margin: 0;
}

.file-name {
  flex: 1;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center; /* 文件名居中 */
  min-width: 80px;
}

.file-size {
  width: 100%;
  color: #909399;
  text-align: center; /* 文件大小居中 */
  margin-left: 0; /* 移除之前的左间距 */
}

/* 按钮区域样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  width: 100%;
}

/* 增强：阻止模态框内所有事件冒泡 */
:deep(.el-dialog) {
  pointer-events: auto;
  z-index: 9999 !important;
}

:deep(.el-dialog__body) {
  pointer-events: auto;
}

:deep(.el-dialog__header) {
  pointer-events: auto;
}

:deep(.el-dialog__footer) {
  pointer-events: auto;
}
</style>