<template>
  <div class="media-upload">
    <!-- 文件上传 -->
    <el-upload
      class="upload-demo"
      :action="uploadAction"
      :headers="uploadHeaders"
      :data="{ item_id: itemId }"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      :before-upload="beforeUpload"
      :file-list="fileList"
      :auto-upload="true"
    >
      <el-button size="small" type="primary">点击上传</el-button>
      <template #tip>
        <div class="el-upload__tip">
          支持图片和视频文件，单次上传多个文件
        </div>
      </template>
    </el-upload>

    <!-- 已上传文件列表 -->
    <div v-if="existingMedia.length > 0" class="existing-media-list">
      <h4>已上传文件：</h4>
      <div class="media-items">
        <div
          v-for="media in existingMedia"
          :key="media.id"
          class="media-item"
        >
          <div class="media-preview">
            <img
              v-if="media.file_type === 'image'"
              :src="media.file_url"
              :alt="media.file_name"
              class="media-img"
              @click="previewMedia(media)"
            />
            <div
              v-else-if="media.file_type === 'video'"
              class="media-video-placeholder"
              @click="previewMedia(media)"
            >
              <el-icon><VideoPlay /></el-icon>
              <span>视频：{{ media.file_name }}</span>
            </div>
            <div v-else class="media-other-placeholder">
              <el-icon><Document /></el-icon>
              <span>{{ media.file_name }}</span>
            </div>
          </div>
          <div class="media-actions">
            <el-button
              size="small"
              type="danger"
              @click="deleteMedia(media.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 媒体文件预览弹窗 -->
    <el-dialog v-model="showPreviewDialog" title="文件预览" width="80%">
      <div v-if="currentPreviewMedia">
        <img
          v-if="currentPreviewMedia.file_type === 'image'"
          :src="currentPreviewMedia.file_url"
          alt="预览图片"
          class="preview-img"
        />
        <video
          v-else-if="currentPreviewMedia.file_type === 'video'"
          :src="currentPreviewMedia.file_url"
          controls
          class="preview-video"
        ></video>
        <div v-else class="preview-other">
          <el-icon><Document /></el-icon>
          <span>{{ currentPreviewMedia.file_name }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  VideoPlay,
  Document,
  Delete
} from '@element-plus/icons-vue';
import { ProgressMedia } from '@/types/order';
import { uploadProgressMedia, deleteProgressMedia } from '@/api/progress';
import { getToken } from '@/utils/authUtils';

interface Props {
  itemId: string;
  existingMedia: ProgressMedia[];
}

const props = withDefaults(defineProps<Props>(), {
  existingMedia: () => []
});

const emit = defineEmits<{
  (e: 'upload-success', media: ProgressMedia): void;
  (e: 'delete-success', mediaId: string): void;
}>();

// 响应式数据
const fileList = ref<any[]>([]);
const showPreviewDialog = ref(false);
const currentPreviewMedia = ref<ProgressMedia | null>(null);

// 计算属性 - 上传请求头
const uploadHeaders = computed(() => {
  return {
    'Authorization': `Bearer ${getToken()}`
  };
});

// 计算属性 - 上传URL
const uploadAction = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL || ''}/api/progress/media/upload`;
});

// 上传前检查
const beforeUpload = (file: File) => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/wmv'];
  const isAllowedType = allowedTypes.includes(file.type);

  if (!isAllowedType) {
    ElMessage.error('只能上传图片或视频文件!');
    return false;
  }

  const isLt100M = file.size / 1024 / 1024 < 100; // 限制100MB
  if (!isLt100M) {
    ElMessage.error('文件大小不能超过100MB!');
    return false;
  }

  return true;
};

// 上传成功回调
const handleUploadSuccess = (response: any) => {
  if (response.code === 200) {
    ElMessage.success('文件上传成功');
    const media: ProgressMedia = {
      id: response.data.id,
      file_type: response.data.file_url.includes('image') ? 'image' : 'video',
      file_url: response.data.file_url,
      file_name: response.data.file_name,
      upload_time: new Date().toISOString()
    };
    emit('upload-success', media);
  } else {
    ElMessage.error(response.msg || '文件上传失败');
  }
};

// 上传失败回调
const handleUploadError = () => {
  ElMessage.error('文件上传失败');
};

// 删除媒体文件
const deleteMedia = async (mediaId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文件吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await deleteProgressMedia(mediaId);
    ElMessage.success('文件删除成功');
    emit('delete-success', mediaId);
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('文件删除失败');
      console.error(error);
    }
  }
};

// 预览媒体文件
const previewMedia = (media: ProgressMedia) => {
  currentPreviewMedia.value = media;
  showPreviewDialog.value = true;
};

onMounted(() => {
  // 初始化文件列表
  fileList.value = props.existingMedia.map(media => ({
    name: media.file_name,
    url: media.file_url,
    id: media.id
  }));
});
</script>

<style scoped>
.media-upload {
  width: 100%;
}

.existing-media-list {
  margin-top: 20px;
}

.media-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.media-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  width: 150px;
}

.media-preview {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.media-img {
  max-width: 100%;
  max-height: 100px;
  object-fit: cover;
  cursor: pointer;
  border-radius: 4px;
}

.media-video-placeholder,
.media-other-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100px;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
}

.media-video-placeholder .el-icon,
.media-other-placeholder .el-icon {
  font-size: 24px;
  margin-bottom: 5px;
  color: #409eff;
}

.preview-img {
  width: 100%;
  height: auto;
  max-height: 60vh;
  object-fit: contain;
}

.preview-video {
  width: 100%;
  max-height: 60vh;
  object-fit: contain;
}

.preview-other {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.preview-other .el-icon {
  font-size: 48px;
  color: #909399;
  margin-bottom: 10px;
}
</style>