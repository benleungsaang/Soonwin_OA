<template>
  <div class="upload-container">
    <el-page-header content="上传展示文件" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>

    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>上传展示文件</span>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="文件类型" prop="fileType">
          <el-radio-group v-model="form.fileType" @change="handleFileTypeChange" text-color="#fff" fill="#409eff">
            <el-radio-button label="PDF文件" value="pdf" />
            <el-radio-button label="图片组" value="image_group" />
          </el-radio-group>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入文件标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="文件上传" prop="files" required>
          <el-upload
            class="upload-area"
            drag
            :action="uploadUrl"
            :headers="uploadHeaders"
            :multiple="form.fileType === 'image_group'"
            :accept="form.fileType === 'image_group' ? 'image/*' : '.pdf'"
            :before-upload="beforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :on-remove="handleRemoveFile"
            :on-change="handleFileChange"
            :auto-upload="false"
            :limit="form.fileType === 'image_group' ? 50 : 1"
          >
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                {{ form.fileType === 'image_group'
                  ? '只能上传图片文件，最多50张，支持jpg/png/gif格式'
                  : '只能上传PDF文件，大小不超过50MB' }}
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="submitForm"
            :loading="uploading"
            :disabled="!canSubmit"
          >
            {{ uploading ? '上传中...' : '提交上传' }}
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 上传成功信息 -->
      <div v-if="uploadSuccess" class="upload-success">
        <el-alert
          title="上传成功！"
          type="success"
          :closable="false"
          show-icon
        >
          <p>{{ uploadSuccessMessage }}</p>
        </el-alert>
        <div class="success-actions">
          <el-button @click="resetUploadSuccess">继续上传</el-button>
          <el-button @click="goToDisplayFiles" type="primary">查看文件</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { ElMessage, ElButton, ElPageHeader, ElDivider } from 'element-plus';
import { Upload } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { useRouter } from 'vue-router';

// 表单数据
const form = reactive({
  title: '',
  fileType: 'pdf' as 'image_group' | 'pdf',
  displayMode: 'waterfall' as 'waterfall' | 'pagination',
  files: [] as File[]
});

// 文件列表
const fileList = ref<any[]>([]);

// 上传状态
const uploading = ref(false);

// 上传成功状态
const uploadSuccess = ref(false);
const uploadSuccessMessage = ref('');

// 表单引用
const formRef = ref();

// 路由
const router = useRouter();

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 登出
const logout = async () => {
  try {
    await ElMessage.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    // 清除本地存储的token
    localStorage.removeItem('oa_token');
    // 提示用户
    ElMessage.success('已退出登录');

    // 跳转到登录页
    router.push('/login');
  } catch (error) {
    // 用户取消登出，什么都不做
  }
};

// 上传URL和请求头
const uploadUrl = '/api/display-file/upload';
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('oa_token')}`
};

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入文件标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在1-200个字符之间', trigger: 'blur' }
  ],
  fileType: [
    { required: true, message: '请选择文件类型', trigger: 'change' }
  ],
  files: [
    { required: true, message: '请上传文件', trigger: 'change' }
  ]
};

// 计算是否可以提交
const canSubmit = computed(() => {
  return fileList.value.length > 0;  // 只要选择了文件，上传按钮就可以激活
});
// 文件类型改变处理
const handleFileTypeChange = () => {
  // 重置文件列表
  fileList.value = [];
  form.files = [];
};

// 上传前验证
const beforeUpload = (file: File) => {
  // 验证文件类型
  if (form.fileType === 'image_group') {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      ElMessage.error('只能上传图片文件!');
      return false;
    }
  } else {
    const isPDF = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPDF) {
      ElMessage.error('只能上传PDF文件!');
      return false;
    }
  }

  // 验证文件大小
  const isLt50M = file.size / 1024 / 1024 < 50;
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过50MB!');
    return false;
  }

  return true;
};

// 上传成功处理
const handleUploadSuccess = (_response: any, _file: any, updatedFileList: any[]) => {
  ElMessage.success('文件上传成功!');
  fileList.value = updatedFileList;
};

// 文件改变处理（选择文件时触发）
const handleFileChange = (_file: any, fileListUpdated: any[]) => {
  // 更新文件列表，保持响应性
  // 保留所有文件，包括待上传和已上传的
  fileList.value = [...fileListUpdated];
};

// 上传错误处理
const handleUploadError = (error: any) => {
  console.error('上传错误:', error);
  ElMessage.error('文件上传失败!');
};

// 移除文件处理
const handleRemoveFile = (_file: any, updatedFileList: any[]) => {
  fileList.value = [...updatedFileList];
};

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return;

  try {
    // 在提交前进行完整验证
    if (!form.title) {
      ElMessage.error('请输入文件标题!');
      return;
    }

    if (!form.fileType) {
      ElMessage.error('请选择文件类型!');
      return;
    }

    if (fileList.value.length === 0) {
      ElMessage.error('请至少上传一个文件!');
      return;
    }

    uploading.value = true;

        // 创建FormData对象
        const formData = new FormData();
        formData.append('title', form.title);
        formData.append('file_type', form.fileType);
        formData.append('display_mode', 'waterfall'); // 默认瀑布流

        // 添加文件
        for (let i = 0; i < fileList.value.length; i++) {
          // 仅处理原始文件（未上传的文件）
          if (fileList.value[i].raw) {
            formData.append('file', fileList.value[i].raw);
          } else if (fileList.value[i].originFileObj) {
            formData.append('file', fileList.value[i].originFileObj);
          }
        }
    // 发送请求
    const response = await request.post('/api/display-file/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    ElMessage.success('展示文件上传成功!');
    uploadSuccess.value = true;
    uploadSuccessMessage.value = `文件 "${response.title}" 上传成功！`;
    // 不跳转页面，只显示成功信息
    // router.push('/display-files');
  } catch (error: any) {
    console.error('上传错误:', error);
    if (error.message) {
      ElMessage.error(`上传失败: ${error.message}`);
    } else {
      ElMessage.error('上传失败!');
    }
  } finally {
    uploading.value = false;
  }
};

// 重置上传成功状态
const resetUploadSuccess = () => {
  uploadSuccess.value = false;
  uploadSuccessMessage.value = '';
  resetForm();
};

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  form.title = '';
  form.fileType = 'pdf';
  form.displayMode = 'waterfall';
  form.files = [];
  fileList.value = [];
};

// 跳转到展示文件页面
const goToDisplayFiles = () => {
  router.push('/display-files');
};




</script>

<style scoped>
.upload-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.upload-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  width: 100%;
}

.upload-icon {
  font-size: 40px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  text-align: center;
  line-height: 178px;
}

.el-upload__tip {
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-success {
  margin-top: 20px;
}

.success-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>