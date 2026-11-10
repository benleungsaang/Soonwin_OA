<template>
  <div class="video-management">
    <CommonHeader title="视频管理" />
    <div class="header">
      <div class="title-with-count">
        <h2>
          <template v-if="showingRecycleBin">
            回收站
            <span v-if="showingRecycleBin" class="recycle-statistics">
              ({{ totalVideos }} 个文件, {{ formatFileSize(totalDeletedSize) }})
            </span>
          </template>
          <template v-else>视频管理</template>
        </h2>
        <div v-if="showResultCount && !showingRecycleBin" class="result-count-container">
          <span class="result-count">
            找到 {{ totalVideos }} 条视频
          </span>
          <el-icon
            @click="clearSearch"
            class="result-refresh-btn"
          ><RefreshLeft /></el-icon>
        </div>
      </div>
      <div class="header-buttons">

        <el-button
          v-if="!showingRecycleBin && !isMultiSelectMode"
          type="primary"
          @click="showUploadDialog = true"
        >
          <el-icon><UploadFilled /></el-icon>
          上传视频
        </el-button>

        <el-button
          v-if="!showingRecycleBin && !isMultiSelectMode"
          type="success"
          @click="showBatchUploadDialog = true"
        >
          <el-icon><UploadFilled /></el-icon>
          批量上传
        </el-button>

        <!-- 普通视频列表多选模式按钮组 -->
        <div v-if="!showingRecycleBin && isMultiSelectMode" class="multi-select-buttons">
          <el-button @click="toggleSelectAllNormal">
            {{ selectedNormalVideos.length === videos.length ? '取消全选' : '全选' }}
          </el-button>
          <el-button
          type="danger"
          @click="batchDeleteNormalVideos"
          :disabled="selectedNormalVideos.length === 0">
            <el-icon><Delete /></el-icon>
            批量删除 ({{ selectedNormalVideos.length }})
          </el-button>
          <el-button
          type="warning"
          @click="toggleMultiSelectMode"
          >
            取消
          </el-button>
        </div>

        <!-- 非多选模式且非回收站模式下的多选按钮 -->
        <el-button
          v-if="!showingRecycleBin && !isMultiSelectMode && videos.length > 0"
          @click="toggleMultiSelectMode"
          type="success"
        >
          <el-icon><CircleCheck /></el-icon>
          多选
        </el-button>

        <el-button
          v-if="!showingRecycleBin && isAdmin"
        @click="showVideoLogs" >
          <el-icon><Document /></el-icon>
          查看日志
        </el-button>
        <el-button
          v-if="showingRecycleBin"
          type="primary"
          @click="confirmRestore"
          style="margin-right: 10px;"
        >
          <el-icon><Refresh /></el-icon>
          恢复 ({{ selectedVideos.length }})
        </el-button>
        <el-button
          v-if="showingRecycleBin"
          type="danger"
          @click="confirmPhysicalDelete"
          style="margin-right: 10px;"
        >
          <el-icon><Delete /></el-icon>
          彻底删除 ({{ selectedVideos.length }})
        </el-button>
        <el-button
          v-if="!showingRecycleBin && isAdmin"
          @click="enterRecycleBin"
          style="margin-right: 10px;"
        >
          <el-icon><Delete /></el-icon>
          回收站
        </el-button>
        <el-button
          v-if="showingRecycleBin && isAdmin"
          @click="toggleSelectAll"
          style="margin-right: 10px;"
        >
          <el-icon><CircleCheck /></el-icon>
          {{ selectedVideos.length === videos.length ? '取消' : '全选' }}
        </el-button>
        <el-button
          v-if="showingRecycleBin"
          @click="exitRecycleBin"
          style="margin-right: 10px;"
        >
          <el-icon><Back /></el-icon>
          返回
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
          :key="machine.id"
          :label="`${machine.model} (${machine.original_model})`"
          :value="machine.id"
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
        :class="{
          // 'selected': showingRecycleBin && selectedVideos.includes(video.id),
          'selected': !showingRecycleBin && isMultiSelectMode && isNormalVideoSelected(video.id)
        }"
        :data-video-id="video.id"
        @click="showingRecycleBin ? toggleVideoSelection(video) :
                 isMultiSelectMode ? selectNormalVideo(video.id) :
                 viewVideoDetails(video)"
      >
        <!-- 多选复选框（在普通视频列表的多选模式下显示） -->
        <div
          v-if="!showingRecycleBin && isMultiSelectMode"
          class="select-checkbox"
          @click.stop="selectNormalVideo(video.id)"
        >
          <el-checkbox
            :model-value="isNormalVideoSelected(video.id)"
            @click.stop="selectNormalVideo(video.id)"
          />
        </div>

        <!-- 多选复选框（仅在回收站模式下显示） -->
        <div
          v-else-if="showingRecycleBin"
          class="select-checkbox"
          @click.stop="toggleVideoSelection(video)"
        >
          <el-checkbox
            :model-value="selectedVideos.includes(video.id)"
            @click.stop="toggleVideoSelection(video)"
          />
        </div>

        <!-- 卡片菜单（仅在非多选模式且非回收站模式下显示） -->
        <div v-else-if="!showingRecycleBin && !isMultiSelectMode" class="delete-btn" @click.stop>
          <el-dropdown trigger="click" @command="handleVideoMenuCommand($event, video)">
            <el-button circle text aria-label="视频操作菜单">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="delete">
                  <el-icon><Delete /></el-icon> 删除
                </el-dropdown-item>
                <el-dropdown-item
                  v-if="isAdmin"
                  command="compress"
                  :disabled="Boolean(video.compressed_path) || isVideoProcessing(video)"
                >
                  <el-icon><VideoPlay /></el-icon>
                  {{ video.compressed_path ? '已压缩' : isVideoProcessing(video) ? '压缩中' : '压缩' }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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

          <div v-if="isVideoProcessing(video)" class="video-processing-overlay">
            <el-icon class="video-processing-icon"><Refresh /></el-icon>
            <span>转码中...</span>
          </div>

          <!-- 右下角时长和文件大小 -->
          <div class="video-info-bottom">
            <span v-if="video.duration" class="video-duration">{{ formatDuration(video.duration) }}</span>
            <span v-if="video.file_size" class="video-file-size">{{ formatFileSize(video.file_size) }}</span>
          </div>
        </div>

        <div class="video-info">
          <div class="video-title">{{ video.title }}</div>
          <div class="video-upload-time">
            <template v-if="!showingRecycleBin">
              <span class="time-label">上传:</span> {{ video.upload_time }}
            </template>
            <template v-else>
              <div class="recycle-info">
                <div class="info-item">
                  <span class="time-label">上传:</span> {{ video.upload_time }}
                </div>
                <div class="info-item">
                  <span class="time-label">上传人:</span> {{ video.uploader }}
                </div>
                <div class="info-item">
                  <span class="time-label">删除:</span> {{ video.delete_time || 'N/A' }}
                </div>
                <div class="info-item">
                  <span class="time-label">删除人:</span> {{ video.delete_operator || 'N/A' }}
                </div>
              </div>
            </template>
          </div>
          <div class="card-tags-container" v-if="video.tags && !showingRecycleBin">
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
    <el-dialog v-model="showUploadDialog" title="上传视频" width="min(940px, 96vw)" :before-close="handleUploadDialogClose" class="video-upload-v2" destroy-on-close>
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-position="top" class="vu-form">
        <div class="vu-layout">
          <section class="vu-card"><h2>选择视频文件</h2>
            <el-form-item prop="file" class="vu-file-field"><el-upload ref="uploadRef" drag :auto-upload="false" :on-change="handleFileChange" :file-list="fileList" :limit="1" :on-remove="handleFileRemove" accept=".mp4,.avi,.mov,.mkv,.wmv" class="vu-upload">
              <el-icon class="vu-drop-icon"><UploadFilled /></el-icon><strong>拖放文件到此处，或点击选择</strong><span class="vu-muted">MP4 / AVI / MOV / MKV / WMV</span>
            </el-upload></el-form-item>
            <p class="vu-hint">{{ compressVideoEnabled ? '压缩时按现有上传规则处理' : '不压缩时文件不超过 500 MB' }}</p>
            <div class="vu-option"><el-checkbox v-model="compressVideoEnabled">压缩视频（默认压缩）</el-checkbox><el-checkbox v-model="watermarkEnabled">添加 Logo 水印</el-checkbox>
              <div v-if="watermarkEnabled" class="vu-watermark"><div class="vu-label">选择水印位置</div><div class="vu-positions"><button v-for="option in watermarkPositionOptions" :key="option.value" type="button" class="vu-position" :class="{ selected: watermarkPosition === option.value }" :aria-pressed="watermarkPosition === option.value" @click="watermarkPosition = option.value"><img :src="`${apiBaseUrl}/assets/Media/Videos/water-mark/${option.image}`" :alt="`水印位置：${option.label}`" /><span>{{ option.label }}</span></button></div></div>
            </div>
          </section>
          <section class="vu-card"><h2>内容信息</h2>
            <el-form-item label="视频标题" prop="title"><el-input v-model="uploadForm.title" placeholder="请输入视频标题" /></el-form-item>
            <el-form-item label="关联机器" prop="machineId"><el-select v-model="uploadForm.machineId" placeholder="选择关联机器（可选）" clearable><el-option v-for="machine in machineList" :key="machine.id" :label="`${machine.model} (${machine.original_model})`" :value="machine.id" /></el-select></el-form-item>
            <el-form-item label="标签" prop="tags"><el-input-tag v-model="uploadFormTags" placeholder="多个标签用逗号分隔" delimiter="," /></el-form-item>
            <el-form-item label="备注"><el-input v-model="uploadForm.remark" type="textarea" :rows="4" placeholder="填写备注信息（可选）" /></el-form-item>
            <div class="vu-divider"></div><p class="vu-muted">标题和文件为必填项，其余字段可选。</p>
          </section>
        </div>
        <el-progress v-if="uploading" :percentage="uploadProgress" class="vu-progress" />
        <div class="vu-footer"><span class="vu-muted">{{ fileList.length ? `已选择 ${fileList.length} 个文件` : '尚未选择文件' }}</span><div class="vu-actions"><button type="button" class="vu-btn" :disabled="uploading" @click="showUploadDialog = false">取消</button><button type="button" class="vu-btn vu-primary" :disabled="uploading" @click="submitUpload">{{ uploading ? '上传中…' : '上传视频' }}</button></div></div>
      </el-form>
    </el-dialog>

    <!-- 视频详情对话框 -->
    <el-dialog v-model="showDetailsDialog" width="min(1260px, 96vw)" :before-close="handleDialogClose" class="video-detail-v2-dialog" destroy-on-close>
      <main v-if="selectedVideo" class="vd-shell">
        <div class="vd-toolbar">
          <button v-if="!isEditingAll" class="vd-btn" @click="startEditingAll">编辑信息</button>
          <template v-else><button class="vd-btn" :disabled="savingAll" @click="cancelEditingAll">取消</button><button class="vd-btn vd-primary" :disabled="savingAll" @click="saveAll">{{ savingAll ? '保存中…' : '保存' }}</button></template>
        </div>
        <div class="vd-layout">
          <section class="vd-preview">
            <div class="vd-eyebrow">VIDEO PREVIEW / 视频预览</div>
            <div class="vd-stage"><div class="vd-video-wrap">
              <video :key="selectedVideo.id" :src="currentVideoSrc" :poster="selectedVideo.thumbnail_path ? `${apiBaseUrl}/assets/Media/Videos/${selectedVideo.thumbnail_path}` : undefined" controls preload="metadata" playsinline class="video-preview" @error="onVideoError">浏览器不支持视频播放。</video>
            </div></div>
            <div class="vd-filefoot"><div><div class="vd-filename">{{ videoFilename }}</div><div class="vd-sub">{{ videoTechnicalInfo }}</div></div><button v-if="selectedVideo.original_path" class="vd-btn" @click="downloadVideo">↧ 下载视频</button></div>
          </section>
          <aside class="vd-right">
            <section class="vd-panel vd-content"><h2>内容信息</h2>
              <div class="vd-field"><div class="vd-label">标题</div><div v-if="!isEditingAll" class="vd-value">{{ selectedVideo.title || '无标题' }}</div><input v-else v-model="editTitle" class="vd-editor" maxlength="255" aria-label="标题" /></div>
              <div v-if="selectedVideo.machine_info" class="vd-field"><div class="vd-label">关联机器</div><div class="vd-value">{{ selectedVideo.machine_info.model }} ( {{ selectedVideo.machine_info.original_model }} )</div></div>
              <div class="vd-field"><div class="vd-label">标签</div><div v-if="!isEditingAll" class="vd-value">{{ selectedVideo.tags || '无标签' }}</div><input v-else v-model="editTagsInput" class="vd-editor" placeholder="多个标签用逗号分隔" aria-label="标签" /></div>
              <div class="vd-field"><div class="vd-label">备注</div><div v-if="!isEditingAll" class="vd-value vd-note">{{ selectedVideo.remark || '无备注' }}</div><textarea v-else v-model="editRemark" class="vd-editor vd-note-editor" aria-label="备注"></textarea></div>
            </section>
            <section class="vd-panel vd-record"><h2>文件记录</h2>
              <div class="vd-avatarrow"><div class="vd-avatar">{{ (selectedVideo.uploader || '未').slice(0, 1) }}</div><div><div class="vd-person">{{ selectedVideo.uploader || '未知' }}</div><div class="vd-sub">上传人</div></div></div>
              <div class="vd-recorditem"><div class="vd-label">上传时间</div><div class="vd-value">{{ formatDate(selectedVideo.upload_time) }}</div></div>
              <div class="vd-recorditem"><div class="vd-label">视频详情</div><div class="vd-value">{{ videoTechnicalInfo }}</div></div>
            </section>
          </aside>
        </div>
      </main>
    </el-dialog>

    <!-- 引入通用日志对话框组件 -->
    <CommonLogDialog
      v-model="logDialogVisible"
      log-type="video"
      :handle-jump="handleLogJump"
    />

    <!-- 批量上传视频对话框 -->
    <el-dialog
      v-model="showBatchUploadDialog"
      title="批量上传视频"
      width="80%"
      :before-close="handleBatchUploadDialogClose"
      class="mobile-dialog batch-upload-dialog"
    >
      <BatchVideoUpload
        ref="batchUploadComponent"
        @upload-complete="handleBatchUploadComplete"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled, Delete, VideoPlay, Back, CircleCheck, Refresh, Document, RefreshLeft, MoreFilled } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import CommonHeader from '@/components/CommonHeader.vue';
