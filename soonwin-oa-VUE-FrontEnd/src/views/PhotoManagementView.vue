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
            <el-button
              v-if="!isMultiSelectMode"
              type="primary"
              @click="showUploadDialog = true"
            >
              <el-icon><UploadFilled /></el-icon>
              上传照片
            </el-button>

            <el-button
              v-if="isAdmin && !isMultiSelectMode"
              @click="showPhotoLogs"
            >
              <el-icon><Document /></el-icon>
              查看日志
            </el-button>

            <!-- 多选模式按钮组 -->
            <div v-else class="multi-select-buttons">
              <el-button @click="batchDeletePhotos" :disabled="selectedPhotoIds.length === 0">
                <el-icon><Delete /></el-icon>
                批量删除 ({{ selectedPhotoIds.length }})
              </el-button>
              <el-button @click="toggleSelectAll">
                {{ selectedPhotoIds.length === photos.length ? '取消全选' : '全选' }}
              </el-button>
              <el-button @click="toggleMultiSelectMode">
                取消
              </el-button>
            </div>

            <!-- 非多选模式下的多选按钮 -->
            <el-button
              v-if="!isMultiSelectMode && photos.length > 0"
              @click="toggleMultiSelectMode"
            >
              <el-icon><CircleCheck /></el-icon>
              多选
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

        :class="{ 'selected': isPhotoSelected(photo.id) }"

        @click="isMultiSelectMode ? selectPhoto(photo.id) : viewPhotoDetails(photo)"

      >

        <!-- 多选模式下的选择框 -->

        <div

          v-if="isMultiSelectMode"

          class="select-checkbox"

          @click.stop="selectPhoto(photo.id)"

        >

          <el-checkbox

            :model-value="isPhotoSelected(photo.id)"

            @change="selectPhoto(photo.id)"

          />

        </div>



        <!-- 删除按钮 - 右上角圆形X按钮 -->

        <div

          v-if="!isMultiSelectMode"

          class="delete-btn"

          @click.stop="deletePhoto(photo.id)"

        >

          <el-icon style="margin-right: 0;"><Delete /></el-icon>

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
            :file-list="fileList"
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

        <!-- 匹配文件按钮 -->
        <el-form-item v-if="fileList.length > 0">
          <el-button
            @click="showJsonInputDialog = true"
            type="info"
            :icon="Search"
          >
            匹配文件
          </el-button>
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
            </div>
            <div v-else>
              <label class="detail-label">备注:</label>
              <el-input
                v-model="editRemark"
                type="textarea"
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
      :before-close="handleJsonInputDialogClose"
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

        <!-- 匹配结果展示 -->
        <div v-if="isMatched" class="match-results-section" style="margin-top: 20px;">
          <h4>匹配结果：</h4>

          <!-- 已匹配文件 -->
          <div v-if="matchedFiles.length > 0" class="matched-files-section">
            <h5 style="color: #67c23a;">已匹配文件 ({{ matchedFiles.length }}个)：</h5>
            <el-table :data="matchedFiles" style="width: 100%; margin-top: 8px;">
              <el-table-column prop="file.name" label="文件名" width="200"></el-table-column>
              <el-table-column prop="data.title" label="标题" width="150"></el-table-column>
              <el-table-column prop="data.machineId" label="关联机器" width="150"></el-table-column>
              <el-table-column prop="data.tags" label="标签" width="150"></el-table-column>
              <el-table-column prop="data.remark" label="备注" show-overflow-tooltip></el-table-column>
            </el-table>
          </div>

          <!-- 未匹配文件 -->
          <div v-if="unmatchedFiles.length > 0" class="unmatched-files-section" style="margin-top: 15px;">
            <h5 style="color: #e6a23c;">未匹配文件 ({{ unmatchedFiles.length }}个)：</h5>
            <div style="background: #fdf6ec; border: 1px solid #faecd8; border-radius: 4px; padding: 10px; margin-top: 8px;">
              <span v-for="(file, index) in unmatchedFiles" :key="index" class="unmatched-file">
                {{ file }}{{ index < unmatchedFiles.length - 1 ? ', ' : '' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showJsonInputDialog = false">取消</el-button>
          <el-button
            type="warning"
            @click="matchJsonToFiles"
          >
            匹配文件
          </el-button>
          <el-button
            :disabled="!isMatched"
            type="primary"
            @click="uploadMatchedFiles"
            :loading="uploading"
          >
            上传匹配文件
          </el-button>
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
import { UploadFilled, Delete, ZoomIn, Document, RefreshLeft, Search, CircleCheck } from '@element-plus/icons-vue';
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
  file: null as File | File[] | null, // 支持单/多文件
});

