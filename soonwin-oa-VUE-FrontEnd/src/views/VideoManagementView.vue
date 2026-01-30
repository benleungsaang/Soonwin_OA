<template>
  <div class="video-management">
    <CommonHeader title="视频管理" />
    <div class="header">
      <div class="title-with-count">
        <h2>视频管理</h2>
        <span v-if="showResultCount" class="result-count">找到 {{ totalVideos }} 条视频</span>
      </div>
      <el-button type="primary" @click="showUploadDialog = true">上传视频</el-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-input
        v-model="searchQuery"
        placeholder="搜索标题、标签、备注..."
        prefix-icon="Search"
        style="width: 300px; margin-right: 10px;"
        @keyup.enter="searchContent"
      />
      <el-button type="primary" @click="searchContent" style="margin-right: 10px;">内容搜索</el-button>
      <el-select
        v-model="selectedMachine"
        placeholder="选择机器"
        clearable
        style="width: 200px; margin-right: 10px;"
      >
        <el-option value="0" label="无关联机器" />
        <el-option
          v-for="machine in machineList"
          :key="machine.model"
          :label="`${machine.model} ( ${machine.original_model} )`"
          :value="machine.model"
        />
      </el-select>
      <el-button type="primary" @click="searchByMachine">机器搜索</el-button>
    </div>

    <!-- 视频列表 -->
    <div v-if="videos.length > 0" class="video-grid">
      <div
        v-for="video in videos"
        :key="video.id"
        class="video-card"
        @click="viewVideoDetails(video)"
      >
        <!-- 删除按钮 - 右上角圆形X按钮 -->
        <div class="delete-btn" @click.stop="deleteVideo(video.id)">
          <el-icon><Delete /></el-icon>
        </div>

        <!-- 视频区域 - 包含标题、分辨率、点击触发详情 -->
        <div class="video-image">
          <img
            v-if="video.thumbnail_path"
            :src="`${apiBaseUrl}/assets/Media/Videos/${video.thumbnail_path}`"
            :alt="video.title"
            @error="onImageError"
            style="object-fit: contain; width: 100%; height: 100%;"
          />
          <div v-else class="no-thumbnail">
            <el-icon><VideoPlay /></el-icon>
            <span>无缩略图</span>
          </div>

          <!-- 右下角时长和文件大小 -->
          <div class="video-info-bottom">
            <span v-if="video.duration" class="video-duration">{{ formatDuration(video.duration) }}</span>
            <span v-if="video.file_size" class="video-file-size">{{ formatFileSize(video.file_size) }}</span>
          </div>
        </div>

        <div class="video-info">
          <div class="video-title">{{ video.title }}</div>
          <div class="video-upload-time">{{ video.upload_time }}</div>
          <div class="card-tags-container" v-if="video.tags">
            <div
              v-for="tag in video.tags.split(',')"
              :key="tag"
              class="card-tags"
            >
              {{ tag.trim() }}
            </div>
          </div>
          <p class="machine" v-if="video.machine_info">
            机器: {{ video.machine_info.model }} - {{ video.machine_info.original_model }}
          </p>
          <div class="video-actions">
            <!-- 编辑功能已整合到详情对话框中 -->
          </div>
        </div>
      </div>
    </div>

    <!-- 无搜索结果提示 -->
    <div v-else class="no-results">
      <el-empty
        :description="searchQuery || selectedMachine ? '没有找到匹配的视频' : '暂无视频'"
        :image-size="100">
      </el-empty>
      <div v-if="searchQuery || selectedMachine" class="no-results-actions">
        <el-button type="primary" @click="clearSearch">返回视频主页</el-button>
      </div>
    </div>

    <!-- 搜索结果统计和分页 -->
    <div class="result-info" v-if="videos.length > 0">
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalVideos"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 上传视频对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传视频"
      width="600px"
      :before-close="handleUploadDialogClose"
      class="mobile-dialog"
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="视频标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入视频标题" />
        </el-form-item>
        <el-form-item label="关联机器" prop="machineId">
          <el-select v-model="uploadForm.machineId" placeholder="选择关联机器" clearable style="width: 100%;">
            <el-option
              v-for="machine in machineList"
              :key="machine.model"
              :label="`${machine.model} - ${machine.original_model}`"
              :value="machine.model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-input
            v-model="uploadForm.tags"
            placeholder="多个标签用逗号分隔，例如：故障,检修,2024"
            @keyup.enter="addTag"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="uploadForm.remark"
            type="textarea"
            placeholder="请输入备注信息"
            :rows="2"
          />
        </el-form-item>
        <el-form-item label="视频文件" prop="file">
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="1"
            :on-remove="handleFileRemove"
            :accept="'.mp4,.avi,.mov,.mkv,.wmv'"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将视频拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 mp4/avi/mov/mkv/wmv 格式视频，大小不超过500MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <!-- 上传进度条 -->
        <el-form-item v-if="uploadProgress > 0" label="上传进度">
          <div style="width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin-top: 8px;">
            <div :style="{width: `${uploadProgress}%`, height: '100%', backgroundColor: uploadProgress === 100 ? '#67c23a' : '#409eff', borderRadius: '4px', transition: 'width 0.3s ease'}"></div>
          </div>
          <div style="text-align: right; margin-top: 4px; font-size: 12px; color: #606266;">{{ uploadProgress }}%</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 视频详情对话框 -->
    <el-dialog
      v-model="showDetailsDialog"
      title="视频详情"
      :before-close="handleDialogClose"
      class="mobile-dialog details-dialog"
      width="90%"
    >
      <div v-if="selectedVideo" class="video-details-container">
        <!-- 左右分栏布局 -->
        <div class="video-details-left">
          <div class="video-preview-wrapper">
            <video
              :src="`${apiBaseUrl}/assets/Media/Videos/${selectedVideo.compressed_path || selectedVideo.original_path}`"
              :alt="selectedVideo.title"
              controls
              class="video-preview"
              @error="onVideoError"
            />
            <!-- 预览图底部操作 -->
            <div class="preview-actions">
              <el-button
                v-if="selectedVideo.original_path"
                type="text"
                @click="downloadVideo"
                size="small"
              >
                <el-icon class="icon-download"><Download /></el-icon> 下载视频
              </el-button>
            </div>
          </div>
        </div>

        <div class="video-details-right">
          <!-- 标题区域 -->
          <div class="detail-section">
            <div v-if="!isEditingAll" class="detail-row title-row">
              <label class="detail-label">标题:</label>
              <span class="detail-value small detail-title">{{ selectedVideo.title }}</span>
            </div>
            <div v-else class="detail-row">
              <label class="detail-label">标题:</label>
              <el-input
                v-model="editTitle"
                placeholder="输入视频标题"
                class="title-input"
              />
            </div>
          </div>

          <!-- 关联机器 -->
          <div v-if="selectedVideo.machine_info" class="detail-section">
            <div class="detail-row">
              <label class="detail-label">关联机器:</label>
              <span class="detail-value machine-value">
                {{ selectedVideo.machine_info.model }} ( {{ selectedVideo.machine_info.original_model }} )
              </span>
            </div>
          </div>

          <!-- 标签区域 -->
          <div class="detail-section">
            <label class="detail-label">标签:</label>
            <div class="tags-container">
              <el-tooltip
                v-for="tag in currentTags"
                :key="tag"
                :content="tag"
                placement="top"
              >
                <el-tag
                  closable
                  :disable-transitions="false"
                  @close="isEditingAll ? removeTag(tag) : ''"
                  class="detail-tag"
                  :class="{ 'tag-disabled': !isEditingAll }"
                >
                  {{ tag.trim() }}
                </el-tag>
              </el-tooltip>
              <el-input
                v-if="isEditingAll"
                v-model="editTagsInput"
                class="tag-input"
                size="small"
                @keyup.enter="addTagFromInput"
                placeholder="回车添加标签"
              />
            </div>
          </div>

          <!-- 备注区域 -->
          <div class="detail-section">
            <div v-if="!isEditingAll" class="detail-row" style="flex-direction: column;">
              <label class="detail-label">备注:</label>
              <div class="detail-value remark-value">
                {{ selectedVideo.remark || '无备注' }}
              </div>
            </div>
            <div v-else>
              <label class="detail-label">备注:</label>
              <el-input
                v-model="editRemark"
                type="input"
                :rows="4"
                placeholder="请输入备注信息"
                class="remark-input"
              />
            </div>
          </div>

          <!-- 文件信息区域 -->
          <div class="detail-section info-section">
            <div class="info-grid">
              <div class="info-item">
                <label class="detail-label small">上传时间:</label>
                <span class="detail-value small">{{ formatDate(selectedVideo.upload_time) }}</span>
              </div>
              <div class="info-item">
                <label class="detail-label small">上传者:</label>
                <span class="detail-value small">{{ selectedVideo.uploader }}</span>
              </div>
              <div class="info-item">
                <label class="detail-label small">文件大小:</label>
                <span class="detail-value small">{{ formatFileSize(selectedVideo.file_size) }}</span>
              </div>
              <div class="info-item" v-if="selectedVideo.duration">
                <label class="detail-label small">视频时长:</label>
                <span class="detail-value small">{{ formatDuration(selectedVideo.duration) }}</span>
              </div>
              <div class="info-item" v-if="selectedVideo.original_width && selectedVideo.original_height">
                <label class="detail-label small">视频分辨率:</label>
                <span class="detail-value small">{{ selectedVideo.original_width }} x {{ selectedVideo.original_height }}</span>
              </div>
            </div>
          </div>

          <!-- 底部操作按钮 -->
          <div class="detail-actions">
            <el-button
              v-if="!isEditingAll"
              type="primary"
              @click="startEditingAll"
            >
              编辑视频信息
            </el-button>
            <div v-else class="edit-actions-group">
              <el-button
                type="success"
                @click="saveAll"
                :loading="savingAll"
              >
                保存所有更改
              </el-button>
              <el-button @click="cancelEditingAll">取消</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled, Delete, Download, VideoPlay } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import CommonHeader from '@/components/CommonHeader.vue';