import CommonLogDialog from '@/components/CommonLogDialog.vue';
import BatchVideoUpload from '@/components/BatchVideoUpload.vue';
import { uploadFile } from '@/utils/upload';
import { getCurrentUserRole } from '@/utils/authUtils';
import request, {
  getMachinesForVideos,
  createVideo,
  updateVideo,
  deleteVideo as deleteVideoAPI,
  compressVideo as compressVideoAPI,
  getDeletedVideos,
  physicalDeleteVideos,
  restoreVideos
} from '@/utils/request';
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

const uploadFormTags = ref<string[]>([]);
const watermarkEnabled = ref(false);
const compressVideoEnabled = ref(true);
const watermarkPosition = ref(2);
const watermarkPositionOptions = [
  { value: 1, label: '左上', image: 'pos-1.jpg' },
  { value: 2, label: '右上', image: 'pos-2.jpg' },
  { value: 3, label: '中间', image: 'pos-3.jpg' },
  { value: 4, label: '左下', image: 'pos-4.jpg' },
  { value: 5, label: '右下', image: 'pos-5.jpg' }
];
const inputValueString = ref('');
const inputVisible = ref(false);
const inputValue = ref('');
const tagInputRef = ref();

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

// 批量上传相关
const showBatchUploadDialog = ref(false);
const batchUploadComponent = ref();

