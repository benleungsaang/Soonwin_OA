<template>
  <div class="photo-management">
    <CommonHeader title="照片管理" />
    <div class="header">
      <div class="title-with-count">
        <h2>照片管理</h2>
        <span v-if="showResultCount" class="result-count">
          找到 {{ totalPhotos }} 张照片

        </span>
        <el-icon
          v-if="showResultCount"
          @click="clearSearch"
          class="result-refresh-btn"
        ><RefreshLeft /></el-icon>
      </div>
      <div class="header-buttons">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><UploadFilled /></el-icon>
          上传照片
        </el-button>
        <el-button
          v-if="isAdmin"
          @click="showPhotoLogs"
        >
          <el-icon><Document /></el-icon>
          查看日志
        </el-button>
      </div>
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

    <!-- 照片列表 -->
    <div v-if="photos.length > 0" class="photo-grid">
      <div
    v-for="photo in photos"
    :key="photo.id"
    class="photo-card"
    @click="viewPhotoDetails(photo)"
  >
    <!-- 删除按钮 - 右上角圆形X按钮 -->
    <div class="delete-btn" @click.stop="deletePhoto(photo.id)">
      <el-icon><Delete /></el-icon>
    </div>

    <!-- 图片区域 - 包含标题、分辨率、点击触发详情 -->
    <div class="photo-image" >

      <img
        :src="`${apiBaseUrl}/assets/Media/Photos/${photo.thumbnail_path}`"
        :alt="photo.title"
        @error="onImageError"
      />

      <!-- 右下角分辨率 -->
      <div class="photo-resolution" v-if="photo.original_width && photo.original_height">
        {{ photo.original_width }} x {{ photo.original_height }}
      </div>
    </div>

    <div class="photo-info">

      <div class="photo-title">{{ photo.title }}</div>
      <div class="photo-upload-time">{{ photo.upload_time }}</div>
      <div class="card-tags-container" v-if="photo.tags">
        <div
          v-for="tag in photo.tags.split(',')"
          :key="tag"
          class="card-tags"
        >
          {{ tag.trim() }}
        </div>
      </div>
      <p class="machine" v-if="photo.machine_info">
        机器: {{ photo.machine_info.model }} - {{ photo.machine_info.original_model }}
      </p>
      <div class="photo-actions">
        <!-- 编辑功能已整合到详情对话框中 -->
      </div>
    </div>
  </div>
    </div>

    <!-- 无搜索结果提示 -->
    <div v-else class="no-results">
      <el-empty
        :description="searchQuery || selectedMachine ? '没有找到匹配的照片' : '暂无照片'"
        :image-size="100">
      </el-empty>
      <div v-if="searchQuery || selectedMachine" class="no-results-actions">
        <el-button type="primary" @click="clearSearch">返回照片主页</el-button>
      </div>
    </div>

    <!-- 搜索结果统计和分页 -->
    <div class="result-info" v-if="photos.length > 0">
      <!-- <div class="result-count">
        共找到 {{ totalPhotos }} 张照片
      </div> -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalPhotos"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 上传照片对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传照片"
      width="600px"
      :before-close="handleUploadDialogClose"
      class="mobile-dialog"
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="照片标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入照片标题" />
        </el-form-item>
        <el-form-item label="关联机器" prop="machineId">
          <el-select v-model="uploadForm.machineId" placeholder="选择关联机器" clearable style="width: 100%;">
            <el-option
              v-for="machine in machineList"
              :key="machine.model"
              :label="`${machine.model}`"
              :value="machine.model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <!-- 使用 el-input-tag 替换原有自定义标签结构 -->
          <el-input-tag
            v-model="uploadFormTags"
            placeholder="请输入标签，多个标签用逗号分隔"
            delimiter=","
            class="tag-input-wrapper"
            size="small"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="uploadForm.remark"
            type="textarea"
            placeholder="请输入备注信息"
            :rows="2"
            :show-file-list="true"
          />
        </el-form-item>
        <el-form-item label="照片文件" prop="file">
          <el-upload
            ref="uploadRef"
            drag
            multiple
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="true"
            :on-remove="handleFileRemove"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将照片拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 png/jpg/jpeg/webp 格式图片，大小不超过50MB
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
          <el-button @click="showJsonInputDialog = true">JSON匹配多文件</el-button>
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
        </span>
      </template>
    </el-dialog>



    <!-- 照片详情对话框 -->
    <el-dialog
      v-model="showDetailsDialog"
      title="照片详情"
      width="900px"
      :before-close="handleDialogClose"
      class="mobile-dialog details-dialog"
    >
      <div v-if="selectedPhoto" class="photo-details-container">
        <!-- 左右分栏布局 -->
        <div class="photo-details-left">
          <div class="photo-preview-wrapper">
            <img
              :src="`${apiBaseUrl}/assets/Media/Photos/${selectedPhoto.normal_path}`"
              :alt="selectedPhoto.title"
              @error="onImageError"
              class="photo-preview-img"
            />
            <!-- 预览图底部操作 -->
            <div class="preview-actions">
              <el-button
                v-if="selectedPhoto.original_path"
                type="text"
                @click="viewOriginalImage"
                size="small"
              >
                <el-icon class="icon-zoomin"><ZoomIn /></el-icon> 查看原图
              </el-button>
            </div>
          </div>
        </div>

        <div class="photo-details-right">
          <!-- 标题区域 -->
          <div class="detail-section">
            <div v-if="!isEditingAll" class="detail-row title-row">
              <label class="detail-label">标题:</label>
              <h3 class="detail-title">{{ selectedPhoto.title }}</h3>
            </div>
            <div v-else class="detail-row">
              <label class="detail-label">标题:</label>
              <el-input
                v-model="editTitle"
                placeholder="输入照片标题"
                class="title-input"
              />
            </div>
          </div>

          <!-- 关联机器 -->
          <div v-if="selectedPhoto.machine_info" class="detail-section">
            <div class="detail-row">
              <label class="detail-label">关联机器:</label>
              <span class="detail-value machine-value">
                {{ selectedPhoto.machine_info.model }} ( {{ selectedPhoto.machine_info.original_model }} )
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
              <div class="detail-value remark-value" style="width: 90%;">
                {{ selectedPhoto.remark || '无备注' }}
              </div>
              <!-- <el-input
                v-model="editRemark"
                type="input"
                :rows="4"
                placeholder="请输入备注信息"
                class="detail-value remark-value"
                :value="selectedPhoto.remark || '无备注'"
                disabled
              /> -->
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
                <span class="detail-value small">{{ formatDate(selectedPhoto.upload_time) }}</span>
              </div>
              <div class="info-item">
                <label class="detail-label small">上传者:</label>
                <span class="detail-value small">{{ selectedPhoto.uploader }}</span>
              </div>
              <div class="info-item">
                <label class="detail-label small">文件大小:</label>
                <span class="detail-value small">{{ formatFileSize(selectedPhoto.file_size) }}</span>
              </div>
              <div class="info-item">
                <label class="detail-label small">原始尺寸:</label>
                <span class="detail-value small">{{ selectedPhoto.original_width }} x {{ selectedPhoto.original_height }}</span>
              </div>
              <!-- <div class="info-item">
                <label class="detail-label small">压缩状态:</label>
                <span class="detail-value small">
                  <el-tag :type="getCompressStatusType(selectedPhoto.compress_status)" size="small">
                    {{ getCompressStatusText(selectedPhoto.compress_status) }}
                  </el-tag>
                </span>
              </div> -->
            </div>
          </div>

          <!-- 底部操作按钮 -->
          <div class="detail-actions">
            <el-button
              v-if="!isEditingAll"
              type="primary"
              @click="startEditingAll"
            >
              编辑照片信息
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

    <!-- JSON匹配多文件对话框 -->
    <el-dialog
      v-model="showJsonInputDialog"
      title="JSON匹配多文件"
      width="800px"
      :before-close="() => { showJsonInputDialog = false; jsonInputText = ''; }"
      class="mobile-dialog"
    >
      <div>
        <p>请输入匹配信息，格式如下：</p>
        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0; white-space: pre-wrap; word-break: break-all;">
