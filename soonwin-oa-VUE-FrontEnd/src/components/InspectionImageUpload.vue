<template>
  <div class="inspection-image-upload">
    <!-- 正常状态图片上传区域 -->
    <div v-if="inspectionResult === 'normal'" class="upload-section">
      <div class="photo-grid">
        <div
          v-for="(photo, index) in getPhotoPaths(photoPath)"
          :key="index"
          class="photo-preview"
          @click="emit('preview-image', getPhotoUrl(photo))"
        >
          <img :src="getPhotoUrl(photo)" :alt="`正常照片${index + 1}`" style="max-width: 100px; max-height: 100px; cursor: pointer;">
          <el-icon
            class="delete-photo-icon"
            @click.stop="removePhoto(photo)"
            style="position: absolute; top: -8px; right: -8px; background: red; border-radius: 50%; color: white; cursor: pointer;"
          >
            <Close />
          </el-icon>
        </div>
      </div>
      <el-upload
        class="upload-demo"
        :auto-upload="true"
        :show-file-list="false"
        list-type="picture"
        :http-request="(options) => handlePhotoUpload(options, 'normal')"
      >
        <el-icon style="cursor: pointer; border: 1px ; margin-left: 2cqw; font-size: 25px; background-color: #ddd; padding: 8px; border-radius: 5px;">
          <Camera />
        </el-icon>
      </el-upload>
    </div>

    <!-- 缺陷状态图片上传区域 -->
    <div v-if="inspectionResult === 'defect'" class="defect-section">
      <div class="photo-grid">
        <div
          v-for="(photo, index) in getPhotoPaths(photoPath)"
          :key="index"
          class="photo-preview"
          @click="emit('preview-image', getPhotoUrl(photo))"
        >
          <img :src="getPhotoUrl(photo)" :alt="`缺陷照片${index + 1}`" style="max-width: 100px; max-height: 100px; cursor: pointer;">
          <el-icon
            class="delete-photo-icon"
            @click.stop="removePhoto(photo)"
            style="position: absolute; top: -8px; right: -8px; background: red; border-radius: 50%; color: white; cursor: pointer;"
          >
            <Close />
          </el-icon>
        </div>
      </div>

      <el-input
        v-model="localDescription"
        type="textarea"
        :rows="3"
        placeholder="请输入缺陷描述"
        @blur="onDescriptionBlur"
      />

      <el-upload
        class="upload-demo"
        :auto-upload="true"
        :show-file-list="false"
        list-type="picture"
        style="display: inline-flex; margin-left: 15px;"
        :http-request="(options) => handlePhotoUpload(options, 'defect')"
      >
        <el-icon style=" cursor: pointer; border: 1px ; font-size: 25px; background-color: #ddd; padding: 8px; border-radius: 5px;">
          <Camera />
        </el-icon>
      </el-upload>
    </div>


  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { uploadFile } from '@/utils/upload';
import { Close, Camera } from '@element-plus/icons-vue';

// 定义组件props
interface Props {
  inspectionResult: string;
  photoPath?: string | null;
  description?: string | null;
}

const props = withDefaults(defineProps<Props>(), {
  photoPath: null,
  description: null
});

// 使用计算属性处理description的双向绑定
const localDescription = computed({
  get: () => props.description || '',
  set: (value) => {
    emit('update:description', value);
  }
});

// 定义emit事件
const emit = defineEmits<{ 
  'update:photo-path': [value: string | null];
  'update:description': [value: string | null];
  'photo-updated': [value: { photoPath: string | null; description: string | null }];
  'preview-image': [url: string];
}>();

// 响应式数据
const windowWidth = ref(window.innerWidth);

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};



// 监听窗口大小变化
const onMounted = () => {
  window.addEventListener('resize', handleResize);
};

const onUnmounted = () => {
  window.removeEventListener('resize', handleResize);
};

// 获取图片路径数组
const getPhotoPaths = (photoPath: string | null) => {
  if (!photoPath) return [];
  return photoPath.split(',').map(path => path.trim()).filter(path => path);
};

// 获取照片URL，支持临时照片
const getPhotoUrl = (path: string) => {
  if (!path) return '';

  // 标准化路径分隔符
  const normalizedPath = path.replace(/\\/g, '/');

  // 如果路径已经是完整URL，则直接返回
  if (normalizedPath.startsWith('http://') || normalizedPath.startsWith('https://')) {
    return normalizedPath;
  }

  // 否则添加基础URL
  if (import.meta.env.MODE === 'development') {
    // 开发环境下，假设文件服务在后端服务器上
    return `http://192.168.30.70:5000/${normalizedPath}`;
  } else {
    return `${window.location.protocol}//${window.location.hostname}:5000/${normalizedPath}`;
  }
};

// 删除单张图片
const removePhoto = async (photoToRemove: string) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这张照片吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 从路径字符串中移除指定图片路径
    const currentPaths = getPhotoPaths(props.photoPath);
    const updatedPaths = currentPaths.filter(path => path !== photoToRemove);
    const newPhotoPath = updatedPaths.join(',') || null;

    // 更新照片路径并触发事件
    emit('update:photo-path', newPhotoPath);
    emit('photo-updated', { photoPath: newPhotoPath, description: props.description });
    ElMessage.success('照片已标记为删除，将在保存时提交到服务器');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除照片失败:', error);
      ElMessage.error('删除照片失败');
    }
  }
};

// 手动上传照片处理
interface UploadOptions {
  file: File;
  onProgress?: (event: ProgressEvent) => void;
  onError?: (error: Error) => void;
  onSuccess: (response: any) => void;
}

const handlePhotoUpload = async (options: UploadOptions, type: string) => {
  const { file, onProgress, onError, onSuccess } = options;

  try {
    // 使用新的上传模块上传文件到临时位置
    // 目前uploadFile函数不直接支持进度，但我们可以显示上传开始消息
    if (onProgress) {
      // 显示上传进度（虽然当前uploadFile不提供进度，但保留接口兼容）
      onProgress({ loaded: 0, total: file.size } as ProgressEvent);
    }

    const result: any = await uploadFile(file);

    // 调用成功回调
    onSuccess(result);

    // 更新项目照片路径 - 支持多张图片
    let newPhotoPath = '';
    if (result && result.path) {
      if (props.photoPath) {
        // 如果已有照片路径，添加新路径（逗号分隔）
        newPhotoPath = `${props.photoPath},${result.path}`;
      } else {
        // 如果没有照片路径，直接设置
        newPhotoPath = result.path;
      }

      // 更新照片路径并触发事件
      emit('update:photo-path', newPhotoPath);
      emit('photo-updated', { photoPath: newPhotoPath, description: props.description });
      ElMessage.success(`${type === 'normal' ? '正常' : '缺陷'}照片上传成功`);
    }
  } catch (error: any) {
    console.error('照片上传失败:', error);
    if (onError) {
      onError(error);
    }
    ElMessage.error(`${type === 'normal' ? '正常' : '缺陷'}照片上传失败`);
  }
};

// 描述信息失焦事件
const onDescriptionBlur = () => {
  emit('photo-updated', { photoPath: props.photoPath, description: localDescription.value });
};

// 组件挂载时添加事件监听
onMounted();

// 组件卸载前移除事件监听
onUnmounted();
</script>

<style scoped>
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
</style>