const selectedVideo = ref<any>(null);
const previewVideoData = ref<any>(null);
const fileList = ref<any[]>([]);
const machineList = ref<any[]>([]);

// 预览相关变量
const isShowingOriginal = ref(false);
const currentPreviewPath = ref('');
const currentVideoSrc = ref('');

// 编辑相关变量
const isEditingAll = ref(false);
const editTitle = ref('');
const editTagsInput = ref('');
const editRemark = ref('');
const currentTags = ref<string[]>([]);
const savingAll = ref(false);

// 回收站相关变量
const showingRecycleBin = ref(false);  // 是否显示回收站
const selectedVideos = ref<number[]>([]);  // 选中的视频ID数组（回收站模式下使用）
const totalDeletedSize = ref(0);  // 回收站中文件的总大小

// 普通视频列表多选相关状态
const isMultiSelectMode = ref(false); // 是否处于普通视频列表的多选模式
const selectedNormalVideos = ref<number[]>([]); // 选中的普通视频ID列表

// 权限相关
const isAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'admin';
});

// 通用日志组件相关
const logDialogVisible = ref(false);

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
// 视频加载错误处理 - 支持路径切换（原文件vs压缩文件）
const onVideoError = (event: Event) => {
  console.error('视频加载失败:', event);

  if (selectedVideo.value) {
    const videoElement = event.target as HTMLVideoElement;
    const currentSrc = videoElement.src;

    // 尝试切换到备用路径
    let newSrc = null;

    // 如果当前使用的是压缩路径，尝试切换到原始路径
    if (selectedVideo.value.compressed_path && currentSrc.includes(selectedVideo.value.compressed_path)) {
      if (selectedVideo.value.original_path) {
        newSrc = `${apiBaseUrl.value}/assets/Media/Videos/${selectedVideo.value.original_path}`;
        console.log(`视频加载失败，尝试使用原始路径: ${selectedVideo.value.original_path}`);
      }
    }
    // 如果当前使用的是原始路径，尝试切换到压缩路径
    else if (selectedVideo.value.original_path && currentSrc.includes(selectedVideo.value.original_path)) {
      if (selectedVideo.value.compressed_path) {
        newSrc = `${apiBaseUrl.value}/assets/Media/Videos/${selectedVideo.value.compressed_path}`;
        console.log(`视频加载失败，尝试使用压缩路径: ${selectedVideo.value.compressed_path}`);
      }
    }

    if (newSrc) {
      // 更新视频源
      currentVideoSrc.value = newSrc;
      // 注意：由于Vue的响应式机制，这里可能需要触发重新渲染
      // 通过给video元素添加key来强制重新创建元素
    } else {
      ElMessage.error('视频加载失败，未找到可用的备用路径');
    }
  } else {
    ElMessage.error('视频加载失败');
  }
};