import { uploadFile } from '@/utils/upload';
import request, { getMachinesForVideos, createVideo, updateVideo, deleteVideo as deleteVideoAPI } from '@/utils/request';

// 响应式数据
const videos = ref<any[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);
const totalVideos = ref(0);
const searchQuery = ref('');
const selectedMachine = ref('');
const showUploadDialog = ref(false);
const showResultCount = ref(false); // 是否显示结果计数

const showDetailsDialog = ref(false);
const showPreviewDialog = ref(false);
const uploading = ref(false);
const uploadProgress = ref(0); // 上传进度

const uploadForm = ref({
  title: '',
  tags: '',
  machineId: '',
  remark: '',
  file: null as File | null
});

// 表单引用
const uploadFormRef = ref();

const selectedVideo = ref<any>(null);
const previewVideoData = ref<any>(null);
const fileList = ref<any[]>([]);
const machineList = ref<any[]>([]);

// 预览相关变量
const isShowingOriginal = ref(false);
const currentPreviewPath = ref('');

// 编辑相关变量
const isEditingAll = ref(false);
const editTitle = ref('');
const editTagsInput = ref('');
const editRemark = ref('');
const currentTags = ref<string[]>([]);
const savingAll = ref(false);

// 表单验证规则
const uploadRules = {
  title: [{ required: true, message: '请输入视频标题', trigger: 'blur' }],
  file: [{ required: true, message: '请选择视频文件', trigger: 'change' }]
};

