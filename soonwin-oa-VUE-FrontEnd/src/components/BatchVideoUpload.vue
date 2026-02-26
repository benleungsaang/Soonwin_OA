<template>
  <div class="batch-video-upload">
    <!-- 拖拽上传区域 -->
    <el-upload
      ref="uploadRef"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :file-list="fileList"
      :on-remove="handleFileRemove"
      :accept="'.mp4,.avi,.mov,.mkv,.wmv,.json'"
      :multiple="true"
      :on-drop="handleDrop"
      :on-dragover="handleDragOver"
      :on-dragleave="handleDragLeave"
      class="upload-dragger"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        将视频或JSON文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持多视频文件和JSON配置文件，支持 mp4/avi/mov/mkv/wmv 格式，JSON文件用于批量配置
        </div>
      </template>
    </el-upload>

    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list-section">
      <div class="section-header">
        <h4>已选择的文件</h4>
        <div class="file-actions">
          <el-button @click="clearAllFiles" size="small" type="danger">清空全部</el-button>
          <el-button
            v-if="hasVideoAndJson && !isMatching"
            @click="matchFiles"
            size="small"
            type="primary"
            :disabled="isMatching"
          >
            匹配
          </el-button>
          <el-button
            v-if="hasVideoAndJson && isMatching"
            @click="matchFiles"
            size="small"
            type="primary"
            :disabled="true"
          >
            匹配中...
          </el-button>
        </div>
      </div>

      <el-table :data="fileList" style="width: 100%" border>
        <el-table-column prop="name" label="文件名" width="300">
          <template #default="{ row }">
            <div class="file-info">
              <el-icon v-if="isVideoFile(row.name)"><VideoPlay /></el-icon>
              <el-icon v-else-if="isJsonFile(row.name)"><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="raw.type" label="文件类型" width="120" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button @click="removeFile(row)" type="danger" size="small" :icon="Delete" circle />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 匹配结果对话框 -->
    <el-dialog
      v-model="showMatchResultDialog"
      title="批量上传 - 匹配结果"
      width="80%"
      :before-close="handleMatchResultDialogClose"
    >
            <div class="match-result-header">
              <p>共有 <strong>{{ matchedVideos.length }}</strong> 个视频匹配成功</p>
              <div class="match-actions">
                <el-button 
                  @click="selectAllForUpload" 
                  size="small"
                  :icon="CircleCheck"
                >
                  全选
                </el-button>
                <el-button 
                  @click="unselectAllForUpload" 
                  size="small"
                  :icon="Remove"
                >
                  全不选
                </el-button>
              </div>
            </div>
            <el-table
              ref="tableRef"
              :data="matchResults"
              style="width: 100%"
              border
              @selection-change="handleSelectionChange"
            >
        <el-table-column type="selection" width="55" :selectable="isRowSelectable" />
        <el-table-column v-if="isUploading" label="上传进度" width="150">
          <template #default="{ row }">
            <template v-if="selectedForUpload.some(item => item.filename === row.filename)">
              <div style="width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin-top: 4px;">
                <div :style="{width: `${getUploadProgress(row.filename)}%`, height: '100%', backgroundColor: getProgressColor(row.filename), borderRadius: '4px', transition: 'width 0.3s ease'}"></div>
              </div>
              <div style="text-align: right; margin-top: 2px; font-size: 12px; color: #606266;">{{ getUploadProgress(row.filename) }}%</div>
            </template>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="视频文件名" prop="filename" width="200">
          <template #default="{ row }">
            <div class="file-info">
              <el-icon><VideoPlay /></el-icon>
              <span>{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="标题" prop="title" width="200" />
        <el-table-column label="标签" prop="tags" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="tag in getTagsArray(row.tags)"
              :key="tag"
              size="small"
              style="margin-right: 4px; margin-bottom: 4px;"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="备注" prop="remark" width="200" />
                <el-table-column label="状态" prop="status" width="120">
                  <template #default="{ row }">
                    <el-tag 
                      :type="getStatusType(row.status)"
                    >
                      {{ getStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>      </el-table>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showMatchResultDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="batchUpload"
            :disabled="selectedForUpload.length === 0"
            :loading="isUploading"
          >
            批量上传 ({{ selectedForUpload.length }})
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus';
import { UploadFilled, Delete, VideoPlay, Document, CircleCheck, Remove } from '@element-plus/icons-vue';
import { createVideo } from '@/utils/request';
import request from '@/utils/request';

// 定义emit事件
const emit = defineEmits(['upload-complete']);

// 响应式数据
const uploadRef = ref();
const tableRef = ref();
const fileList = ref<any[]>([]);
const videos = ref<any[]>([]);
const jsonFile = ref<any>(null);
const showMatchResultDialog = ref(false);
const matchResults = ref<any[]>([]);
const selectedForUpload = ref<any[]>([]);
const isMatching = ref(false);
const isUploading = ref(false);
const uploadProgressMap = ref<Record<string, number>>({});

// 计算属性
const hasVideoAndJson = computed(() => {
  const videoCount = fileList.value.filter(file => isVideoFile(file.name)).length;
  const jsonCount = fileList.value.filter(file => isJsonFile(file.name)).length;
  return videoCount > 0 && jsonCount > 0;
});

const matchedVideos = computed(() => {
  return matchResults.value.filter(item => item.status === 'matched');
});

const duplicateTitleCount = computed(() => {
  return 0; // 移除标题重复检查后，始终为0
});

// 方法
const isVideoFile = (filename: string) => {
  const videoExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv'];
  return videoExtensions.some(ext => filename.toLowerCase().endsWith(ext));
};

const isJsonFile = (filename: string) => {
  return filename.toLowerCase().endsWith('.json');
};

const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const handleFileChange = (file: any, fileListArr: any[]) => {
  // 检查是否是多视频文件上传
  const videoFiles = fileListArr.filter(item => isVideoFile(item.name));
  const jsonFiles = fileListArr.filter(item => isJsonFile(item.name));

  // 如果是视频文件，检查是否需要提示上传JSON
  if (isVideoFile(file.name) && videoFiles.length > 1 && jsonFiles.length === 0) {
    ElMessage.info('检测到多个视频文件，请上传JSON配置文件进行批量配置');
  }

  // 更新fileList
  fileList.value = fileListArr;

  // 分离视频和JSON文件
  updateVideoAndJsonFiles();
};

const updateVideoAndJsonFiles = () => {
  videos.value = fileList.value.filter(file => isVideoFile(file.name));
  const jsonFiles = fileList.value.filter(file => isJsonFile(file.name));
  jsonFile.value = jsonFiles.length > 0 ? jsonFiles[0] : null;
};

const handleFileRemove = (file: any, fileListArr: any[]) => {
  fileList.value = fileListArr;
  updateVideoAndJsonFiles();
};

const removeFile = (file: any) => {
  const index = fileList.value.findIndex(f => f.uid === file.uid);
  if (index !== -1) {
    fileList.value.splice(index, 1);
    updateVideoAndJsonFiles();
  }
};

const clearAllFiles = () => {
  fileList.value = [];
  videos.value = [];
  jsonFile.value = null;
};

const handleDragOver = (event: DragEvent) => {
  event.preventDefault();
};

const handleDragLeave = () => {
  // 可以添加拖拽离开的样式
};

const handleDrop = async (event: DragEvent) => {
  event.preventDefault();

  if (event.dataTransfer?.items) {
    const items = Array.from(event.dataTransfer.items);
    const files = [];

    for (const item of items) {
      if (item.kind === 'file') {
        files.push(item.getAsFile());
      }
    }

    // 检查是否是多视频拖拽
    const videoFiles = files.filter(file => isVideoFile(file.name));
    if (videoFiles.length > 1) {
      // 检查是否有JSON文件
      const jsonFiles = files.filter(file => isJsonFile(file.name));
      if (jsonFiles.length === 0) {
        ElMessage.info('检测到多个视频文件，请同时拖入JSON配置文件进行批量配置');
      }
    }

    // 添加文件到列表
    const newFiles = files.map(file => ({
      name: file.name,
      size: file.size,
      raw: file,
      uid: Date.now() + Math.random()
    }));

    fileList.value = [...fileList.value, ...newFiles];
    updateVideoAndJsonFiles();
  }
};

const matchFiles = async () => {
  if (!hasVideoAndJson.value) {
    ElMessage.warning('请同时上传视频文件和JSON配置文件');
    return;
  }

  isMatching.value = true;

  try {
    // 读取JSON文件内容
    const jsonContent = await readJsonFile(jsonFile.value.raw);
    const jsonData = JSON.parse(jsonContent);

    // 提取视频信息
    const videoConfigs = jsonData.videos || [];

    // 匹配视频文件和配置
    const results = [];

    for (const videoFile of videos.value) {
      const filename = videoFile.name;
      // 从filePath中提取文件名
      const matchedConfig = videoConfigs.find((config: any) => {
        const filePathFileName = config.filePath ? config.filePath.split('/').pop() : '';
        return filePathFileName === filename || config.filename === filename;
      });

            if (matchedConfig) {
              results.push({
                filename: filename,
                title: matchedConfig.title || '',
                tags: Array.isArray(matchedConfig.tagNames) ? matchedConfig.tagNames.join(',') : matchedConfig.tags || '',
                remark: matchedConfig.remark || '',
                status: 'matched',
                videoFile: videoFile
              });
            } else {
              results.push({
                filename: filename,
                title: '',
                tags: '',
                remark: '',
                status: 'unmatched',
                videoFile: videoFile
              });
            }    }

        matchResults.value = results;

            matchResults.value = results;

                matchResults.value = results;



                showMatchResultDialog.value = true;



                // 在对话框显示后，下一帧自动勾选所有匹配成功的视频

                nextTick(() => {

                  // 使用表格ref来设置默认选中项

                  if (tableRef.value) {

                    // 等待表格渲染完成

                    setTimeout(() => {

                      // 获取表格实例的选择方法

                      const matchedResults = results.filter(item => item.status === 'matched');

                      selectedForUpload.value = matchedResults;



                      // 手动设置表格行的选中状态

                      results.forEach((row, index) => {

                        if (row.status === 'matched') {

                          tableRef.value.toggleRowSelection(row, true);

                        }

                      });

                    }, 100);

                  }

                });      } catch (error) {
        console.error('匹配文件失败:', error);
        ElMessage.error('匹配文件失败，请检查JSON文件格式');
      } finally {
        isMatching.value = false;
      }
    };const readJsonFile = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve(reader.result as string);
    };
    reader.onerror = () => {
      reject(new Error('读取JSON文件失败'));
    };
    reader.readAsText(file, 'utf-8');
  });
};