const isVideoProcessing = (video: any) => {
  return ['pending', 'processing', 'compressing'].includes(
    String(video?.compress_status || '').toLowerCase()
  );
};

let processingRefreshTimer: ReturnType<typeof setInterval> | undefined;

// 获取视频列表
const fetchVideos = async () => {
  try {
    if (showingRecycleBin.value) {
      // 如果显示回收站，则获取已删除的视频
      const response = await getDeletedVideos({
        page: currentPage.value,
        per_page: pageSize.value,
        search: searchQuery.value
      });

      videos.value = response.videos;
      totalVideos.value = response.total;
    } else {
      // 否则获取正常的视频列表
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
    }
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

  // 未启用压缩时限制文件大小；压缩模式不设应用层文件大小限制
  const maxSize = 500 * 1024 * 1024; // 500MB
  if (!compressVideoEnabled.value && file.raw.size > maxSize) {
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

// 关闭批量上传对话框
const handleBatchUploadDialogClose = (done: () => void) => {
  // 这里可以添加确认提示，如果批量上传正在进行中
  done();
};

// 处理批量上传完成事件
const handleBatchUploadComplete = () => {
  // 关闭批量上传对话框
  showBatchUploadDialog.value = false;
  // 刷新视频列表数据
  fetchVideos();
};

// 添加标签函数
// 标签处理函数
const handleTagClose = (tag: string) => {
  const index = uploadFormTags.value.indexOf(tag);
  if (index > -1) {
    uploadFormTags.value.splice(index, 1);
  }
};

const showInput = () => {
  inputVisible.value = true;
  nextTick(() => {
    tagInputRef.value?.focus();
  });
};

const handleInputConfirm = () => {
  if (inputValue.value) {
    // 按逗号分割输入的标签
    const newTags = inputValue.value.split(',').map(tag => tag.trim()).filter(tag => tag);

    newTags.forEach(tag => {
      if (!uploadFormTags.value.includes(tag)) {
        uploadFormTags.value.push(tag);
      }
    });
  }
  inputVisible.value = false;
  inputValue.value = '';
};

// 标签输入框失焦处理函数
const handleTagInputBlur = () => {
  if (inputValueString.value) {
    const newTags = inputValueString.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    // 去重并更新标签数组
    const uniqueTags = Array.from(new Set(newTags));
    uploadFormTags.value = uniqueTags;
  }
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
    formData.append('watermark_enabled', String(watermarkEnabled.value));
    formData.append('watermark_position', String(watermarkPosition.value));
    formData.append('compress_video', String(compressVideoEnabled.value));

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
  watermarkEnabled.value = false;
  compressVideoEnabled.value = true;
  watermarkPosition.value = 2;
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

const handleVideoMenuCommand = (command: string, video: any) => {
  if (command === 'delete') {
    deleteVideo(video.id);
  } else if (command === 'compress' && !video.compressed_path && !isVideoProcessing(video)) {
    compressVideo(video.id);
  }
};

const compressVideo = async (video: any) => {
  try {
    await ElMessageBox.confirm(`确定要压缩视频“${video.title}”吗？`, '确认压缩', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    await compressVideoAPI(video.id);
    ElMessage.success('视频已加入压缩队列');
    fetchVideos();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('压缩视频失败:', error);
      ElMessage.error('压缩视频失败');
    }
  }
};

const videoFilename = computed(() => (selectedVideo.value?.compressed_path || selectedVideo.value?.original_path || '').split('/').pop() || '视频');
const videoTechnicalInfo = computed(() => {
  const video = selectedVideo.value;
  if (!video) return '';
  const extension = videoFilename.value.includes('.') ? videoFilename.value.split('.').pop()?.toUpperCase() : '';
  const dimensions = video.original_width && video.original_height ? `${video.original_width} × ${video.original_height}` : '';
  return [extension, dimensions, video.duration ? formatDuration(video.duration) : '', video.file_size != null ? formatFileSize(video.file_size) : ''].filter(Boolean).join(' / ');
});

// 查看视频详情
const viewVideoDetails = (video: any) => {
  selectedVideo.value = video;
  // 初始化编辑值
  editTitle.value = video?.title || '';
  editRemark.value = video?.remark || '';
  // 初始化标签显示
  const tagsString = video?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];

  // 设置视频源路径：优先使用压缩路径，如果不存在则使用原始路径
  if (video.compressed_path) {
    currentVideoSrc.value = `${apiBaseUrl.value}/assets/Media/Videos/${video.compressed_path}`;
  } else if (video.original_path) {
    currentVideoSrc.value = `${apiBaseUrl.value}/assets/Media/Videos/${video.original_path}`;
  } else {
    currentVideoSrc.value = '';
  }

  // 重置编辑状态
  isEditingAll.value = false;
  editTagsInput.value = '';

  showDetailsDialog.value = true;
};

// 开始编辑所有信息
const startEditingAll = () => {
  editTitle.value = selectedVideo.value?.title || '';
  editRemark.value = selectedVideo.value?.remark || '';
  const tagsString = selectedVideo.value?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
  isEditingAll.value = true;
  editTagsInput.value = currentTags.value.join(',');
};

// 保存所有更改
const saveAll = async () => {
  if (!selectedVideo.value) return;

  const originalTags = selectedVideo.value.tags || '';
  const initialTagsInput = originalTags.split(',').map((tag: string) => tag.trim()).filter(Boolean).join(',');
  const tagsChanged = editTagsInput.value !== initialTagsInput;
  if (editTitle.value === (selectedVideo.value.title || '') &&
      editRemark.value === (selectedVideo.value.remark || '') && !tagsChanged) {
    isEditingAll.value = false;
    return;
  }

  savingAll.value = true;
  try {
    const tagsString = tagsChanged
      ? [...new Set(editTagsInput.value.split(/[,，]/).map(tag => tag.trim()).filter(Boolean))].join(',')
      : originalTags;
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

    currentTags.value = tagsString ? tagsString.split(',') : [];
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
  const videoPath = selectedVideo.value?.compressed_path || selectedVideo.value?.original_path;
  if (videoPath) {
    const videoUrl = `${apiBaseUrl.value}/assets/Media/Videos/${videoPath}`;
    // 创建一个临时链接来下载视频，并以视频标题命名
    const link = document.createElement('a');
    link.href = videoUrl;
    // 使用视频标题作为文件名，如果标题为空则使用默认名称
    const fileName = selectedVideo.value.title ? selectedVideo.value.title.trim() : 'video';
    // 确保文件扩展名正确
    const fileExtension = videoUrl.split('.').pop() || 'mp4';
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

// 进入回收站
const enterRecycleBin = async () => {
  showingRecycleBin.value = true;
  isMultiSelectMode.value = false;
  currentPage.value = 1;
  selectedVideos.value = []; // 清空选中的视频
  await fetchDeletedVideos();
};

// 退出回收站
const exitRecycleBin = () => {
  showingRecycleBin.value = false;
  currentPage.value = 1;
  selectedVideos.value = []; // 清空选中的视频
  fetchVideos(); // 重新获取正常视频列表
};

// 获取已删除的视频列表
const fetchDeletedVideos = async () => {
  try {
    const response = await getDeletedVideos({
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchQuery.value
    });

    videos.value = response.videos;
    totalVideos.value = response.total;

    // 计算回收站中所有视频的总大小
    totalDeletedSize.value = response.videos.reduce((total, video) => {
      return total + (video.file_size || 0);
    }, 0);
  } catch (error) {
    console.error('获取已删除视频列表失败:', error);
    ElMessage.error('获取已删除视频列表失败');
  }
};

// 恢复视频确认
const confirmRestore = async () => {
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请先选择要恢复的视频');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要恢复选中的 ${selectedVideos.value.length} 个视频吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    );

    await restoreVideos(selectedVideos.value);
    ElMessage.success(`成功恢复 ${selectedVideos.value.length} 个视频`);

    // 清空选中项并刷新列表
    selectedVideos.value = [];
    await fetchDeletedVideos();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复视频失败:', error);
      ElMessage.error('恢复失败');
    }
  }
};

// 物理删除确认
const confirmPhysicalDelete = async () => {
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请先选择要物理删除的视频');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要永久删除选中的 ${selectedVideos.value.length} 个视频吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await physicalDeleteVideos(selectedVideos.value);
    ElMessage.success(`成功物理删除 ${selectedVideos.value.length} 个视频`);

    // 清空选中项并刷新列表
    selectedVideos.value = [];
    await fetchDeletedVideos();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('物理删除视频失败:', error);
      ElMessage.error('物理删除失败');
    }
  }
};

// 切换视频选择状态
const toggleVideoSelection = (video: any) => {
  const index = selectedVideos.value.indexOf(video.id);
  if (index > -1) {
    // 如果已选中，则取消选中
    selectedVideos.value.splice(index, 1);
  } else {
    // 如果未选中，则添加到选中列表
    selectedVideos.value.push(video.id);
  }
};

// 全选/取消全选功能
const toggleSelectAll = () => {
  if (selectedVideos.value.length === videos.value.length) {
    // 如果当前已全选，则取消全选
    selectedVideos.value = [];
  } else {
    // 如果未全选，则全选
    selectedVideos.value = videos.value.map(video => video.id);
  }
};

// 处理视频选择变化（保留原来的，以兼容其他可能的用法）
const handleSelectionChange = (selected: any[]) => {
  selectedVideos.value = selected.map(video => video.id);
};

// 添加专门的日志跳转处理函数
const handleLogJump = async (id: number) => {
  console.log(`跳转到视频ID: ${id}`);

  // 首先检查当前页面的视频列表中是否包含该视频
  const currentVideo = videos.value.find(video => video.id === id);

  if (currentVideo) {
    // 如果在当前页面找到视频，直接打开详情
    viewVideoDetails(currentVideo);
  } else {
    // 如果当前页面没有找到，需要从服务器获取该视频信息
    try {
      const response = await request.get(`/api/videos/${id}`);

      // 检查响应是否成功
      if (response && response.code === 200) {
        const responseData = response.data; // 获取实际数据
        // 打开视频详情
        viewVideoDetails(responseData);
      } else {
        // 如果后端返回了错误格式的响应
        if (response && response.code !== 200 &&
            response.msg && (response.msg.includes('404') || response.msg.toLowerCase().includes('not found'))) {
          ElMessage.error('该视频已删除或不存在');
        } else {
          ElMessage.error('加载视频详情失败');
        }
      }
    } catch (error: any) {
      console.error('加载视频详情失败:', error);
      // 检查错误是否为404相关的错误
      if (error && error.response) {
        const responseData = error.response.data;
        if (responseData && typeof responseData === 'object' &&
            responseData.msg && (responseData.msg.includes('404') || responseData.msg.toLowerCase().includes('not found'))) {
          ElMessage.error('该视频已删除或不存在');
        } else {
          ElMessage.error('加载视频详情失败');
        }
      } else {
        ElMessage.error('加载视频详情失败');
      }
    }
  }
};
// 显示视频日志
const showVideoLogs = () => {
          if (!isAdmin.value) {    ElMessage.error('您没有权限查看日志');
    return;
  }
  // 先重置日志组件的状态，再显示对话框
  logDialogVisible.value = false;
  // 使用nextTick确保状态更新后再显示
  nextTick(() => {
    logDialogVisible.value = true;
  });
};

// 切换普通视频列表多选模式
const toggleMultiSelectMode = () => {
  isMultiSelectMode.value = !isMultiSelectMode.value;
  if (!isMultiSelectMode.value) {
    // 退出多选模式时清空选中项
    selectedNormalVideos.value = [];
  }
};

// 选择单个普通视频
const selectNormalVideo = (videoId: number) => {
  const index = selectedNormalVideos.value.indexOf(videoId);
  if (index > -1) {
    // 已选中，取消选择
    selectedNormalVideos.value.splice(index, 1);
  } else {
    // 未选中，添加选择
    selectedNormalVideos.value.push(videoId);
  }
};

// 普通视频列表全选/取消全选
const toggleSelectAllNormal = () => {
  if (selectedNormalVideos.value.length === videos.value.length) {
    // 当前已全选，取消全选
    selectedNormalVideos.value = [];
  } else {
    // 未全选，进行全选
    selectedNormalVideos.value = videos.value.map(video => video.id);
  }
};

// 批量删除选中的普通视频
const batchDeleteNormalVideos = async () => {
  if (selectedNormalVideos.value.length === 0) {
    ElMessage.warning('请先选择要删除的视频');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedNormalVideos.value.length} 个视频吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 批量删除视频
    let successCount = 0;
    let errorCount = 0;

    for (const videoId of selectedNormalVideos.value) {
      try {
        await deleteVideoAPI(videoId);
        successCount++;
      } catch (error) {
        console.error(`删除视频 ${videoId} 失败:`, error);
        errorCount++;
      }
    }

    if (errorCount > 0) {
      ElMessage.warning(`批量删除完成: ${successCount} 个成功, ${errorCount} 个失败`);
    } else {
      ElMessage.success(`成功删除 ${successCount} 个视频`);
    }

    // 重置选择状态并刷新列表
    selectedNormalVideos.value = [];
    isMultiSelectMode.value = false;
    fetchVideos();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除视频失败:', error);
      ElMessage.error('批量删除失败');
    }
  }
};