// 获取router
const router = useRouter();

// API基础URL
const apiBaseUrl = computed(() => {
  // 根据环境变量确定API基础URL
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // 开发环境默认使用开发服务器代理
  return '';
});

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN');
};

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 格式化视频时长
const formatDuration = (seconds: number) => {
  if (!seconds) return '00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  } else {
    return `${m}:${s.toString().padStart(2, '0')}`;
  }
};

// 定义行点击处理函数
const showVideoDetails = (video) => {
  viewVideoDetails(video)
};

// 图片加载错误处理
const onImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  // 检查是否已经是默认图片，防止死循环
  if (!target.src.includes("default-image") && !target.src.startsWith("data:image")) {
    // 使用一个base64编码的默认图片
    target.src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjEwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gSW1hZ2U8L3RleHQ+PC9zdmc+";
  }
};

// 视频加载错误处理
const onVideoError = (event: Event) => {
  console.error('视频加载失败:', event);
  ElMessage.error('视频加载失败');
};

// 获取视频列表
const fetchVideos = async () => {
  try {
    const response = await request.get('/api/videos', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        search: searchQuery.value,
        machine_id: selectedMachine.value
      }
    });

    videos.value = response.videos;
    totalVideos.value = response.total;
  } catch (error) {
    console.error('获取视频列表失败:', error);
    ElMessage.error('获取视频列表失败');
  }
};