照片文件名	照片标题	关联机器	标签	备注
5328	测试标题1	VP-BF-210-10	标签1,标签2	测试备注1
1024	测试标题2	VP-BF-210-10	标签4,标签3	测试备注2
        </pre>
        <el-input
          v-model="jsonInputText"
          :rows="10"
          type="textarea"
          placeholder="请按上述格式输入匹配信息"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showJsonInputDialog = false">取消</el-button>
          <el-button type="primary" @click="matchJsonToFiles">匹配并上传</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 引入通用日志对话框组件 -->
    <CommonLogDialog
      v-model="logDialogVisible"
      log-type="photo"
      :handle-jump="handleLogJump"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled, Delete, ZoomIn, Document, RefreshLeft } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import CommonHeader from '@/components/CommonHeader.vue';
import CommonLogDialog from '@/components/CommonLogDialog.vue';
import { uploadFile } from '@/utils/upload';
import { isCurrentUserAdmin } from '@/utils/authUtils';
import request, { getMachinesForPhotos, createPhoto, updatePhoto, deletePhoto as deletePhotoAPI } from '@/utils/request';

// 响应式数据
const photos = ref<any[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);
const totalPhotos = ref(0);
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

const uploadFormTags = ref<string[]>([]);
const inputValueString = ref('');
const inputVisible = ref(false);
const inputValue = ref('');
const tagInputRef = ref();
const showJsonInputDialog = ref(false);
const jsonInputText = ref('');