// 检查普通视频是否被选中
const isNormalVideoSelected = (videoId: number) => {
  return selectedNormalVideos.value.includes(videoId);
};

// 初始化
onMounted(() => {
  fetchVideos();
  fetchMachines();
  processingRefreshTimer = setInterval(() => {
    if (!showingRecycleBin.value && videos.value.some(isVideoProcessing)) {
      fetchVideos();
    }
  }, 3000);
});

onBeforeUnmount(() => {
  if (processingRefreshTimer) {
    clearInterval(processingRefreshTimer);
  }
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
  background-color: #202020;
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
  justify-content: center;
  min-height: 100px;
  background-color: #363636;
  border-radius: 5px;
  /* 关键：给父容器添加内边距，避免子元素圆角被裁切，同时限制溢出 */
  padding: 2px; /* 可选：留一点边距，视觉更友好 */
  overflow: hidden;
}

.video-preview-wrapper {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: #000;
  /* 核心：自适应填满父容器且不超出 */
  width: 100%;
  height: 100%;
  /* 关键：维持视频比例（16:9），避免拉伸变形 */
  aspect-ratio: 16/9;
  /* 自适应缩放：优先占满宽度，高度自动适配；高度超了则占满高度，宽度自动适配 */
  max-width: 100%;
  max-height: 100%;
  /* 确保内容居中 */
  display: flex;
  align-items: center;
  justify-content: center;
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
}

/* Logo 水印设置区 */
.watermark-settings-panel {
  margin-top: 18px;
  padding: 16px 18px 18px;
  border: 1px solid #e4edf8;
  border-radius: 8px;
  background: #f7faff;
}

.watermark-settings-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 24px;
  font-size: 14px;
}