const uploadFormTags = ref<string[]>([]);
const inputValueString = ref('');
const showJsonInputDialog = ref(false);
const jsonInputText = ref('');
// JSON匹配相关状态
const matchedFiles = ref<any[]>([]);
const unmatchedFiles = ref<string[]>([]);
const isMatched = ref(false); // 是否已匹配成功

// 多选相关状态
const isMultiSelectMode = ref(false); // 是否处于多选模式
const selectedPhotoIds = ref<number[]>([]); // 选中的照片ID列表

// 监听uploadFormTags变化并更新uploadForm中的tags字段
watch(uploadFormTags, (newTags) => {
  uploadForm.value.tags = newTags.join(',');
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
const fileList = ref<any[]>([]); // Element Upload组件的文件列表
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

// 表单验证规则（适配多文件）
const uploadRules = {
  title: [{ required: true, message: '请输入照片标题', trigger: 'blur' }],
  file: [{
    required: true,
    validator: (rule: any, value: any, callback: any) => {
      if (fileList.value.length === 0) {
        callback(new Error('请选择照片文件'));
      } else {
        callback();
      }
    },
    trigger: 'change'
  }]
};

// 获取router
const router = useRouter();

// API基础URL
const apiBaseUrl = computed(() => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
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
const showPhotoDetails = (photo: any) => {
  viewPhotoDetails(photo);
};

// 图片加载错误处理
const onImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  if (!target.src.includes("default-image") && !target.src.startsWith("data:image")) {
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

// 文件选择处理（核心修复：正确更新文件列表）
const handleFileChange = (file: any, newFileList: any[]) => {
  // 检查文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
  let isValid = true;

  // 校验当前文件
  if (!allowedTypes.includes(file.raw.type)) {
    ElMessage.error(`文件 ${file.name} 格式错误，仅支持png/jpg/jpeg/webp格式`);
    isValid = false;
  }

  // 检查文件大小
  const maxSize = 50 * 1024 * 1024; // 50MB
  if (file.raw.size > maxSize) {
    ElMessage.error(`文件 ${file.name} 大小超过50MB限制`);
    isValid = false;
  }

  // 过滤非法文件并更新列表
  if (isValid) {
    fileList.value = newFileList; // 使用组件返回的完整列表
  } else {
    // 过滤掉当前非法文件
    fileList.value = newFileList.filter(item => item.uid !== file.uid);
  }

  // 更新表单中的文件（转为原生File数组）
  uploadForm.value.file = fileList.value.map(item => item.raw);

  // 自动填充标题（仅第一个文件）
  if (!uploadForm.value.title && fileList.value.length > 0) {
    const fileName = fileList.value[0].raw.name;
    const lastDotIndex = fileName.lastIndexOf('.');
    uploadForm.value.title = lastDotIndex > 0
      ? fileName.substring(0, lastDotIndex)
      : fileName;
  }
};

// 文件移除处理
const handleFileRemove = (file: any, newFileList: any[]) => {
  // 同步更新文件列表
  fileList.value = newFileList;
  // 同步更新表单文件
  uploadForm.value.file = fileList.value.map(item => item.raw);
};

// 关闭上传对话框
const handleUploadDialogClose = (done: () => void) => {
  if (uploading.value) {
    return;
  }
  done();
};

// 提交上传（逐个上传，等待后端支持批量接口）
const submitUpload = async () => {
  // 表单验证
  if (uploadFormRef.value) {
    const valid = await uploadFormRef.value.validate().catch(() => false);
    if (!valid) {
      return;
    }
  }

  if (fileList.value.length === 0) {
    ElMessage.error('请选择照片文件');
    return;
  }

  uploading.value = true;
  uploadProgress.value = 0;
  let successCount = 0;
  let errorCount = 0;

  try {
    // 从token解析上传者
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

    // 批量上传每个文件
    for (let i = 0; i < fileList.value.length; i++) {
      const fileItem = fileList.value[i];
      try {
        const formData = new FormData();
        formData.append('file', fileItem.raw);
        formData.append('title', uploadForm.value.title || fileItem.name.replace(/\.\w+$/, ''));
        formData.append('tags', uploadForm.value.tags);
        formData.append('machine_id', uploadForm.value.machineId);
        formData.append('remark', uploadForm.value.remark);
        formData.append('uploader', uploader);

        await createPhoto(formData, (progressEvent) => {
          if (progressEvent.total) {
            const fileProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            uploadProgress.value = Math.round(((i * 100) + fileProgress) / fileList.value.length);
          }
        });
        successCount++;
      } catch (uploadError) {
        console.error(`上传文件 ${fileItem.name} 失败:`, uploadError);
        errorCount++;
      }
    }

    ElMessage.success(`上传完成: ${successCount} 个成功, ${errorCount} 个失败`);
    showUploadDialog.value = false;
    resetUploadForm();
    fetchPhotos();
  } catch (error) {
    console.error('上传失败:', error);
    ElMessage.error('上传过程中发生错误');
  } finally {
    uploading.value = false;
    uploadProgress.value = 0;
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
  uploadFormTags.value = [];
  uploadProgress.value = 0;
};

// JSON匹配多文件相关函数（核心修复：换行符兼容）
const matchJsonToFiles = () => {
  try {
    // 解析JSON输入 - 核心优化：兼容制表符和多个空格分隔
    const inputText = jsonInputText.value.trim();
    if (!inputText) {
      ElMessage.error('请输入匹配信息');
      return;
    }

    // 第一步：将所有连续空白（制表符、多个空格、全角空格）统一替换为单个制表符
    const normalizedText = inputText.replace(/[\s\u00A0]+/g, '\t');
    // 第二步：按换行符分割行（兼容\r\n和\n）
    let lines = normalizedText.split(/\r?\n/).filter(line => line.trim() !== '');

    // 核心修复：处理无换行符的场景（所有内容在一行）
    if (lines.length === 1) {
      const allFields = lines[0].split('\t').map(field => field.trim()).filter(field => field);
      // 检查是否是表头+多行数据混在一起的情况（表头5个字段，总字段数>5且能被5整除）
      if (allFields.length >= 5 && allFields.slice(0,5).join(',') === '照片文件名,照片标题,关联机器,标签,备注') {
        // 分离表头和数据
        const headerFields = allFields.slice(0,5); // 前5个是表头
        const dataFields = allFields.slice(5);     // 后面的是数据

        // 按每5个字段为一行拆分数据
        const newLines = [headerFields.join('\t')]; // 重新构建表头行
        for (let i = 0; i < dataFields.length; i += 5) {
          const rowFields = dataFields.slice(i, i+5);
          if (rowFields.length >= 1) { // 至少有文件名字段
            newLines.push(rowFields.join('\t'));
          }
        }
        lines = newLines; // 使用重构后的行数据
      }
    }

    if (lines.length === 0) {
      ElMessage.error('请输入匹配信息');
      return;
    }

    // 解析表头
    const headers = lines[0].split('\t').map(header => header.trim());

    // 校验表头（增加容错性，处理大小写和空白问题）
    if (headers.length < 5 ||
        headers[0].toLowerCase().trim() !== '照片文件名' ||
        headers[1].toLowerCase().trim() !== '照片标题' ||
        headers[2].toLowerCase().trim() !== '关联机器' ||
        headers[3].toLowerCase().trim() !== '标签' ||
        headers[4].toLowerCase().trim() !== '备注') {
      ElMessage.error('表头格式不正确，请使用：照片文件名\t照片标题\t关联机器\t标签\t备注');
      return;
    }

    // 解析数据行
    const dataRows = lines.slice(1).map(line => {
      const fields = line.split('\t').map(field => field.trim());
      // 确保至少有文件名字段，其他字段可选（补空）
      if (fields.length >= 1 && fields[0]) {
        return {
          filename: fields[0] || '',
          title: fields[1] || '',
          machineId: fields[2] || '',
          tags: fields[3] || '',
          remark: fields[4] || ''
        };
      }
      return null;
    }).filter(row => row !== null);

    // 匹配文件与数据
    const matchedFilesTemp = [];
    const unmatchedFilesTemp = [];

    fileList.value.forEach(fileObj => {
      const originalFilename = fileObj.name;
      // 安全地提取文件名（去掉扩展名）
      const lastDotIndex = originalFilename.lastIndexOf('.');
      let baseFilename;
      if (lastDotIndex > 0) {
        baseFilename = originalFilename.substring(0, lastDotIndex);
      } else {
        // 如果没有扩展名，使用完整文件名
        baseFilename = originalFilename;
      }

      // 统一小写进行匹配，增加匹配的健壮性
      const targetFilename = baseFilename.toLowerCase().trim();
      const matchedData = dataRows.find(data =>
        data.filename.toLowerCase().trim() === targetFilename
      );

      if (matchedData) {
        matchedFilesTemp.push({
          file: fileObj,
          data: matchedData
        });
      } else {
        unmatchedFilesTemp.push(originalFilename);
      }
    });

    // 更新匹配结果
    matchedFiles.value = matchedFilesTemp;
    unmatchedFiles.value = unmatchedFilesTemp;
    isMatched.value = matchedFilesTemp.length > 0;

    // 提示信息
    if (unmatchedFilesTemp.length > 0) {
      ElMessage.warning(`以下文件未找到匹配数据: ${unmatchedFilesTemp.join(', ')}`);
    }

    if (matchedFilesTemp.length === 0) {
      ElMessage.warning('没有找到匹配的文件');
      isMatched.value = false;
    } else {
      ElMessage.success(`匹配成功: ${matchedFilesTemp.length} 个文件已匹配`);
    }
  } catch (error) {
    console.error('匹配JSON数据失败:', error);
    ElMessage.error('解析JSON数据失败，请检查格式');
    isMatched.value = false;
  }
};

// 重置匹配状态
const resetMatchState = () => {
  jsonInputText.value = '';
  matchedFiles.value = [];
  unmatchedFiles.value = [];
  isMatched.value = false;
};

// 处理JSON匹配对话框关闭
const handleJsonInputDialogClose = (done: () => void) => {
  if (isMatched.value && matchedFiles.value.length > 0) {
    ElMessageBox.confirm('您有已匹配但未上传的文件，确定要关闭吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      // 用户确认关闭，重置状态
      resetMatchState();
      done();
    }).catch(() => {
      // 用户取消关闭
    });
  } else {
    // 没有匹配的文件，直接关闭
    resetMatchState();
    done();
  }
};

// 上传已匹配的文件（逐个上传，等待后端支持批量接口）
const uploadMatchedFiles = async () => {
  if (matchedFiles.value.length === 0) {
    ElMessage.warning('没有匹配的文件可上传');
    return;
  }

  uploading.value = true;
  let successCount = 0;
  let errorCount = 0;

  try {
    // 逐个上传匹配的文件
    for (let i = 0; i < matchedFiles.value.length; i++) {
      const matchedFile = matchedFiles.value[i];
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
          const overallProgress = Math.round(((i * 100) + fileProgress) / matchedFiles.value.length);
          uploadProgress.value = overallProgress;
        });
        successCount++;
      } catch (uploadError) {
        console.error(`上传文件 ${matchedFile.data.title} 失败:`, uploadError);
        errorCount++;
      }
    }

    ElMessage.success(`批量上传完成: ${successCount} 个成功, ${errorCount} 个失败`);
    showJsonInputDialog.value = false;
    showUploadDialog.value = false; // 同时关闭主上传对话框
    resetUploadForm();
    fetchPhotos(); // 刷新列表
  } catch (error) {
    console.error('批量上传失败:', error);
    ElMessage.error(`批量上传失败: ${(error as Error).message}`);
  } finally {
    uploading.value = false;
    uploadProgress.value = 0;
    // 重置匹配状态
    resetMatchState();
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
    fetchPhotos();
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
  editTitle.value = photo?.title || '';
  editRemark.value = photo?.remark || '';
  const tagsString = photo?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
  isEditingAll.value = false;
  editTagsInput.value = '';
  showDetailsDialog.value = true;
};

// 添加标签
const addTagFromInput = () => {
  if (editTagsInput.value.trim()) {
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
    window.open(originalImageUrl, '_blank');
  }
};

// 处理对话框关闭
const handleDialogClose = () => {
  if (isEditingAll.value) {
    cancelEditingAll();
  }
  showDetailsDialog.value = false;
};

// 内容搜索
const searchContent = async () => {
  currentPage.value = 1;
  showResultCount.value = !!searchQuery.value;
  await fetchPhotos();
};

// 机器搜索
const searchByMachine = async () => {
  currentPage.value = 1;
  showResultCount.value = !!selectedMachine.value;
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
  showResultCount.value = !!searchQuery.value || !!selectedMachine.value;
  fetchPhotos();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  showResultCount.value = !!searchQuery.value || !!selectedMachine.value;
  fetchPhotos();
};

// 日志跳转处理
const handleLogJump = async (id: number) => {
  console.log(`跳转到照片ID: ${id}`);

  const currentPhoto = photos.value.find(photo => photo.id === id);
  if (currentPhoto) {
    viewPhotoDetails(currentPhoto);
    return;
  }

  try {
    const response = await request.get(`/api/photos/${id}`);
    if (response && response.code === 200) {
      viewPhotoDetails(response.data);
    } else {
      ElMessage.error('加载照片详情失败');
    }
  } catch (error: any) {
    console.error('加载照片详情失败:', error);
    if (error.response && error.response.data && error.response.data.msg?.includes('404')) {
      ElMessage.error('该照片已删除或不存在');
    } else {
      ElMessage.error('加载照片详情失败');
    }
  }
};

// 显示照片日志
const showPhotoLogs = () => {
  if (!isAdmin.value) {
    ElMessage.error('您没有权限查看日志');
    return;
  }
  logDialogVisible.value = false;
  nextTick(() => {
    logDialogVisible.value = true;
  });
};

// 切换多选模式
const toggleMultiSelectMode = () => {
  isMultiSelectMode.value = !isMultiSelectMode.value;
  if (!isMultiSelectMode.value) {
    // 退出多选模式时清空选中项
    selectedPhotoIds.value = [];
  }
};

// 选择单个照片
const selectPhoto = (photoId: number) => {
  const index = selectedPhotoIds.value.indexOf(photoId);
  if (index > -1) {
    // 已选中，取消选择
    selectedPhotoIds.value.splice(index, 1);
  } else {
    // 未选中，添加选择
    selectedPhotoIds.value.push(photoId);
  }
};

// 全选/取消全选
const toggleSelectAll = () => {
  if (selectedPhotoIds.value.length === photos.value.length) {
    // 当前已全选，取消全选
    selectedPhotoIds.value = [];
  } else {
    // 未全选，进行全选
    selectedPhotoIds.value = photos.value.map(photo => photo.id);
  }
};

// 批量删除选中的照片
const batchDeletePhotos = async () => {
  if (selectedPhotoIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的照片');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedPhotoIds.value.length} 张照片吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 批量删除照片
    let successCount = 0;
    let errorCount = 0;

    for (const photoId of selectedPhotoIds.value) {
      try {
        await deletePhotoAPI(photoId);
        successCount++;
      } catch (error) {
        console.error(`删除照片 ${photoId} 失败:`, error);
        errorCount++;
      }
    }

    if (errorCount > 0) {
      ElMessage.warning(`批量删除完成: ${successCount} 个成功, ${errorCount} 个失败`);
    } else {
      ElMessage.success(`成功删除 ${successCount} 张照片`);
    }

    // 重置选择状态并刷新列表
    selectedPhotoIds.value = [];
    isMultiSelectMode.value = false;
    fetchPhotos();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除照片失败:', error);
      ElMessage.error('批量删除失败');
    }
  }
};

// 检查照片是否被选中
const isPhotoSelected = (photoId: number) => {
  return selectedPhotoIds.value.includes(photoId);
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

/* 多选模式按钮样式 */
.multi-select-buttons {
  display: flex;
  gap: 8px;
}

/* 照片卡片多选样式 */
.photo-card.selected {
  border: 2px solid #409eff; /* 选中时边框为蓝色 */
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.photo-card .select-checkbox {
  position: absolute;
  z-index: 10;
  top: 10px;
  right: 10px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  border-radius: 50%;
}

.photo-card .select-checkbox .el-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-checkbox{
  width: 32px;
  height: 32px;
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
  position: relative;
  width: 100%;
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
  color: #f56c6c;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
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
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
  cursor: pointer;
}

.photo-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-title {
  font-size: 14px;
  font-weight: bold;
  max-width: 80%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.photo-upload-time {
  font-size: 11px;
  color: #909399;
}

.card-tags-container {
  white-space: nowrap;
  overflow: hidden;
  max-width: 80%;
  text-overflow: ellipsis;
}

.card-tags {
  display: inline-block;
  background-color: #bedbfc;
  color: #013b75;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 11px;
  margin-right: 5px;
  margin-top: 6px;
}

.photo-resolution {
  position: absolute;
  bottom: 10px;
  right: 10px;
  color: white;
  font-size: 11px;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  z-index: 5;
}

.photo-info {
  padding: 12px;
}

.photo-info h4 {
  margin: 0 0 10px 0;
  font-size: 15px;
  font-weight: 600;
}

.machine {
  color: #606266;
  font-size: 13px;
  margin: 5px 0;
  word-break: break-word;
}

.upload-time,
.uploader {
  color: #909399;
  font-size: 11px;
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

.photo-details-container {
  display: flex;
  gap: 24px;
  padding: 16px 0;
  flex-direction: column;
}

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
  right: 0;
  padding: 8px 12px;
  background: linear-gradient(to top, rgba(0,0,0,0.3), transparent);
}

.preview-actions .el-button {
  color: white;
}

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

:deep(.el-input-tag__content) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  width: 100%;
}

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

:deep(.el-tag__close) {
  font-size: 12px;
  margin-left: 4px;
  color: #409eff;
  opacity: 0.7;
}

:deep(.el-tag__close:hover) {
  opacity: 1;
}

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

:deep(.el-input__inner:focus) {
  border: none;
  box-shadow: none;
}

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

.machine-value {
  color: #409eff;
  font-weight: 500;
}

.detail-actions {
  margin-top: 24px;
  text-align: right;
}

.edit-actions-group {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

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
    grid-template-columns: 1fr;
    padding: 5px;
  }

  .photo-card {
    margin: 5px 0;
  }

  .photo-image {
    height: 200px;
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

  .mobile-dialog {
    width: 95% !important;
    margin-top: 2vh;
  }

  .details-dialog {
    width: 98% !important;
  }

  .photo-preview-img {
    max-height: 300px;
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

  .mobile-dialog {
    width: 98% !important;
    margin-top: 5vh;
  }

  .photo-preview-img {
    max-height: 200px;
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

/* 多选模式按钮样式 */
.multi-select-buttons {
  display: flex;
  gap: 8px;
}

/* 照片卡片多选样式 */
.photo-card.selected {
  border: 2px solid #409eff; /* 选中时边框为蓝色 */
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.photo-card .select-checkbox {
  position: absolute;
  z-index: 10;
  top: 10px;
  right: 10px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.photo-card .select-checkbox .el-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-icon{
  margin-right: 5px;
}
</style>