// 监听uploadFormTags变化并更新uploadForm中的tags字段
watch(uploadFormTags, (newTags) => {
  uploadForm.value.tags = newTags.join(',');
  // 同时更新inputValueString以保持UI同步
  inputValueString.value = newTags.join(',');
}, { deep: true });

// 监听uploadForm中的tags变化并更新uploadFormTags
watch(() => uploadForm.value.tags, (newTags) => {
  if (newTags) {
    const tagsArray = newTags.split(',').filter(tag => tag.trim() !== '');
    uploadFormTags.value = tagsArray;
    inputValueString.value = newTags;
  } else {
    uploadFormTags.value = [];
    inputValueString.value = '';
  }
});

// 监听inputValueString的变化并更新uploadFormTags
watch(inputValueString, (newVal) => {
  if (newVal) {
    const tagsArray = newVal.split(',').filter(tag => tag.trim() !== '');
    uploadFormTags.value = tagsArray;
    uploadForm.value.tags = newVal;
  } else {
    uploadFormTags.value = [];
    uploadForm.value.tags = '';
  }
});

// 表单引用
const uploadFormRef = ref();

const selectedPhoto = ref<any>(null);

// 通用日志组件相关
const logDialogVisible = ref(false);
const previewPhotoData = ref<any>(null);
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
  title: [{ required: true, message: '请输入照片标题', trigger: 'blur' }],
  file: [{ required: true, message: '请选择照片文件', trigger: 'change' }]
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

// 权限相关
const isAdmin = computed(() => isCurrentUserAdmin());

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


// 定义行点击处理函数
const showPhotoDetails = (photo) => {
  viewPhotoDetails(photo)
};

// 获取压缩状态类型
const getCompressStatusType = (status: string) => {
  switch (status) {
    case 'success': return 'success';
    case 'processing': return 'warning';
    case 'failed': return 'danger';
    default: return 'info';
  }
};

// 获取压缩状态文本
const getCompressStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '待处理';
    case 'processing': return '处理中';
    case 'success': return '已完成';
    case 'failed': return '失败';
    default: return status;
  }
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

