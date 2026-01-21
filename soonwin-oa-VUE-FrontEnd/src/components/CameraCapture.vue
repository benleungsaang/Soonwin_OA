<template>
  <div class="camera-capture-container">
    <!-- 拍照模态框 -->
    <el-dialog
      v-model="showCameraModal"
      title="拍照"
      :width="isMobile ? '95%' : '60%'"
      :before-close="closeCameraModal"
      :destroy-on-close="true"
    >
      <div class="camera-container">
        <div v-if="!capturing" class="video-container">
          <video
            ref="videoRef"
            autoplay
            playsinline
            muted
            style="width: 100%; height: auto; max-height: 70vh; background: #000;"
          ></video>
        </div>
        
        <!-- 拍照后预览 -->
        <div v-else class="preview-container">
          <img :src="capturedImage || ''" alt="Captured Preview" style="width: 100%; height: auto; max-height: 70vh;" />
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer" style="display: flex; justify-content: space-between; padding: 0 20px;">
          <div>
            <el-button v-if="!capturing" @click="switchCamera">
              <el-icon><Refresh /></el-icon>
              切换摄像头
            </el-button>
          </div>
          
          <div>
            <el-button @click="closeCameraModal">取消</el-button>
            <el-button 
              v-if="!capturing" 
              type="primary" 
              @click="capturePhoto"
              :loading="capturing"
            >
              <el-icon><Camera /></el-icon>
              拍照
            </el-button>
            <div v-else style="display: flex; gap: 10px;">
              <el-button @click="retakePhoto">重拍</el-button>
              <el-button type="success" @click="confirmPhoto">确认</el-button>
            </div>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { ElDialog, ElButton, ElIcon, ElMessage } from 'element-plus';
import { Camera, Refresh } from '@element-plus/icons-vue';

interface Props {
  modelValue: boolean; // 控制模态框显示
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void;
  (e: 'photo-captured', blob: Blob): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 响应式变量
const showCameraModal = ref(false);
const videoRef = ref<HTMLVideoElement | null>(null);
const cameraStream = ref<MediaStream | null>(null);
const capturedImage = ref<string | null>(null);
const capturing = ref(false);
const facingMode = ref<'user' | 'environment'>('environment'); // 默认后置摄像头
const windowWidth = ref(window.innerWidth);

// 计算属性判断是否为移动端
const isMobile = computed(() => windowWidth.value < 768);

// 打开摄像头
const openCamera = async () => {
  try {
    // 关闭之前的流
    if (cameraStream.value) {
      cameraStream.value.getTracks().forEach(track => track.stop());
    }

    const constraints = {
      video: {
        facingMode: facingMode.value,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    };

    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    cameraStream.value = stream;

    if (videoRef.value) {
      videoRef.value.srcObject = stream;
    }
  } catch (error: any) {
    console.error('无法访问摄像头:', error);
    let errorMessage = '无法访问摄像头';
    
    // 根据错误类型提供更具体的错误信息
    if (error.name === 'NotAllowedError') {
      errorMessage = '用户拒绝了摄像头访问权限，请在浏览器设置中允许访问';
    } else if (error.name === 'NotFoundError') {
      errorMessage = '未找到可用的摄像头设备';
    } else if (error.name === 'NotReadableError') {
      errorMessage = '摄像头被其他应用占用';
    } else if (error.name === 'SecureContextRequiredError') {
      errorMessage = '需要在安全上下文（HTTPS）中运行';
    }
    
    ElMessage.error(errorMessage);
    
    // 降级处理：尝试使用前置摄像头
    try {
      const constraints = {
        video: { facingMode: 'user' },
        audio: false
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      cameraStream.value = stream;

      if (videoRef.value) {
        videoRef.value.srcObject = stream;
      }
    } catch (fallbackError: any) {
      console.error('无法访问任何摄像头:', fallbackError);
      let fallbackErrorMessage = '无法访问任何摄像头';
      
      if (fallbackError.name === 'NotAllowedError') {
        fallbackErrorMessage = '用户拒绝了摄像头访问权限';
      } else if (fallbackError.name === 'NotFoundError') {
        fallbackErrorMessage = '未找到可用的摄像头设备';
      } else if (fallbackError.name === 'NotReadableError') {
        fallbackErrorMessage = '摄像头被其他应用占用';
      }
      
      ElMessage.error(fallbackErrorMessage);
    }
  }
};

// 拍照
const capturePhoto = async () => {
  if (!videoRef.value) return;

  capturing.value = true;

  // 创建canvas进行截图
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  if (!context) return;

  canvas.width = videoRef.value.videoWidth;
  canvas.height = videoRef.value.videoHeight;

  // 绘制当前视频画面到canvas
  context.drawImage(videoRef.value, 0, 0, canvas.width, canvas.height);

  // 将canvas内容转换为图片blob
  canvas.toBlob((blob) => {
    if (blob) {
      capturedImage.value = URL.createObjectURL(blob);
    }
    capturing.value = false;
  }, 'image/jpeg', 0.8); // JPEG格式，质量0.8
};

// 确认照片
const confirmPhoto = async () => {
  if (capturedImage.value) {
    // 转换为blob并返回
    try {
      const blob = await blobUrlToBlob(capturedImage.value);
      emit('photo-captured', blob);
      closeCameraModal();
    } catch (error) {
      console.error('转换图片失败:', error);
    }
  }
};

// 重拍
const retakePhoto = () => {
  capturing.value = false;
  capturedImage.value = null;
};

// 切换摄像头
const switchCamera = () => {
  facingMode.value = facingMode.value === 'environment' ? 'user' : 'environment';
  openCamera();
};

// 关闭摄像头和模态框
const closeCameraModal = () => {
  // 停止摄像头流
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(track => track.stop());
    cameraStream.value = null;
  }
  
  // 清理预览图片URL
  if (capturedImage.value) {
    URL.revokeObjectURL(capturedImage.value);
    capturedImage.value = null;
  }
  
  capturing.value = false;
  emit('update:modelValue', false);
};

// 将图片URL转换为Blob
const blobUrlToBlob = async (url: string): Promise<Blob> => {
  const response = await fetch(url);
  return await response.blob();
};

// 监听模态框显示状态
watch(() => props.modelValue, (newValue) => {
  showCameraModal.value = newValue;
  if (newValue) {
    openCamera();
  } else {
    closeCameraModal();
  }
});

// 窗口大小变化处理
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  // 确保摄像头流被关闭
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(track => track.stop());
  }
});
</script>

<style scoped>
.camera-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 300px;
}

.video-container, .preview-container {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>