const getStatusType = (status: string) => {
  if (status !== 'matched') return 'info';
  return 'success';
};

const getStatusText = (status: string) => {
  if (status === 'matched') {
    return '匹配成功';
  }
  return '未匹配';
};

const getTagsArray = (tags: string) => {
  if (!tags) return [];
  return Array.isArray(tags) ? tags : tags.split(',').map(tag => tag.trim()).filter(tag => tag);
};

const isRowSelectable = (row: any) => {
  // 只有匹配成功的行才可选择
  return row.status === 'matched';
};

const getUploadProgress = (filename: string) => {
  return uploadProgressMap.value[filename] || 0;
};

const getProgressColor = (filename: string) => {
  const progress = getUploadProgress(filename);
  return progress === 100 ? '#67c23a' : '#409eff'; // 完成时绿色，其他时候蓝色
};

const handleSelectionChange = (selection: any[]) => {
  selectedForUpload.value = selection;
};

const selectAllForUpload = () => {
  selectedForUpload.value = matchedVideos.value;
};

const unselectAllForUpload = () => {
  selectedForUpload.value = [];
};

const batchUpload = async () => {
  if (selectedForUpload.value.length === 0) {
    ElMessage.warning('请选择要上传的视频');
    return;
  }

  isUploading.value = true;
  // 初始化所有选中项的进度为0
  selectedForUpload.value.forEach(item => {
    uploadProgressMap.value[item.filename] = 0;
  });

  try {
    let successCount = 0;
    let errorCount = 0;

    for (const item of selectedForUpload.value) {
      try {
        const formData = new FormData();
        formData.append('file', item.videoFile.raw);
        formData.append('title', item.title);
        formData.append('tags', item.tags);
        formData.append('remark', item.remark);

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

        // 使用createVideo函数支持进度回调
        await createVideo(formData, (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            uploadProgressMap.value[item.filename] = progress;
          }
        });
        successCount++;
      } catch (uploadError) {
        console.error(`上传视频 ${item.filename} 失败:`, uploadError);
        errorCount++;
      } finally {
        // 无论成功还是失败，都把进度设为100，表示已完成
        uploadProgressMap.value[item.filename] = 100;
      }
    }

        if (errorCount > 0) {
          ElMessage.warning(`批量上传完成: ${successCount} 个成功, ${errorCount} 个失败`);
        } else {
          ElMessage.success(`成功上传 ${successCount} 个视频`);
        }
        
        // 关闭对话框并重置状态
        showMatchResultDialog.value = false;
        clearAllFiles();
        
        // 触发上传完成事件，通知父组件刷新数据
        emit('upload-complete');
      } catch (error) {
        console.error('批量上传失败:', error);
        ElMessage.error('批量上传失败');
      } finally {
        isUploading.value = false;
        // 重置进度
        Object.keys(uploadProgressMap.value).forEach(key => {
          uploadProgressMap.value[key] = 0;
        });
      }
    };const handleMatchResultDialogClose = (done: () => void) => {
  if (isUploading.value) {
    return;
  }
  done();
};

// 暴露方法给父组件使用
defineExpose({
  fileList,
  clearAllFiles
});
</script>

<style scoped>
.batch-video-upload {
  margin: 20px 0;
}

.upload-dragger {
  width: 100%;
  margin-bottom: 20px;
}

.file-list-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.match-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.match-actions {
  display: flex;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>