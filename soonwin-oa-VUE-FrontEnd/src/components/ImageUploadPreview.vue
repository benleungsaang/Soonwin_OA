<template>
  <div
    class="media-upload-preview-container"
    :class="{ 'tooltip-disabled': confirmDialogVisible || clipboardDialogVisible }"
  >
    <!-- 媒体拖拽区域 -->
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
        accept="image/*,video/*"
        style="display: none"
        @change="handleFileSelect"
      />
    </div>

    <!-- 剪贴板媒体预览对话框 -->
    <el-dialog
      v-model="clipboardDialogVisible"
      title="剪贴板媒体预览"
      width="50%"
      :before-close="handleClipboardDialogClose"
    >
      <div style="text-align: center; padding: 20px;">
        <!-- 如果是图片 -->
        <el-image
          v-if="clipboardMediaUrl && clipboardMediaType === 'image'"
          :src="clipboardMediaUrl"
          style="max-width: 100%; max-height: 400px;"
          fit="contain"
        />
        <!-- 如果是视频 -->
        <video
          v-else-if="clipboardMediaUrl && clipboardMediaType === 'video'"
          :src="clipboardMediaUrl"
          style="max-width: 100%; max-height: 400px;"
          controls
        />
        <div v-else style="color: #999; padding: 50px;">未检测到剪贴板中的媒体文件</div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleClipboardDialogClose">取消</el-button>
          <el-button type="primary" @click="confirmUploadClipboardMedia">确认上传</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 媒体上传确认对话框 -->
    <el-dialog
      v-model="confirmDialogVisible"
      :title="`确认上传媒体文件`"
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
          <span class="dialog-title">确认上传媒体文件</span>
          <span class="selected-count-text">当前已选择 {{ selectedCount }} 个媒体文件</span>
        </div>
      </template>

      <div class="confirm-dialog-content">
        <div class="confirm-grid">
          <div
            v-for="(media, index) in selectedMedia"
            :key="index"
            class="confirm-media-item"
          >
            <!-- 图片预览 -->
            <el-image
              v-if="media.file.type.startsWith('image/')"
              :src="media.url"
              :preview-src-list="previewList"
              :initial-index="index"
              preview-teleported
              hide-on-click-modal
              close-on-press-esc
              class="confirm-preview-media"
            />
            <!-- 视频缩略图预览 -->
            <div
              v-else-if="media.file.type.startsWith('video/')"
              class="video-thumb-container"
            >
              <img
                v-if="media.thumbUrl"
                :src="media.thumbUrl"
                :alt="media.file.name"
                class="confirm-preview-media"
              />
              <div v-else class="video-placeholder" @click="generateVideoThumbnail(media)">
                <el-icon><VideoCamera /></el-icon>
                <span>生成缩略图</span>
              </div>
              <!-- 视频类型指示器 -->
              <div class="file-type-indicator">
                <el-icon><VideoCamera /></el-icon>
              </div>
            </div>
            <div class="confirm-media-info">
              <el-checkbox v-model="media.selected" class="info-checkbox">
                <!-- 给文本包一个容器，方便调整顺序 -->
                <div class="checkbox-label-content">
                  <span class="file-name">{{ media.file.name }}</span>
                  <span class="file-size">{{ formatFileSize(media.file.size) }}</span>
                  <span class="file-type">{{ media.file.type.startsWith('image/') ? '图片' : '视频' }}</span>
                </div>
              </el-checkbox>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div style="width: 100%;">
          <!-- 上传进度条 -->
          <div v-if="isUploading" class="progress-container" style="margin-bottom: 15px;">
            <div style="width: 100%; height: 8px; background: rgba(255, 186, 98, 0.6); border-radius: 4px; overflow: hidden;">
              <div :style="{width: (uploadProgress[0] || 0) + '%', height: '100%'}" style="background: #409eff; border-radius: 4px; transition: width 0.3s;"></div>
            </div>
            <div class="progress-text" style="margin-top: 2px; text-align: center;">
              {{ uploadProgress[0] || 0 }}%
            </div>
          </div>
          <span class="dialog-footer">
            <el-button @click="closeConfirmDialog">取消</el-button>
            <!-- 合并全选/取消全选按钮 -->
            <el-button @click="toggleSelectAll">{{ isAllSelected ? '取消全选' : '全选' }}</el-button>
            <el-button type="primary" :disabled="isUploading" @click="confirmUpload">
              <span v-if="isUploading">上传中...</span>
              <span v-else>确认上传</span>
            </el-button>
          </span>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Camera, VideoCamera } from '@element-plus/icons-vue';
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
  'upload-success': [files: File[], mediaFiles: any[]]; // 修改：传递原始文件和媒体文件信息
  'upload-failure': [error: any];
  'upload-clipboard-image': [file: File, taskId: number]; // 新增：上传剪贴板媒体事件
}>();