// 获取照片列表
const fetchPhotos = async () => {
  try {
    const response = await request.get('/api/photos', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        search: searchQuery.value,
        machine_id: selectedMachine.value
      }
    });

    photos.value = response.photos;
    totalPhotos.value = response.total;
  } catch (error) {
    console.error('获取照片列表失败:', error);
    ElMessage.error('获取照片列表失败');
  }
};

// 获取机器列表
const fetchMachines = async () => {
  try {
    const response = await getMachinesForPhotos();
    machineList.value = response;
  } catch (error) {
    console.error('获取机器列表失败:', error);
    ElMessage.error('获取机器列表失败');
  }
};

// 文件选择处理
const handleFileChange = (file: any) => {
  // 检查文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
  if (!allowedTypes.includes(file.raw.type)) {
    ElMessage.error('仅支持png/jpg/jpeg/webp格式的图片');
    return;
  }

  // 检查文件大小
  const maxSize = 50 * 1024 * 1024; // 50MB
  if (file.raw.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB');
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
    ElMessage.error('请选择照片文件');
    return;
  }

  uploading.value = true;
  uploadProgress.value = 0; // 重置进度
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

    const response = await createPhoto(formData, (progressEvent) => {
      // 上传进度回调
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      }
    });

    ElMessage.success('照片上传成功');
    showUploadDialog.value = false;
    resetUploadForm();
    fetchPhotos(); // 刷新列表
  } catch (uploadError) {
    console.error('上传照片失败:', uploadError);
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

// JSON匹配多文件相关函数
const matchJsonToFiles = () => {
  try {
    // 解析JSON输入
    const lines = jsonInputText.value.trim().split('\n').filter(line => line.trim() !== '');
    if (lines.length === 0) {
      ElMessage.error('请输入匹配信息');
      return;
    }

    // 解析表头
    const headers = lines[0].split('\t');
    if (headers.length < 5 || headers[0] !== '照片文件名' || headers[1] !== '照片标题' || 
        headers[2] !== '关联机器' || headers[3] !== '标签' || headers[4] !== '备注') {
      ElMessage.error('表头格式不正确，请使用：照片文件名\t照片标题\t关联机器\t标签\t备注');
      return;
    }

    // 解析数据行
    const dataRows = lines.slice(1).map(line => {
      const fields = line.split('\t');
      if (fields.length >= 5) {
        return {
          filename: fields[0],
          title: fields[1],
          machineId: fields[2],
          tags: fields[3],
          remark: fields[4]
        };
      }
      return null;
    }).filter(row => row !== null);

    // 匹配文件与数据
    const matchedFiles = [];
    const unmatchedFiles = [];

    fileList.value.forEach(fileObj => {
      const originalFilename = fileObj.name;
      const baseFilename = originalFilename.substring(0, originalFilename.lastIndexOf('.')); // 去掉扩展名
      
      const matchedData = dataRows.find(data => data.filename === baseFilename);
      if (matchedData) {
        matchedFiles.push({
          file: fileObj,
          data: matchedData
        });
      } else {
        unmatchedFiles.push(originalFilename);
      }
    });

    if (unmatchedFiles.length > 0) {
      ElMessage.warning(`以下文件未找到匹配数据: ${unmatchedFiles.join(', ')}`);
    }

    if (matchedFiles.length === 0) {
      ElMessage.warning('没有找到匹配的文件');
      return;
    }

    // 上传匹配的文件
    uploadMatchedFiles(matchedFiles);
    
    // 重置并关闭对话框
    jsonInputText.value = '';
    showJsonInputDialog.value = false;
  } catch (error) {
    console.error('匹配JSON数据失败:', error);
    ElMessage.error('解析JSON数据失败，请检查格式');
  }
};

// 批量上传匹配的文件
const uploadMatchedFiles = async (matchedFiles) => {
  if (matchedFiles.length === 0) {
    return;
  }

  uploading.value = true;
  let successCount = 0;
  let errorCount = 0;

  try {
    // 逐个上传匹配的文件
    for (let i = 0; i < matchedFiles.length; i++) {
      const matchedFile = matchedFiles[i];
      try {
        const { file, data } = matchedFile;
        const formData = new FormData();
        formData.append('file', file.raw || file);
        formData.append('title', data.title);
        formData.append('tags', data.tags);
        formData.append('machine_id', data.machineId);
        formData.append('remark', data.remark);

        // 从token中解析用户信息作为上传者
        const token = localStorage.getItem('oa_token');
        let uploader = 'system';
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            uploader = payload.emp_id || payload.employee_id || payload.username || payload.user || 'system';
          } catch (error) {
            console.error('解析用户信息失败:', error);
          }
        }
        formData.append('uploader', uploader);

        await createPhoto(formData, (progressEvent) => {
          // 上传进度回调 - 为了显示整体进度，需要计算每个文件的进度
          const fileProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          // 大略计算整体进度
          const overallProgress = Math.round(((i * 100) + fileProgress) / matchedFiles.length);
          uploadProgress.value = overallProgress;
        });

        successCount++;
      } catch (uploadError) {
        console.error(`上传文件 ${matchedFile.data.title} 失败:`, uploadError);
        errorCount++;
      }
    }

    ElMessage.success(`批量上传完成: ${successCount} 个成功, ${errorCount} 个失败`);
    showUploadDialog.value = false;
    resetUploadForm();
    fetchPhotos(); // 刷新列表
  } catch (error) {
    ElMessage.error(`批量上传过程中发生错误: ${error.message}`);
  } finally {
    uploading.value = false;
    uploadProgress.value = 0;
  }
};