// 获取机器列表
const fetchMachines = async () => {
  try {
    const response = await getMachinesForVideos();
    machineList.value = response;
  } catch (error) {
    console.error('获取机器列表失败:', error);
    ElMessage.error('获取机器列表失败');
  }
};

// 文件选择处理
const handleFileChange = (file: any) => {
  // 检查文件类型
  const allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/x-ms-wmv'];
  if (!allowedTypes.includes(file.raw.type)) {
    ElMessage.error('仅支持mp4/avi/mov/mkv/wmv格式的视频');
    return;
  }

  // 检查文件大小
  const maxSize = 500 * 1024 * 1024; // 500MB
  if (file.raw.size > maxSize) {
    ElMessage.error('文件大小不能超过500MB');
    return;
  }

  uploadForm.value.file = file.raw;
  fileList.value = [file];

  // 如果标题为空，自动填充文件名（不含扩展名）
  if (!uploadForm.value.title) {
    const fileName = file.raw.name;
    const lastDotIndex = fileName.lastIndexOf('.');
    if (lastDotIndex > 0) {
      uploadForm.value.title = fileName.substring(0, lastDotIndex);
    } else {
      uploadForm.value.title = fileName;
    }
  }
};

// 文件移除处理
const handleFileRemove = () => {
  uploadForm.value.file = null;
  fileList.value = [];
};

// 关闭上传对话框
const handleUploadDialogClose = (done: () => void) => {
  if (uploading.value) {
    return;
  }
  done();
};

// 添加标签函数
const addTag = () => {
  // 这个函数可以用于添加标签，但目前我们只需要让输入框响应回车键
  console.log('addTag called');
};

// 提交上传
const submitUpload = async () => {
  // @ts-ignore
  if (uploadFormRef?.value) {
    // @ts-ignore
    const valid = await uploadFormRef.value.validate().catch(() => false);
    if (!valid) {
      return;
    }
  }

  if (!uploadForm.value.file) {
    ElMessage.error('请选择视频文件');
    return;
  }

  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', uploadForm.value.file);
    formData.append('title', uploadForm.value.title);
    formData.append('tags', uploadForm.value.tags);
    formData.append('machine_id', uploadForm.value.machineId);
    formData.append('remark', uploadForm.value.remark);

    // 从token中解析用户信息作为上传者
    const token = localStorage.getItem('oa_token');
    let uploader = 'system';
    if (token) {
      try {
        // 解码JWT token获取用户名
        const payload = JSON.parse(atob(token.split('.')[1]));
        // 优先使用员工的emp_id，如果不存在则使用其他字段
        uploader = payload.emp_id || payload.employee_id || payload.username || payload.user || 'system';
      } catch (error) {
        console.error('解析用户信息失败:', error);
      }
    }
    formData.append('uploader', uploader);

    const response = await createVideo(formData, (progressEvent) => {
      // 上传进度回调
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      }
    });

    ElMessage.success('视频上传成功');
    showUploadDialog.value = false;
    resetUploadForm();
    fetchVideos(); // 刷新列表
  } catch (uploadError) {
    console.error('上传视频失败:', uploadError);
    ElMessage.error('上传失败');
  } finally {
    uploading.value = false;
    uploadProgress.value = 0; // 重置进度条
  }
};

// 重置上传表单
const resetUploadForm = () => {
  uploadForm.value = {
    title: '',
    tags: '',
    machineId: '',
    remark: '',
    file: null
  };
  fileList.value = [];
  uploadProgress.value = 0;
};