// 响应式数据
const selectedMedia = ref<{ file: File; url: string; thumbUrl?: string; selected: boolean; type: string }[]>([]);
const isDragOver = ref(false);
const confirmDialogVisible = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

// 上传进度相关
const uploadProgress = ref<{[key: number]: number}>({}); // 用于存储每个文件的上传进度
const isUploading = ref(false); // 是否正在上传

// 剪贴板相关
const clipboardDialogVisible = ref(false);
const clipboardMediaUrl = ref(''); // 剪贴板媒体预览URL
const clipboardMediaType = ref<'image' | 'video'>('image'); // 剪贴板媒体类型
const clipboardMediaFile = ref<File | null>(null); // 剪贴板媒体文件对象

// 计算属性：生成预览列表
const previewList = computed(() => {
  return selectedMedia.value
    .filter(media => media.selected && media.file.type.startsWith('image/'))
    .map(media => media.url);
});

// 计算属性：当前选中的媒体数量
const selectedCount = computed(() => {
  return selectedMedia.value.filter(media => media.selected).length;
});

// 计算属性：判断是否全选
const isAllSelected = computed(() => {
  // 空列表时返回false
  if (selectedMedia.value.length === 0) return false;
  // 检查所有媒体文件是否都被选中
  return selectedMedia.value.every(media => media.selected);
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
    if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
      validFiles.push(file);
    } else {
      ElMessage.warning(`文件 ${file.name} 不是图片或视频格式，已跳过`);
    }
  }

  if (validFiles.length === 0) return;

  // 将文件转换为预览对象
  const newMedia = validFiles.map(file => ({
    file,
    url: URL.createObjectURL(file),
    thumbUrl: file.type.startsWith('video/') ? undefined : URL.createObjectURL(file), // 图片使用原图作为缩略图
    selected: true, // 默认全选
    type: file.type.startsWith('image/') ? 'image' : 'video'
  }));

  // 添加到已选择的媒体列表
  selectedMedia.value = [...selectedMedia.value, ...newMedia];

  ElMessage.success(`已选择 ${newMedia.length} 个媒体文件`);

  // 核心修改：处理完文件后直接打开确认对话框
  confirmDialogVisible.value = true;
};

// 关闭确认对话框（修改：关闭时清空媒体）
const closeConfirmDialog = () => {
  confirmDialogVisible.value = false;
  // 清空已选择的媒体，避免重复添加
  clearSelectedMedia();
};

// 切换全选/取消全选状态
const toggleSelectAll = () => {
  const targetState = !isAllSelected.value;
  selectedMedia.value.forEach(media => {
    media.selected = targetState;
  });
};

// 确认上传
const confirmUpload = async () => {
  if (!props.taskId) {
    ElMessage.error('未指定任务ID');
    return;
  }

  // 获取选中的文件
  const selectedFiles = selectedMedia.value
    .filter(media => media.selected)
    .map(media => media.file);

  if (selectedFiles.length === 0) {
    ElMessage.warning('请至少选择一个媒体文件');
    return;
  }

  try {
    isUploading.value = true;
    
    // 创建FormData对象并添加所有选定的文件
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file); // 后端使用getlist获取多个文件
    });
    formData.append('task_id', props.taskId.toString());

    // 创建带进度的请求
    const response: any = await request.post('/api/order-status/upload-multiple-images', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent: any) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          // 更新整体上传进度
          uploadProgress.value[0] = progress; // 使用0作为整体进度的key
        }
      }
    });

    ElMessage.success(`${selectedFiles.length} 个媒体文件上传成功`);
    // 发送新上传的媒体文件信息，而不是只发送原始文件
    emit('upload-success', selectedFiles, response.data?.media_files || []);

    // 清空已选择的媒体
    clearSelectedMedia();
    closeConfirmDialog();
  } catch (error) {
    console.error('上传失败:', error);
    ElMessage.error('媒体文件上传失败');
    emit('upload-failure', error);
  } finally {
    isUploading.value = false;
    // 清空进度
    uploadProgress.value = {};
  }
};