// 删除照片
const deletePhoto = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这张照片吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await deletePhotoAPI(id);

    ElMessage.success('照片删除成功');
    fetchPhotos(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除照片失败:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 查看照片详情
const viewPhotoDetails = (photo: any) => {
  selectedPhoto.value = photo;
  // 初始化编辑值
  editTitle.value = photo?.title || '';
  editRemark.value = photo?.remark || '';
  // 初始化标签显示
  const tagsString = photo?.tags || '';
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
  editTitle.value = selectedPhoto.value?.title || '';
  editRemark.value = selectedPhoto.value?.remark || '';
  const tagsString = selectedPhoto.value?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
  isEditingAll.value = true;
  editTagsInput.value = '';
};

// 保存所有更改
const saveAll = async () => {
  if (!selectedPhoto.value) return;

  savingAll.value = true;
  try {
    const tagsString = currentTags.value.join(',');
    await updatePhoto(selectedPhoto.value.id, {
      title: editTitle.value,
      tags: tagsString,
      machine_id: selectedPhoto.value.machine_id,
      remark: editRemark.value
    });

    // 更新本地数据
    selectedPhoto.value.title = editTitle.value;
    selectedPhoto.value.tags = tagsString;
    selectedPhoto.value.remark = editRemark.value;

    // 同时更新photos列表中的对应项
    const photoIndex = photos.value.findIndex(photo => photo.id === selectedPhoto.value.id);
    if (photoIndex !== -1) {
      photos.value[photoIndex].title = editTitle.value;
      photos.value[photoIndex].tags = tagsString;
      photos.value[photoIndex].remark = editRemark.value;
    }

    ElMessage.success('照片信息更新成功');
    isEditingAll.value = false;
  } catch (error) {
    console.error('更新照片信息失败:', error);
    ElMessage.error('照片信息更新失败');
  } finally {
    savingAll.value = false;
  }
};

// 取消所有编辑
const cancelEditingAll = () => {
  // 重新加载原始值
  editTitle.value = selectedPhoto.value?.title || '';
  editRemark.value = selectedPhoto.value?.remark || '';
  const tagsString = selectedPhoto.value?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
  isEditingAll.value = false;
  editTagsInput.value = '';
};

// 查看原图
const viewOriginalImage = () => {
  if (selectedPhoto.value?.original_path) {
    const originalImageUrl = `${apiBaseUrl.value}/assets/Media/Photos/${selectedPhoto.value.original_path}`;
    // 在新窗口中打开原图
    window.open(originalImageUrl, '_blank');
  }
};

// 处理对话框关闭
const handleDialogClose = () => {
  // 如果正在编辑，先取消编辑
  if (isEditingAll.value) {
    cancelEditingAll();
  }
  showDetailsDialog.value = false;
};

// 内容搜索
const searchContent = async () => {
  currentPage.value = 1;
  showResultCount.value = !!(searchQuery.value); // 只有在有搜索内容时显示计数
  await fetchPhotos();
};

// 机器搜索
const searchByMachine = async () => {
  currentPage.value = 1;
  showResultCount.value = selectedMachine.value !== '' && selectedMachine.value !== null && selectedMachine.value !== undefined; // 只有在选择了机器时显示计数
  await fetchPhotos();
};

// 清除搜索条件并返回主页
const clearSearch = () => {
  searchQuery.value = '';
  selectedMachine.value = '';
  showResultCount.value = false;
  currentPage.value = 1;
  fetchPhotos();
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
  fetchPhotos();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  if (searchQuery.value || selectedMachine.value) {
    showResultCount.value = true; // 保持搜索状态下的计数显示
  } else {
    showResultCount.value = false; // 非搜索状态下不显示计数
  }
  fetchPhotos();
};

// 添加专门的日志跳转处理函数
const handleLogJump = async (id: number) => {
  console.log(`跳转到照片ID: ${id}`);

  // 首先检查当前页面的视频列表中是否包含该视频
  const currentPhoto = photos.value.find(photo => photo.id === id);

  if (currentPhoto) {
    // 如果在当前页面找到照片，直接打开详情
    viewPhotoDetails(currentPhoto);
  } else {
    // 如果当前页面没有找到，需要从服务器获取该照片信息
    try {
      const response = await request.get(`/api/photos/${id}`);

      // 检查响应是否成功
      if (response && response.code === 200) {
        const responseData = response.data; // 获取实际数据
        // 打开照片详情
        viewPhotoDetails(responseData);
      } else {
        // 如果后端返回了错误格式的响应
        if (response && response.code !== 200 &&
            response.msg && (response.msg.includes('404') || response.msg.toLowerCase().includes('not found'))) {
          ElMessage.error('该照片已删除或不存在');
        } else {
          ElMessage.error('加载照片详情失败');
        }
      }
    } catch (error: any) {
      console.error('加载照片详情失败:', error);
      // 检查错误是否为404相关的错误
      if (error && error.response) {
        const responseData = error.response.data;
        if (responseData && typeof responseData === 'object' &&
            responseData.msg && (responseData.msg.includes('404') || responseData.msg.toLowerCase().includes('not found'))) {
          ElMessage.error('该照片已删除或不存在');
        } else {
          ElMessage.error('加载照片详情失败');
        }
      } else {
        ElMessage.error('加载照片详情失败');
      }
    }
  }
};

// 显示照片日志
const showPhotoLogs = () => {
  if (!isAdmin.value) {
    ElMessage.error('您没有权限查看日志');
    return;
  }
  // 先重置日志组件的状态，再显示对话框
  logDialogVisible.value = false;
  // 使用nextTick确保状态更新后再显示
  nextTick(() => {
    logDialogVisible.value = true;
  });
};

// 初始化
onMounted(() => {
  fetchPhotos();
  fetchMachines();
});
</script>

<style scoped>
.photo-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
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

.result-refresh-btn{
  cursor: pointer;
  margin-left: 5px;
  font-size: 20px;
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

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
  padding: 10px;
  border-radius: 15px;
}

.photo-card {
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

.photo-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}


.photo-image {
  position: relative; /* 为标题和分辨率定位做准备 */
  width: 100%;
  height: 180px; /* 适配移动端 */
  overflow: hidden;
  cursor: pointer; /* 提示可点击 */
}

.photo-image img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 保持图片比例 */
}