// 删除视频
const deleteVideo = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个视频吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await deleteVideoAPI(id);

    ElMessage.success('视频删除成功');
    fetchVideos(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除视频失败:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 查看视频详情
const viewVideoDetails = (video: any) => {
  selectedVideo.value = video;
  // 初始化编辑值
  editTitle.value = video?.title || '';
  editRemark.value = video?.remark || '';
  // 初始化标签显示
  const tagsString = video?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];

  // 重置编辑状态
  isEditingAll.value = false;
  editTagsInput.value = '';

  showDetailsDialog.value = true;
};

// 添加标签
const addTagFromInput = () => {
  if (editTagsInput.value.trim()) {
    // 按逗号分隔输入的标签
    const newTags = editTagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);

    newTags.forEach(tag => {
      if (!currentTags.value.includes(tag)) {
        currentTags.value.push(tag);
      }
    });

    editTagsInput.value = '';
  }
};

// 移除标签
const removeTag = (tagToRemove: string) => {
  const index = currentTags.value.indexOf(tagToRemove);
  if (index > -1) {
    currentTags.value.splice(index, 1);
  }
};

// 开始编辑所有信息
const startEditingAll = () => {
  editTitle.value = selectedVideo.value?.title || '';
  editRemark.value = selectedVideo.value?.remark || '';
  const tagsString = selectedVideo.value?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
  isEditingAll.value = true;
  editTagsInput.value = '';
};

// 保存所有更改
const saveAll = async () => {
  if (!selectedVideo.value) return;

  savingAll.value = true;
  try {
    const tagsString = currentTags.value.join(',');
    await updateVideo(selectedVideo.value.id, {
      title: editTitle.value,
      tags: tagsString,
      machine_id: selectedVideo.value.machine_id,
      remark: editRemark.value
    });

    // 更新本地数据
    selectedVideo.value.title = editTitle.value;
    selectedVideo.value.tags = tagsString;
    selectedVideo.value.remark = editRemark.value;

    // 同时更新videos列表中的对应项
    const videoIndex = videos.value.findIndex(video => video.id === selectedVideo.value.id);
    if (videoIndex !== -1) {
      videos.value[videoIndex].title = editTitle.value;
      videos.value[videoIndex].tags = tagsString;
      videos.value[videoIndex].remark = editRemark.value;
    }

    ElMessage.success('视频信息更新成功');
    isEditingAll.value = false;
  } catch (error) {
    console.error('更新视频信息失败:', error);
    ElMessage.error('视频信息更新失败');
  } finally {
    savingAll.value = false;
  }
};

// 取消所有编辑
const cancelEditingAll = () => {
  // 重新加载原始值
  editTitle.value = selectedVideo.value?.title || '';
  editRemark.value = selectedVideo.value?.remark || '';
  const tagsString = selectedVideo.value?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
  isEditingAll.value = false;
  editTagsInput.value = '';
};