// 清空已选择的媒体
const clearSelectedMedia = () => {
  // 释放URL对象
  selectedMedia.value.forEach(media => {
    URL.revokeObjectURL(media.url);
    if (media.thumbUrl) {
      URL.revokeObjectURL(media.thumbUrl);
    }
  });
  selectedMedia.value = [];
};

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 生成视频缩略图
const generateVideoThumbnail = (media: { file: File; url: string; thumbUrl?: string; selected: boolean; type: string }) => {
  const video = document.createElement('video');
  video.src = media.url;

  video.addEventListener('loadedmetadata', () => {
    // 创建canvas元素用于截图
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    // 设置canvas尺寸
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // 设置视频播放位置（第一帧）
    video.currentTime = 0;

    video.addEventListener('seeked', () => {
      // 绘制视频帧到canvas
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // 生成缩略图URL
        const thumbUrl = canvas.toDataURL('image/jpeg', 0.7);
        media.thumbUrl = thumbUrl;
      }
    });
  });
};

// 组件卸载时清理URL对象
onUnmounted(() => {
  clearSelectedMedia();
});

// ===================== 剪贴板功能 =====================

/**
 * 从剪贴板读取媒体文件（多方案兼容处理）
 */
const pasteMediaFromClipboard = async (taskId: number) => {
  try {
    let file = null;

    // 方案1：优先使用 Clipboard API (现代浏览器)
    try {
      if (navigator.clipboard && window.ClipboardItem) {
        const clipboardItems = await navigator.clipboard.read();
        // 遍历剪贴板项查找媒体文件
        for (const item of clipboardItems) {
          const types = item.types;
          for (const type of types) {
            if (type.startsWith('image/') || type.startsWith('video/')) {
              const blob = await item.getType(type);
              // 创建File对象，包含时间戳避免重名
              const ext = type.split('/')[1] || 'png';
              file = new File([blob], `paste-${Date.now()}.${ext}`, {
                type: blob.type
              });
              clipboardMediaType.value = type.startsWith('image/') ? 'image' : 'video';
              break;
            }
          }
          if (file) break;
        }
      }
    } catch (clipboardApiError) {
      console.warn('Clipboard API 访问失败，尝试备用方案:', clipboardApiError);
    }

    // 方案2：使用 clipboardData.items (在组件上下文外无法直接访问，但可作为通用方法)
    if (!file) {
      // 提示用户在输入框粘贴
      throw new Error('请在输入框中使用 Ctrl+V 粘贴媒体文件');
    }

    if (!file) {
      throw new Error('剪贴板中未检测到媒体文件，请先复制媒体文件后再尝试');
    }

    // 验证文件类型
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
    const allowedVideoExts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v'];

    if (!allowedImageExts.includes(ext) && !allowedVideoExts.includes(ext)) {
      throw new Error(`不支持的媒体格式：${ext}，支持的格式：${[...allowedImageExts, ...allowedVideoExts].join(', ')}`);
    }

    // 存储文件对象并创建预览URL
    clipboardMediaFile.value = file;
    clipboardMediaUrl.value = URL.createObjectURL(file);

    // 打开预览弹窗
    clipboardDialogVisible.value = true;

  } catch (error) {
    console.error('读取剪贴板媒体失败：', error);
    throw error;
  }
};

/**
 * 从父组件添加剪贴板媒体，显示确认对话框
 */
const addClipboardMedia = (file: File) => {
  if (!file || (!file.type.startsWith('image/') && !file.type.startsWith('video/'))) {
    throw new Error('无效的媒体文件');
  }

  // 将文件转换为预览对象
  const newMedia = {
    file,
    url: URL.createObjectURL(file),
    thumbUrl: file.type.startsWith('video/') ? undefined : URL.createObjectURL(file), // 图片使用原图作为缩略图
    selected: true, // 默认选中
    type: file.type.startsWith('image/') ? 'image' : 'video'
  };

  // 添加到已选择的媒体列表
  selectedMedia.value = [...selectedMedia.value, newMedia];

  ElMessage.success(`已添加剪贴板媒体: ${file.name}`);

  // 打开确认对话框
  confirmDialogVisible.value = true;
};