.photo-title {
  font-size: 14px; /* 适配移动端 */
  font-weight: bold;
  max-width: 80%; /* 防止标题过长 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.photo-upload-time {
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


/* 右下角分辨率样式 */
.photo-resolution {
  position: absolute;
  bottom: 10px;
  right: 10px;
  color: white;
  font-size: 11px; /* 适配移动端 */
  background-color: rgba(0, 0, 0, 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  z-index: 5;
}

.photo-info {
  padding: 12px; /* 适配移动端 */
}

.photo-info h4 {
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

.photo-actions {
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

/* 优化后的照片详情布局 */
.photo-details-container {
  display: flex;
  gap: 24px;
  padding: 16px 0;
  flex-direction: column; /* 移动端改为垂直布局 */
}

/* 左侧预览区 */
.photo-details-left {
  flex: 1;
  min-width: 300px;
}

.photo-preview-wrapper {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: #fafafa;
}

.photo-preview-img {
  width: 100%;
  height: auto;
  display: block;
}

.preview-actions {
  position: absolute;
  bottom: 0;
  /* left: 0; */
  right: 0;
  padding: 8px 12px;
  background: linear-gradient(to top, rgba(0,0,0,0.3), transparent);
}

.preview-actions .el-button {
  color: white;
}

/* 右侧信息区 */
.photo-details-right {
  flex: 1.2;
  min-width: 300px;
  overflow-y: scroll;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
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
  align-items: center;
}

.detail-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
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

/* 上传表单标签输入样式（适配el-input） */
.tag-input-wrapper {
  width: 100%;
}

.tag-input-wrapper :deep(.el-input__wrapper) {
  padding: 0 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  min-height: 34px;
  border-radius: 4px;
}

/* 保留并适配原有标签样式，确保视觉一致 */
.tag-input-wrapper {
  /* 继承原有容器样式 */
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  min-height: 32px;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

/* 适配 el-input-tag 内部标签样式 */
:deep(.el-input-tag__content) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  width: 100%;
}

/* 标签项样式（对齐原有 tag-item 样式） */
:deep(.el-tag) {
  height: 24px;
  line-height: 24px;
  padding: 0 8px;
  background-color: #ecf5ff;
  border-color: #d9ecff;
  color: #409eff;
  border-radius: 4px;
  margin: 2px;
}

/* 标签关闭按钮样式 */
:deep(.el-tag__close) {
  font-size: 12px;
  margin-left: 4px;
  color: #409eff;
  opacity: 0.7;
}

:deep(.el-tag__close:hover) {
  opacity: 1;
}

/* 输入框部分样式 */
:deep(.el-input__inner) {
  border: none;
  padding: 0;
  margin: 0;
  outline: none;
  box-shadow: none;
  flex: 1;
  min-width: 80px;
  height: 24px;
  line-height: 24px;
}

/* 去除输入框聚焦时的边框 */
:deep(.el-input__inner:focus) {
  border: none;
  box-shadow: none;
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
  .photo-management {
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

  .photo-grid {
    grid-template-columns: 1fr; /* 移动端单列布局 */
    padding: 5px;
  }

  .photo-card {
    margin: 5px 0;
  }

  .photo-image {
    height: 200px; /* 移动端稍微大一些 */
  }

  .photo-details-container {
    flex-direction: column;
  }

  .photo-details-left,
  .photo-details-right {
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
    width: 95% !important;
    margin-top: 2vh;
  }

  .details-dialog {
    width: 98% !important;
  }

  .photo-details-container {
    flex-direction: column;
    padding: 8px 0;
  }

  .photo-details-left,
  .photo-details-right {
    width: 100%;
    min-width: auto;
  }

  .photo-preview-img {
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
  .photo-management {
    padding: 8px;
  }

  .photo-image {
    height: 160px;
  }

  .photo-title {
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

  .photo-preview-img {
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
  color: #606266;
  font-size: 14px;
  margin-left: 10px;
}

.no-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 20px;
}

.icon-zoomin{
  margin-right: 5px;
  font-size: 18px;
}

</style>