.watermark-position-selector {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #e7edf5;
}

.watermark-position-label {
  margin-bottom: 12px;
  color: #606266;
  font-size: 14px;
  font-weight: 400;
}

.watermark-position-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.watermark-position-card {
  min-width: 0;
  padding: 5px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  color: #606266;
  cursor: pointer;
  font: inherit;
  text-align: center;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.watermark-position-card:hover {
  border-color: #a8abb2;
}

.watermark-position-card.selected {
  border-color: #409eff;
  background: #fff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.12);
  color: #409eff;
}

.watermark-position-card img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 4px;
  object-fit: cover;
}

.watermark-position-card span {
  display: block;
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.2;
  text-align: center;
}

.watermark-position-card.selected span {
  color: #409eff;
  font-weight: 500;
}

/* 视频后台处理状态 */
.video-processing-overlay {
  position: absolute;
  inset: 0;
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  pointer-events: none;
}

.video-processing-icon {
  font-size: 28px;
  animation: video-processing-spin 1.3s linear infinite;
}

@keyframes video-processing-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

  .watermark-position-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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

.result-count-container {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.result-count {
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

/* 回收站相关样式 */
.video-card.selected {
  border: 2px solid #409eff; /* 选中时的边框颜色 */
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.5); /* 选中时的阴影效果 */
}

.select-checkbox {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  padding: 2px;
}

.el-checkbox{
  width: 32px;
  height: 32px;
}


.header-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 回收站信息样式 */
.recycle-info {
  font-size: 12px;
  line-height: 1.4;
}

.info-item {
  margin: 2px 0;
}

.time-label {
  font-weight: bold;
  color: #606266;
}

/* 回收站统计信息样式 */
.recycle-statistics {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
}
.el-icon{
  margin-right: 5px;
}

.result-refresh-btn{
  cursor: pointer;
  margin-left: 5px;
  font-size: 20px;
}

/* 日志跳转高亮样式 */
.video-card.log-highlight {
  border: 2px solid #e6a23c !important; /* 橙色边框 */
  box-shadow: 0 0 15px rgba(230, 162, 60, 0.5) !important; /* 发光效果 */
  transform: scale(1.02); /* 稍微放大 */
  transition: all 0.3s ease; /* 平滑过渡 */
}

/* 多选模式按钮样式 */
.multi-select-buttons {
  display: flex;
  gap: 8px;
}

/* 视频卡片多选样式 */
.video-card.selected {
  border: 2px solid #409eff; /* 选中时边框为蓝色 */
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.video-card .select-checkbox {
  position: absolute;
  z-index: 10;
  background-color: white;
  border-radius: 50%;
  padding: 2px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.video-card .select-checkbox .el-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(.video-detail-v2-dialog.el-dialog){--el-dialog-padding-primary:0;padding:0;background:#faf9f6;border-radius:12px;height:94vh;max-height:94vh;overflow:hidden;margin-top:3vh!important;color:#25303b;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}
:global(.video-detail-v2-dialog .el-dialog__body){height:100%;overflow-y:auto;overflow-x:hidden}:global(.video-detail-v2-dialog .el-dialog__header){padding:0;margin:0}:global(.video-detail-v2-dialog .el-dialog__headerbtn){z-index:2;top:10px;right:10px}
.vd-shell,.vd-shell *{box-sizing:border-box}.vd-shell{min-height:100%;padding:20px 30px 28px;display:flex;flex-direction:column;color:#25303b}.vd-shell button,.vd-shell input,.vd-shell textarea{font-family:inherit}.vd-toolbar{height:60px;min-height:60px;display:flex;align-items:flex-start;justify-content:flex-end;gap:10px;padding-right:48px}
.vd-btn{border:1px solid #d4deeb;background:#fff;color:#263849;padding:11px 17px;border-radius:12px;font-size:13px;cursor:pointer;white-space:nowrap}.vd-btn:hover{background:#f3f6f8}.vd-btn:disabled{opacity:.6;cursor:not-allowed}.vd-btn.vd-primary{background:#203d32;color:white;border-color:#203d32}
.vd-layout{display:grid;grid-template-columns:minmax(0,1.66fr) minmax(340px,1fr);gap:20px;flex:1}.vd-preview{min-height:650px;border-radius:25px;background:#e5eaea;padding:25px;display:flex;flex-direction:column;min-width:0}.vd-eyebrow{font-size:12px;color:#687d90}.vd-stage{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:28px 0}.vd-video-wrap{width:100%;max-width:660px;aspect-ratio:16/9;background:#161c1e;border-radius:7px;overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 5px 24px #25303b16}.vd-video-wrap .video-preview{width:100%;height:100%;max-height:none;object-fit:contain}
.vd-filefoot{display:flex;align-items:center;justify-content:space-between;gap:16px}.vd-filename{font-size:14px;font-weight:700;overflow-wrap:anywhere}.vd-sub{font-size:12px;color:#738397;margin-top:2px}.vd-right{display:grid;grid-template-rows:minmax(444px,1fr) minmax(300px,auto);gap:17px;min-width:0}.vd-panel{border:1px solid #eae6df;background:#fff;border-radius:23px;padding:26px;min-width:0}.vd-panel h2{font-size:18px;margin:0 0 30px;font-weight:750;color:#222a32;line-height:normal}.vd-field{padding:0 0 14px;margin-bottom:14px;border-bottom:1px solid #eeefef}.vd-field:last-child{border-bottom:0}.vd-label{font-size:12px;color:#8392a5;margin-bottom:8px}.vd-value{font-size:14px;line-height:1.6;overflow-wrap:anywhere;min-height:23px}.vd-note{white-space:pre-wrap}
.vd-editor{width:100%;font-size:14px;color:#25303b;border:1px solid #cbd7e5;border-radius:9px;padding:9px 11px;outline:none;background:#fff}.vd-editor:focus{border-color:#769e96}.vd-note-editor{height:100px;resize:none;overflow:auto}.vd-avatarrow{display:flex;align-items:center;gap:12px;margin-bottom:24px}.vd-avatar{height:42px;width:42px;border-radius:50%;background:#e1eddf;color:#3c7757;display:grid;place-items:center;font-weight:700}.vd-person{font-size:14px;font-weight:700}.vd-recorditem{margin-top:17px}
@media(max-width:850px){.vd-shell{padding:14px}.vd-layout{grid-template-columns:1fr}.vd-preview{min-height:390px}.vd-stage{padding:25px 0}.vd-right{grid-template-rows:auto}.vd-panel{padding:22px}.vd-toolbar{height:52px;min-height:52px}}

:global(.video-upload-v2.el-dialog){--el-dialog-padding-primary:0;padding:26px 30px;background:#faf9f6;border-radius:17px;max-height:94vh;overflow-y:auto;margin-top:3vh!important;color:#263138;font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}
:global(.video-upload-v2 .el-dialog__header){padding:0;margin:0 0 20px}:global(.video-upload-v2 .el-dialog__title){font-size:23px;font-weight:700;color:#263138}:global(.video-upload-v2 .el-dialog__headerbtn){top:18px;right:18px}
.vu-form,.vu-form *{box-sizing:border-box}.vu-layout{display:grid;grid-template-columns:1.05fr .95fr;gap:18px;align-items:start}.vu-card{border:1px solid #e7e5de;background:#fff;border-radius:21px;padding:22px;min-width:0}.vu-card h2,.vu-match h2{font-size:17px;margin:0 0 16px;color:#263138;line-height:normal}.vu-form :deep(.el-form-item){margin-bottom:15px}.vu-form :deep(.el-form-item__label){font-size:12px;color:#748390;line-height:1.4;margin-bottom:6px;padding:0}.vu-form :deep(.el-select),.vu-form :deep(.el-input-tag){width:100%}.vu-form :deep(.el-input__wrapper),.vu-form :deep(.el-select__wrapper),.vu-form :deep(.el-input-tag__wrapper){min-height:40px;border-radius:9px}.vu-form :deep(.el-textarea__inner){border-radius:9px;min-height:100px!important}.vu-file-field :deep(.el-form-item__content){display:block}.vu-upload{width:100%}.vu-upload :deep(.el-upload){width:100%;display:block}.vu-upload :deep(.el-upload-dragger){width:100%;min-height:190px;border:2px dashed #b7c8c3;background:#e5eae9;border-radius:17px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;padding:16px;color:#263138}.vu-upload :deep(.el-upload-dragger:hover){background:#dceae5;border-color:#31735d}.vu-upload :deep(.el-upload-list){max-height:150px;overflow:auto}.vu-drop-icon{font-size:36px;color:#416e5c}.vu-muted,.vu-hint{font-size:12px;color:#7b8990;line-height:1.5}.vu-hint{margin:12px 0}.vu-btn{border:1px solid #d4dfe2;background:white;border-radius:10px;padding:9px 15px;color:#34434d;cursor:pointer;font:inherit}.vu-btn:disabled{opacity:.45;cursor:not-allowed}.vu-btn.vu-primary{background:#213e33;border-color:#213e33;color:white}.vu-btn.vu-soft{background:#eef4f1;color:#245b47;border-color:#d4e5db}.vu-footer{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:19px}.vu-actions,.vu-small-actions{display:flex;gap:10px;flex-wrap:wrap}.vu-progress{margin-top:15px}
@media(max-width:800px){.vu-layout{grid-template-columns:1fr}:global(.video-upload-v2.el-dialog){padding:20px}}

.vu-option{background:#f4f7f6;border:1px solid #e1eae6;border-radius:14px;padding:16px;margin-top:16px}.vu-option :deep(.el-checkbox){display:flex;margin:0 0 9px;color:#236c58}.vu-watermark{border-top:1px solid #e1eae6;padding-top:16px}.vu-label{font-size:12px;color:#748390;margin-bottom:8px}.vu-positions{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}.vu-position{background:white;border:2px solid #e3e8e7;border-radius:9px;padding:6px 2px;cursor:pointer;text-align:center;font-size:12px;color:#66777e}.vu-position.selected{border-color:#347963;color:#266a57}.vu-position img{display:block;width:100%;height:37px;object-fit:cover;border-radius:5px}.vu-position span{display:block}.vu-divider{height:1px;background:#eef0ed;margin:18px 0}.vu-upload :deep(.el-upload-dragger){min-height:225px}
</style>