/**
 * 处理输入框的粘贴事件
 */
const handleInputPaste = (e: ClipboardEvent) => {
  try {
    let file = null;

    // 方案1：使用 clipboardData.items
    if (e.clipboardData && e.clipboardData.items) {
      for (let i = 0; i < e.clipboardData.items.length; i++) {
        const item = e.clipboardData.items[i];
        if (item.kind === 'file' && (item.type.startsWith('image/') || item.type.startsWith('video/'))) {
          file = item.getAsFile();
          clipboardMediaType.value = item.type.startsWith('image/') ? 'image' : 'video';
          break;
        }
      }
    }

    // 方案2：使用 clipboardData.files
    if (!file && e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      const candidate = e.clipboardData.files[0];
      if (candidate.type.startsWith('image/') || candidate.type.startsWith('video/')) {
        file = candidate;
        clipboardMediaType.value = candidate.type.startsWith('image/') ? 'image' : 'video';
      }
    }

    if (file) {
      // 验证文件类型
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
      const allowedVideoExts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v'];

      if (allowedImageExts.includes(ext) || allowedVideoExts.includes(ext)) {
        // 直接设置媒体文件并弹出预览框
        clipboardMediaFile.value = file;
        clipboardMediaUrl.value = URL.createObjectURL(file);
        clipboardDialogVisible.value = true;
      } else {
        throw new Error(`检测到文件但格式不支持: ${ext}，仅支持: ${[...allowedImageExts, ...allowedVideoExts].join(', ')}`);
      }
    } else {
      // 检查是否是文本内容
      const pastedText = e.clipboardData?.getData('text') || '';
      if (pastedText) {
        throw new Error('检测到文本内容，此功能主要用于媒体文件粘贴');
      } else {
        throw new Error('剪贴板中未检测到媒体文件');
      }
    }
  } catch (error) {
    console.warn('处理粘贴事件时出错:', error);
    throw error;
  }
};

/**
 * 关闭剪贴板对话框时清理URL
 */
const handleClipboardDialogClose = () => {
  // 释放创建的URL对象，避免内存泄漏
  if (clipboardMediaUrl.value) {
    URL.revokeObjectURL(clipboardMediaUrl.value);
    clipboardMediaUrl.value = '';
  }
  clipboardMediaFile.value = null;
  clipboardDialogVisible.value = false;
};

/**
 * 确认上传剪贴板媒体
 */