// 下载视频
const downloadVideo = () => {
  if (selectedVideo.value?.original_path) {
    const originalVideoUrl = `${apiBaseUrl.value}/assets/Media/Videos/${selectedVideo.value.original_path}`;
    // 创建一个临时链接来下载视频，并以视频标题命名
    const link = document.createElement('a');
    link.href = originalVideoUrl;
    // 使用视频标题作为文件名，如果标题为空则使用默认名称
    const fileName = selectedVideo.value.title ? selectedVideo.value.title.trim() : 'video';
    // 确保文件扩展名正确
    const fileExtension = originalVideoUrl.split('.').pop() || 'mp4';
    link.download = `${fileName}.${fileExtension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

// 处理对话框关闭
const handleDialogClose = () => {
  // 如果正在编辑，先取消编辑
  if (isEditingAll.value) {
    cancelEditingAll();
  }

  // 停止视频播放
  const videoElement = document.querySelector('.video-preview') as HTMLVideoElement;
  if (videoElement) {
    videoElement.pause();
  }

  showDetailsDialog.value = false;
};

// 内容搜索
const searchContent = async () => {
  currentPage.value = 1;
  showResultCount.value = !!(searchQuery.value); // 只有在有搜索内容时显示计数
  await fetchVideos();
};

// 机器搜索
const searchByMachine = async () => {
  currentPage.value = 1;
  showResultCount.value = selectedMachine.value !== '' && selectedMachine.value !== null && selectedMachine.value !== undefined; // 只有在选择了机器时显示计数
  await fetchVideos();
};

// 清除搜索条件并返回主页
const clearSearch = () => {
  searchQuery.value = '';
  selectedMachine.value = '';
  showResultCount.value = false;
  currentPage.value = 1;
  fetchVideos();
};

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  if (searchQuery.value || selectedMachine.value) {
    showResultCount.value = true; // 保持搜索状态下的计数显示
  } else {
    showResultCount.value = false; // 非搜索状态下不显示计数
  }
  fetchVideos();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  if (searchQuery.value || selectedMachine.value) {
    showResultCount.value = true; // 保持搜索状态下的计数显示
  } else {
    showResultCount.value = false; // 非搜索状态下不显示计数
  }
  fetchVideos();
};

// 初始化
onMounted(() => {
  fetchVideos();
  fetchMachines();
});
</script>

<style scoped>
.video-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title-with-count {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-count {
  font-size: 14px;
  color: #606266;
  background-color: #f0f2f5;
  padding: 4px 10px;
  border-radius: 12px;
}

.no-results-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.search-section {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
  padding: 10px;
  border-radius: 15px;
}

.video-card {
  position: relative; /* 为删除按钮定位做准备 */
  width: 100%; /* 适应容器 */
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  overflow: hidden;
  margin: 5px;
  box-shadow: 2px 2px 4px rgba(0,0,0,0.1);
  cursor: pointer;
}

.delete-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.8);
  color: #f56c6c; /* 危险色 */
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10; /* 确保在最上层 */
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s;
}

.delete-btn:hover {
  background-color: #f56c6c;
  color: white;
}

.video-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.video-image {
  position: relative; /* 为标题和分辨率定位做准备 */
  width: 100%;
  height: 180px; /* 适配移动端 */
  overflow: hidden;
  cursor: pointer; /* 提示可点击 */
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

.video-image img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 保持图片比例 */
}

.no-thumbnail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #909399;
}

.no-thumbnail .el-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.video-title {
  font-size: 14px; /* 适配移动端 */
  font-weight: bold;
  max-width: 80%; /* 防止标题过长 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-upload-time {
  font-size: 11px; /* 适配移动端 */
  color: #909399;
}

.card-tags-container {
  white-space: nowrap;
  overflow: hidden;
  max-width: 80%; /* 占满父元素宽度 */
  text-overflow: ellipsis;
}

.card-tags {
  display: inline-block;
  background-color: #bedbfc;
  color: #013b75;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 11px; /* 适配移动端 */
  margin-right: 5px;
  margin-top: 6px;
}

/* 右下角时长和文件大小样式 */
.video-info-bottom {
  position: absolute;
  bottom: 10px;
  left: 10px;  /* 改为左边对齐 */
  right: 10px; /* 同时设置右边距，使内容居中或对齐 */
  color: white;
  z-index: 5;
  display: flex;
  justify-content: space-between;  /* 左右分布 */
}

.video-info-bottom span {
  font-size: 11px; /* 适配移动端 */
  background-color: rgba(0, 0, 0, 0.5);
  padding: 2px 6px;
  border-radius: 4px;
}

.video-info {
  padding: 12px; /* 适配移动端 */
}

.video-info h4 {
  margin: 0 0 10px 0;
  font-size: 15px; /* 适配移动端 */
  font-weight: 600;
}

.machine {
  color: #606266;
  font-size: 13px; /* 适配移动端 */
  margin: 5px 0;
  word-break: break-word; /* 防止文本溢出 */
}

.upload-time,
.uploader {
  color: #909399;
  font-size: 11px; /* 适配移动端 */
  margin: 3px 0;
}

.video-actions {
  margin-top: 10px;
  display: flex;
  gap: 5px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.preview-container {
  text-align: center;
}

.preview-footer {
  text-align: center;
}

/* 优化后的视频详情布局 */
.video-details-container {
  display: flex;
  gap: 24px;
  padding: 16px 0;
  flex-direction: row; /* 移动端改为垂直布局 */
}

/* 左侧预览区 */
.video-details-left {
  flex: 1;
  min-width: 300px;
  display: flex;
  align-items: center;
  min-height: 100px;
  background-color: #363636;
  border-radius: 5px;

}

.video-preview-wrapper {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: #000;
}

.video-preview {
  width: 100%;
  height: auto;
  display: block;
  max-height: 400px;
}

.preview-actions {
  position: absolute;
  bottom: 0;
  right: 0;
  padding: 8px 12px;
  background: linear-gradient(to top, rgba(0,0,0,0.3), transparent);
}

.preview-actions .el-button {
  color: white;
}

/* 右侧信息区 */
.video-details-right {
  flex: 1.2;
  min-width: 300px;
  overflow-y: scroll;
}

.detail-section {
  padding-bottom: 16px;
}

.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-direction: column;
}

.detail-label {
  width: 80px;
  color: #666;
  font-weight: 500;
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
  color: #333;
  word-break: break-word;
}

/* 标题样式 */
.title-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.detail-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  color: #1f2937;
  border: rgba(0, 0, 0, 0.1)  1px solid;
  width: 80%;
  line-height: 30px;
  border-radius: 5px;
  padding: 0 8px;
}

.title-input {
  flex: 1;
}

/* 标签样式 */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  border: rgba(0, 0, 0, 0.1)  1px solid;
  width: 80%;
  height: 30px;
  border-radius: 5px;
  padding: 0 8px;
  align-items: center;
}

.detail-tag {
  transition: all 0.2s;
}

.tag-disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.tag-input {
  width: 140px;
}

/* 备注样式 */
.remark-value {
  line-height: 1.6;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.remark-input {
  margin-top: 8px;
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label.small {
  width: auto;
  font-size: 13px;
}

.detail-value.small {
  font-size: 13px;
}

/* 机器信息样式 */
.machine-value {
  color: #409eff;
  font-weight: 500;
}

/* 操作按钮 */
.detail-actions {
  margin-top: 24px;
  text-align: right;
}

.edit-actions-group {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}


/* 响应式适配 */
@media (max-width: 768px) {
  .video-management {
    padding: 10px;
  }

  .header {
    flex-direction: column;
    align-items: stretch;
  }

  .search-section {
    flex-direction: column;
    align-items: stretch;
  }

  .video-grid {
    grid-template-columns: 1fr; /* 移动端单列布局 */
    padding: 5px;
  }

  .video-card {
    margin: 5px 0;
  }

  .video-image {
    height: 200px; /* 移动端稍微大一些 */
  }

  .video-details-container {
    flex-direction: column;
  }

  .video-details-left,
  .video-details-right {
    width: 100%;
    min-width: auto;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .detail-label {
    width: 70px;
    font-size: 12px;
  }

  /* 移动端对话框适配 */
  .mobile-dialog {
    width: 85% !important;
    margin-top: 2vh;
  }

  .details-dialog {
    width: 98% !important;
  }

  .video-details-container {
    flex-direction: column;
    padding: 8px 0;
  }

  .video-details-left,
  .video-details-right {
    width: 100%;
    min-width: auto;
  }

  .video-preview {
    max-height: 300px;
  }

  .info-grid {
    grid-template-columns: 1fr !important;
  }

  .detail-label {
    width: 70px !important;
    font-size: 12px;
  }

  .detail-actions {
    text-align: center;
  }

  .edit-actions-group {
    justify-content: center !important;
  }
}

@media (max-width: 480px) {
  .video-management {
    padding: 8px;
  }

  .video-image {
    height: 160px;
  }

  .video-title {
    font-size: 13px;
  }

  .detail-label {
    width: 60px;
    font-size: 11px;
  }

  .detail-value {
    font-size: 12px;
  }

  .detail-section {
    padding: 8px 0;
  }

  /* 移动端对话框适配 */
  .mobile-dialog {
    width: 98% !important;
    margin-top: 5vh;
  }

  .video-preview {
    max-height: 200px;
  }

  .detail-label {
    width: 60px !important;
    font-size: 11px;
  }

  .detail-value {
    font-size: 12px;
  }

  .tag-input {
    width: 100% !important;
    margin-top: 8px;
  }
}

.result-info {
  margin-top: 20px;
}

.result-count {
  margin-bottom: 10px;
  color: #606266;
  font-size: 14px;
}

.no-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 20px;
}

.icon-download {
  margin-right: 5px;
  font-size: 18px;
}
</style>