const confirmUploadClipboardMedia = async () => {
  if (!clipboardMediaFile.value) {
    throw new Error('没有可上传的媒体文件');
  }

  if (!props.taskId) {
    throw new Error('未指定任务ID');
  }

  try {
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', clipboardMediaFile.value);
    formData.append('task_id', props.taskId.toString());

    // 调用后端上传API - 保持原始接口不变
    const response: any = await request.post(`/api/order-status/${props.taskId}/tasks/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    // 触发上传媒体文件事件，让父组件处理具体上传逻辑
    emit('upload-clipboard-image', clipboardMediaFile.value, props.taskId);

    // 清理并关闭对话框
    handleClipboardDialogClose();
  } catch (error) {
    console.error('剪贴板媒体上传失败:', error);
    emit('upload-failure', error);
    throw error;
  }
};

// 暴露方法给父组件
defineExpose({
  addClipboardMedia,
  pasteMediaFromClipboard
});
</script>

<style scoped>
.media-upload-preview-container {
  position: relative;
  z-index: 1;
}

/* 禁用tooltip的样式 - 增强版 */
.media-upload-preview-container.tooltip-disabled {
  pointer-events: none;
  /* 彻底阻止tooltip触发 */
  z-index: -1;
}

/* 确保拖拽区域可以响应点击 */
.media-upload-preview-container.tooltip-disabled .drop-area {
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

.confirm-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 10px;
  padding: 0;
  align-items: center;
  justify-content: center;
}

.confirm-media-item {
  width: 180px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  border: rgba(157, 174, 190, 0.2) solid 2px;
  padding: 5px;
  border-radius: 5px;
  position: relative;
}

/* 媒体容器：固定尺寸，确保比例 */
.confirm-preview-media {
  box-sizing: border-box;
  width: 100%; /* 继承父元素180px宽度 */
  border-radius: 4px;
  overflow: hidden; /* 隐藏超出部分 */
  display: block;
}

/* 深度选择器：穿透到el-image内部的img（Vue3 scoped） */
:deep(.confirm-preview-media .el-image__inner) {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 强制按比例展示 */
  object-position: center; /* 居中裁剪 */
  max-width: none !important; /* 覆盖组件默认样式 */
  max-height: none !important;
}

/* 视频缩略图容器 */
.video-thumb-container {
  position: relative;
  width: 100%;
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background-color: #f5f7fa;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
}

.video-placeholder:hover {
  background-color: #e6f7ff;
  border-color: #1890ff;
}

/* 文件类型指示器 */
.file-type-indicator {
  position: absolute;
  top: 5px;
  left: 5px;
  width: 20px;
  height: 20px;
  background-color: #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.file-type-indicator .el-icon {
  font-size: 12px;
  color: white;
  margin: 0;
  padding: 0;
}

/* 重构信息区域样式 - 整体容器 */
.confirm-media-info {
  width: 100%;
  margin-top: 8px;
}

/* 复选框样式调整（核心：网格布局） */
.info-checkbox {
  display: grid; /* 改用grid布局，实现两列布局 */
  grid-template-columns: 1fr 20px; /* 左列占满剩余空间，右列固定20px（复选框宽度） */
  grid-template-rows: auto auto auto; /* 三行自适应高度：文件名、文件大小、文件类型 */
  align-items: center; /* 复选框垂直居中 */
  gap: 4px; /* 行间距 */
  width: 100%;
  height: 60px;
  cursor: pointer;
  padding: 8px 12px; /* 上下内边距更大，适配三行文本 */
  background-color: rgba(160, 179, 196, 0.2);
  border-radius: 5px;
  box-sizing: border-box;
  overflow: hidden;
}

/* 核心：文本区域占左侧三行，复选框占右侧三行 */
:deep(.info-checkbox .el-checkbox__label) {
  grid-row: 1 / 4;
  grid-column: 1 / 2;
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  min-width: 0; /* 关键！解除Grid子元素最小宽度限制 */
  margin: 0 !important;
  padding: 0;
  line-height: 1.2;
}

/* 复选框图标：右侧跨三行垂直居中 */
:deep(.info-checkbox .el-checkbox__input) {
  grid-row: 1 / 4; /* 跨三行 */
  grid-column: 2 / 3; /* 右列 */
  flex-shrink: 0;
  margin: 0 !important;
  /* 确保复选框垂直居中 */
  align-self: center;
}

/* 文本容器：垂直排列 */
.checkbox-label-content {
  display: flex;
  flex-direction: column; /* 三行显示 */
  width: 100%;
  min-width: 0; /* 保证文件名省略号生效 */
  max-width: 100%; /* 强制不超出父容器 */
}

.file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px; /* 文件名稍大 */
  width: 100%; /* 关键：占满父容器宽度 */
  display: block; /* 转为块级元素，确保宽度生效 */
  height: 20px;
}

.file-size {
  flex-shrink: 0;
  color: #999;
  font-size: 12px;
  /* 文件大小单独一行，不会被挤压 */
}

.file-type {
  flex-shrink: 0;
  color: #67c23a;
  font-size: 12px;
  font-weight: bold;
  /* 文件类型单独一行 */
}

/* 重置Element UI默认样式 */
:deep(.info-checkbox .el-checkbox) {
  margin: 0 !important;
  width: 100%;
  padding: 0;
  /* 让el-checkbox适配grid布局 */
  display: grid;
  grid-template-columns: inherit;
  grid-template-rows: inherit;
}

/* 按钮区域样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  width: 100%;
}

/* 进度条容器 */
.progress-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  padding: 5px 10px;
  background-color: rgba(156, 156, 156, 0.1);
  border-radius: 5px;
}

/* 进度文本 */
.progress-text {
  font-size: 12px;
  color: #606266;
  text-align: center;
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