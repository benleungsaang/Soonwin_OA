<template>
  <div class="photo-management">
    <CommonHeader title="照片管理" />
        <div class="header">
          <div class="title-with-count">
            <h2>
              <template v-if="isRecycleBinMode">
                回收站
              </template>
              <template v-else>照片管理</template>
            </h2>
            <div v-if="showResultCount && !isRecycleBinMode" class="result-count-container">
              <span class="result-count">
                找到 {{ totalPhotos }} 张照片
              </span>
              <el-icon
                @click="clearSearch"
                class="result-refresh-btn"
              ><RefreshLeft /></el-icon>
            </div>
          </div>
          <div class="header-buttons">

          <el-button
            v-if="!isRecycleBinMode && !isMultiSelectMode"
            type="primary"
            @click="showUploadDialog = true"
          >
            <el-icon><UploadFilled /></el-icon>
            上传照片
          </el-button>

          <!-- 普通照片列表多选模式按钮组 -->
          <div v-if="!isRecycleBinMode && isMultiSelectMode" class="multi-select-buttons">
            <el-button @click="toggleSelectAll">
              {{ selectedPhotoIds.length === photos.length ? '取消全选' : '全选' }}
            </el-button>
            <el-button
              type="danger"
              @click="batchDeletePhotos"
              :disabled="selectedPhotoIds.length === 0">
              <el-icon><Delete /></el-icon>
              批量删除 ({{ selectedPhotoIds.length }})
            </el-button>
            <el-button
              type="warning"
              @click="toggleMultiSelectMode">
              取消
            </el-button>
          </div>

          <!-- 非多选模式且非回收站模式下的多选按钮 -->
          <el-button
            v-if="!isRecycleBinMode && !isMultiSelectMode && photos.length > 0"
            @click="toggleMultiSelectMode"
            type="success"
          >
            <el-icon><CircleCheck /></el-icon>
            多选
          </el-button>

          <el-button
            v-if="!isRecycleBinMode && isAdmin"
            @click="showPhotoLogs" >
            <el-icon><Document /></el-icon>
            查看日志
          </el-button>
          <el-button
            v-if="isRecycleBinMode"
            type="primary"
            @click="batchRestorePhotos"
            style="margin-right: 10px;"
          >
            <el-icon><RefreshLeft /></el-icon>
            恢复 ({{ selectedDeletedPhotoIds.length }})
          </el-button>
          <el-button
            v-if="isRecycleBinMode"
            type="danger"
            @click="batchPermanentDeletePhotos"
            style="margin-right: 10px;"
          >
            <el-icon><Delete /></el-icon>
            彻底删除 ({{ selectedDeletedPhotoIds.length }})
          </el-button>
          <el-button
            v-if="!isRecycleBinMode && isAdmin"
            @click="showRecycleBin"
            style="margin-right: 10px;"
          >
            <el-icon><Delete /></el-icon>
            回收站
          </el-button>
          <el-button
            v-if="isRecycleBinMode && isAdmin"
            @click="toggleSelectAllDeleted"
            style="margin-right: 10px;"
          >
            <el-icon><CircleCheck /></el-icon>
            {{ selectedDeletedPhotoIds.length === deletedPhotos.length ? '取消' : '全选' }}
          </el-button>
          <el-button
            v-if="isRecycleBinMode"
            @click="backToNormalList"
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
          :label="`${machine.model} ( ${machine.original_model} )`"
          :value="machine.id"
        />
      </el-select>
      <el-button type="primary" @click="searchByMachine">机器搜索</el-button>
    </div>

        <!-- 照片列表或回收站列表 -->

        <div v-if="!isRecycleBinMode && photos.length > 0" class="photo-grid">

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


        <!-- 回收站照片列表 -->
        <div v-if="isRecycleBinMode && deletedPhotos.length > 0" class="photo-grid">

          <div

        v-for="photo in deletedPhotos"

        :key="photo.id"

        class="photo-card deleted-photo"

        :class="{ 'selected': isDeletedPhotoSelected(photo.id) }"

        @click="toggleSelectDeletedPhoto(photo)"

      >

        <!-- 多选复选框（仅在回收站模式下显示） -->

        <div

          class="select-checkbox"

          @click.stop="toggleSelectDeletedPhoto(photo)"

        >

          <el-checkbox

            :model-value="isDeletedPhotoSelected(photo.id)"

            @click.stop="toggleSelectDeletedPhoto(photo)"

          />

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

          <!-- 已删除标识 -->

          <div class="photo-deleted-badge">

            已删除

          </div>

        </div>



        <div class="photo-info">



          <div class="photo-title">{{ photo.title }}</div>

          <div class="photo-upload-time">
            <div class="recycle-info">
              <div class="info-item">
                <span class="time-label">上传:</span> {{ photo.upload_time }}
              </div>
              <div class="info-item" v-if="photo.uploader">
                <span class="time-label">上传人:</span> {{ photo.uploader }}
              </div>
              <div class="info-item" v-if="photo.delete_time">
                <span class="time-label">删除:</span> {{ photo.delete_time }}
              </div>
              <div class="info-item" v-if="photo.delete_operator">
                <span class="time-label">删除人:</span> {{ photo.delete_operator }}
              </div>
            </div>
          </div>

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

        </div>

      </div>

        </div>

            <!-- 无搜索结果提示 -->
        <div v-else class="no-results" v-if="photos.length === 0">
          <el-empty
            :description="isRecycleBinMode ? (searchQuery ? '回收站中没有找到匹配的照片' : '回收站中暂无照片') : (searchQuery || selectedMachine ? '没有找到匹配的照片' : '暂无照片')"
            :image-size="100">
          </el-empty>
          <div v-if="searchQuery || selectedMachine || isRecycleBinMode" class="no-results-actions">
            <el-button v-if="isRecycleBinMode" type="primary" @click="backToNormalList">返回照片主页</el-button>
            <el-button v-else-if="searchQuery || selectedMachine" type="primary" @click="clearSearch">返回照片主页</el-button>
          </div>
        </div>
    <!-- 搜索结果统计和分页 -->
    <div class="result-info" v-if="!isRecycleBinMode && photos.length > 0 || isRecycleBinMode && deletedPhotos.length > 0">
      <div class="pagination">
        <el-pagination
          v-if="!isRecycleBinMode"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalPhotos"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
        <el-pagination
          v-else
          v-model:current-page="deletedCurrentPage"
          v-model:page-size="deletedPageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="deletedTotalPhotos"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleDeletedSizeChange"
          @current-change="handleDeletedCurrentChange"
        />
      </div>
    </div>

    <!-- 上传照片对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传照片" width="min(1080px, 98vw)" :before-close="handleUploadDialogClose" class="photo-upload-v2" destroy-on-close @close="resetPhotoUploadState">
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-position="top" class="pu-form">
        <div class="pu-layout">
          <section class="pu-card"><h2>选择照片文件</h2>
            <el-form-item prop="file" class="pu-file-field"><el-upload ref="uploadRef" drag multiple :auto-upload="false" :on-change="handleFileChange" :file-list="fileList" :show-file-list="true" :on-remove="handleFileRemove" accept=".png,.jpg,.jpeg,.webp" class="pu-upload">
              <el-icon class="pu-drop-icon"><UploadFilled /></el-icon><strong>拖放照片到此处，或点击选择</strong><span class="pu-muted">PNG / JPG / JPEG / WEBP · 支持多文件选择</span>
            </el-upload></el-form-item>
            <p class="pu-hint">单文件最大 50 MB · 文件匹配用于为不同照片批量填写资料</p>
            <button type="button" class="pu-btn pu-soft" :disabled="uploading" @click="showJsonInputDialog = true">▦ 多文件资料匹配</button>
          </section>
          <section class="pu-card"><h2>内容信息</h2>
            <el-form-item label="照片标题" prop="title"><el-input v-model="uploadForm.title" placeholder="请输入照片标题" /></el-form-item>
            <el-form-item label="关联机器" prop="machineId"><el-select v-model="uploadForm.machineId" placeholder="选择关联机器（可选）" clearable><el-option v-for="machine in machineList" :key="machine.id" :label="`${machine.model} (${machine.original_model})`" :value="machine.id" /></el-select></el-form-item>
            <el-form-item label="标签" prop="tags"><el-input-tag v-model="uploadFormTags" placeholder="多个标签用逗号分隔" delimiter="," /></el-form-item>
            <el-form-item label="备注"><el-input v-model="uploadForm.remark" type="textarea" :rows="4" placeholder="填写备注信息（可选）" /></el-form-item>
            <p class="pu-muted">普通上传按文件名生成标题；匹配上传仅上传已匹配的文件。</p>
          </section>
        </div>
        <el-progress v-if="uploading" :percentage="uploadProgress" class="pu-progress" />
        <div class="pu-footer"><div class="pu-muted">{{ fileList.length ? `已选择 ${fileList.length} 个文件` : '尚未选择文件' }}</div><div class="pu-small-actions"><button type="button" class="pu-btn" :disabled="uploading" @click="showUploadDialog = false">取消</button><button type="button" class="pu-btn pu-primary" :disabled="uploading" @click="submitUpload">{{ uploading ? '上传中…' : '上传照片' }}</button></div></div>
      </el-form>
    </el-dialog>

    <el-dialog v-model="showJsonInputDialog" title="多文件资料匹配" width="min(1080px, 98vw)" class="photo-upload-v2 photo-match-v2" append-to-body :close-on-click-modal="!uploading" :close-on-press-escape="!uploading" :show-close="!uploading">
      <div class="pu-form"><div class="pu-match-head"><div><span class="pu-pill">表格</span><p class="pu-muted">通过照片文件名批量关联标题、机器、标签与备注。</p></div></div>
        <div class="pu-match-body"><div class="pu-example"><strong>① 示例数据 <span class="pu-muted">可复制到 Excel 修改</span></strong><div class="pu-table-wrap"><table><thead><tr><th>照片文件名</th><th>照片标题</th><th>关联机器</th><th>标签</th><th>备注</th></tr></thead><tbody><tr v-for="file in fileList" :key="file.uid"><td>{{ file.name }}</td><td>{{ photoNameWithoutExtension(file.name) }}</td><td></td><td></td><td></td></tr><tr v-if="!fileList.length"><td colspan="5">请先选择照片文件</td></tr></tbody></table></div><button type="button" class="pu-btn pu-soft" :disabled="!fileList.length || uploading" @click="copyPhotoMatchExample">复制示例到 Excel</button><p class="pu-hint">已按所选文件填入完整文件名和默认标题，可在 Excel 中补充资料。</p></div>
          <div><strong>② 输入匹配信息</strong><el-input v-model="jsonInputText" type="textarea" :rows="7" :disabled="uploading" placeholder="粘贴从 Excel 复制的五列表格（包含表头）" /><p class="pu-hint">匹配结果只包含当前已选择的文件；未匹配文件不会随匹配上传。</p></div>
        </div>
        <div class="pu-footer"><span class="pu-muted">{{ fileList.length ? `已选择 ${fileList.length} 个文件` : '尚未选择文件' }}</span><div class="pu-actions"><button type="button" class="pu-btn" :disabled="uploading" @click="showJsonInputDialog = false">返回</button><button type="button" class="pu-btn pu-primary" :disabled="uploading || !fileList.length" @click="matchJsonToFiles">检查匹配</button></div></div>
      </div>
    </el-dialog>

    <el-dialog v-model="showMatchResultDialog" title="匹配结果" width="min(800px, 96vw)" class="photo-upload-v2 photo-match-result-v2" append-to-body :close-on-click-modal="!uploading" :close-on-press-escape="!uploading" :show-close="!uploading">
      <div class="pu-form"><div class="pu-result">已匹配 {{ matchedFiles.length }} 个文件，未匹配 {{ unmatchedFiles.length }} 个文件。</div>
        <div class="pu-table-wrap"><table><thead><tr><th>文件名</th><th>标题</th><th>状态</th></tr></thead><tbody><tr v-for="item in matchedFiles" :key="item.file.uid"><td>{{ item.file.name }}</td><td>{{ item.data.title }}</td><td>已匹配</td></tr><tr v-for="name in unmatchedFiles" :key="name"><td>{{ name }}</td><td>—</td><td>未匹配</td></tr></tbody></table></div>
        <p class="pu-hint">仅上传已匹配文件；未匹配文件不会上传。</p><el-progress v-if="uploading" :percentage="uploadProgress" class="pu-progress" />
        <div class="pu-footer"><span></span><div class="pu-actions"><button type="button" class="pu-btn" :disabled="uploading" @click="showMatchResultDialog = false">返回修改</button><button type="button" class="pu-btn pu-primary" :disabled="!isMatched || uploading" @click="uploadMatchedFiles">{{ uploading ? '上传中…' : '上传匹配文件' }}</button></div></div>
      </div>
    </el-dialog>

    <!-- 照片详情对话框 -->
    <el-dialog v-model="showDetailsDialog" width="min(1260px, 96vw)" :before-close="handleDialogClose" class="photo-detail-v2-dialog" destroy-on-close>
      <main v-if="selectedPhoto" class="v2-shell">
        <div class="v2-headline">
          <div class="v2-buttons">
            <button v-if="!isEditingAll" class="v2-btn" @click="startEditingAll">编辑信息</button>
            <template v-else><button class="v2-btn" :disabled="savingAll" @click="cancelEditingAll">取消</button><button class="v2-btn v2-primary" :disabled="savingAll" @click="saveAll">{{ savingAll ? '保存中…' : '保存' }}</button></template>
          </div>
        </div>
        <div class="v2-layout">
          <div class="v2-imagecard">
            <div class="v2-small">IMAGE PREVIEW / 缩略图</div>
            <img :src="`${apiBaseUrl}/assets/Media/Photos/${selectedPhoto.thumbnail_path}`" :alt="selectedPhoto.title" @error="onImageError" />
            <div class="v2-imagefoot">
              <div class="v2-file"><b>{{ photoFilename }}</b><div class="v2-small">{{ photoTechnicalInfo }}</div></div>
              <button v-if="selectedPhoto.original_path" class="v2-btn" @click="viewOriginalImage">↗ 打开原图</button>
            </div>
          </div>
          <div class="v2-side">
            <div class="v2-card">
              <h2>内容信息</h2>
              <div class="v2-meta"><div class="v2-fieldname">标题</div><div v-if="!isEditingAll" class="v2-fieldvalue">{{ selectedPhoto.title }}</div><input v-else v-model="editTitle" class="v2-editfield" aria-label="标题" /></div>
              <div v-if="selectedPhoto.machine_info" class="v2-meta"><div class="v2-fieldname">关联机器</div><div class="v2-fieldvalue">{{ selectedPhoto.machine_info.model }} ( {{ selectedPhoto.machine_info.original_model }} )</div></div>
              <div class="v2-meta"><div class="v2-fieldname">标签</div><div v-if="!isEditingAll"><span v-for="(tag, index) in currentTags" :key="index" class="v2-tag">{{ tag }}</span><span v-if="!currentTags.length" class="v2-fieldvalue">无标签</span></div><input v-else v-model="editTagsInput" class="v2-editfield" placeholder="多个标签用逗号分隔" aria-label="标签" /></div>
              <div class="v2-meta"><div class="v2-fieldname">备注</div><div v-if="!isEditingAll" class="v2-fieldvalue v2-note">{{ selectedPhoto.remark || '无备注' }}</div><textarea v-else v-model="editRemark" class="v2-editfield" aria-label="备注"></textarea></div>
            </div>
            <div class="v2-card">
              <h2>文件记录</h2>
              <div class="v2-person"><div class="v2-avatar">{{ (selectedPhoto.uploader || '未').slice(0, 1) }}</div><div><b>{{ selectedPhoto.uploader || '未知' }}</b><div class="v2-small">上传人</div></div></div>
              <div class="v2-fieldname v2-time">上传时间</div><div class="v2-fieldvalue">{{ formatDate(selectedPhoto.upload_time) }}</div>
              <div class="v2-fieldname v2-details">照片详情</div><div class="v2-fieldvalue">{{ photoTechnicalInfo }}</div>
            </div>
          </div>
        </div>
      </main>
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
import { UploadFilled, Delete, Document, Refresh, RefreshLeft, Search, CircleCheck, Back } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import CommonHeader from '@/components/CommonHeader.vue';
import CommonLogDialog from '@/components/CommonLogDialog.vue';
import { uploadFile } from '@/utils/upload';
import { getCurrentUserRole } from '@/utils/authUtils';
import request, { getMachinesForPhotos, createPhoto, updatePhoto, deletePhoto as deletePhotoAPI, getDeletedPhotos, restorePhoto as restorePhotoAPI, permanentDeletePhotos as permanentDeletePhotosAPI } from '@/utils/request';
import { parseJsonToFiles } from '@/utils/excel-parse';

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
const showMatchResultDialog = ref(false);
const jsonInputText = ref('');
// JSON匹配相关状态
const matchedFiles = ref<any[]>([]);
const unmatchedFiles = ref<string[]>([]);
const isMatched = ref(false); // 是否已匹配成功

// 多选相关状态
const isMultiSelectMode = ref(false); // 是否处于多选模式
const selectedPhotoIds = ref<number[]>([]); // 选中的照片ID列表

// 回收站相关状态
const isRecycleBinMode = ref(false); // 是否处于回收站模式
const deletedPhotos = ref<any[]>([]); // 回收站中的照片
const deletedCurrentPage = ref(1);
const deletedPageSize = ref(10);
const deletedTotalPhotos = ref(0);
const selectedDeletedPhotoIds = ref<number[]>([]); // 选中回收站中的照片ID列表

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
    // 在生产环境中，如果VITE_API_BASE_URL不是相对路径，则使用window.location.origin
    if (import.meta.env.MODE === 'production') {
      // 检查VITE_API_BASE_URL是否为完整的URL
      if (import.meta.env.VITE_API_BASE_URL.startsWith('http')) {
        // 如果是完整URL，返回当前页面的origin，以确保静态资源访问使用当前域名
        return window.location.origin;
      } else {
        // 如果是相对路径或以/开头的路径，直接返回
        return import.meta.env.VITE_API_BASE_URL;
      }
    }
    // 开发环境中继续使用环境变量
    return import.meta.env.VITE_API_BASE_URL;
  }
  // 如果没有设置环境变量，返回当前页面的origin
  return window.location.origin;
});

// 权限相关
const isAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'admin';
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
        // 使用每个文件自己的文件名作为标题（去掉扩展名）
        const fileName = fileItem.name.replace(/\.\w+$/, '');
        formData.append('title', fileName);
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

const resetPhotoUploadState = () => {
  showMatchResultDialog.value = false;
  showJsonInputDialog.value = false;
  resetUploadForm();
  resetMatchState();
  inputValueString.value = '';
  uploadFormRef.value?.clearValidate();
};

// JSON匹配多文件相关函数（核心修复：换行符兼容）
const matchJsonToFiles = () => {
  try {
    const result = parseJsonToFiles(jsonInputText.value, fileList.value);

    // 更新匹配结果
    matchedFiles.value = result.matchedFiles;
    unmatchedFiles.value = result.unmatchedFiles;
    isMatched.value = result.isMatched;
    showMatchResultDialog.value = true;

    // 提示信息
    if (result.unmatchedFiles.length > 0) {
      ElMessage.warning(`以下文件未找到匹配数据: ${result.unmatchedFiles.join(', ')}`);
    }

    if (result.matchedFiles.length === 0) {
      ElMessage.warning('没有找到匹配的文件');
      isMatched.value = false;
    } else {
      ElMessage.success(`匹配成功: ${result.matchedFiles.length} 个文件已匹配`);
    }
  } catch (error: any) {
    console.error('匹配JSON数据失败:', error);
    ElMessage.error(error.message || '解析JSON数据失败，请检查格式');
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

const photoNameWithoutExtension = (name: string) => {
  const dot = name.lastIndexOf('.');
  return dot > 0 ? name.slice(0, dot) : name;
};
const copyPhotoMatchExample = async () => {
  if (!fileList.value.length) return;
  if (fileList.value.some(file => /[\t\r\n]/.test(file.name))) {
    ElMessage.error('文件名包含制表符或换行，无法复制为 Excel 表格');
    return;
  }
  const rows = [
    ['照片文件名', '照片标题', '关联机器', '标签', '备注'],
    ...fileList.value.map(file => [file.name, photoNameWithoutExtension(file.name), '', '', '']),
  ];
  const text = rows.map(row => row.join('\t')).join('\n');
  let copied = false;
  if (navigator.clipboard?.writeText) {
    try { await navigator.clipboard.writeText(text); copied = true; } catch { /* 使用兼容方式重试 */ }
  }
  if (!copied) {
    const input = document.createElement('textarea');
    input.value = text;
    input.setAttribute('readonly', '');
    input.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
    (document.querySelector('.photo-match-v2') || document.body).appendChild(input);
    try {
      input.focus();
      input.select();
      copied = document.execCommand('copy');
    } catch { copied = false; }
    finally { input.remove(); }
  }
  if (copied) ElMessage.success('已复制所选照片，可粘贴到 Excel');
  else ElMessage.error('复制失败，请检查浏览器是否允许复制');
};
watch([jsonInputText, fileList], () => { isMatched.value = false; matchedFiles.value = []; unmatchedFiles.value = []; }, { deep: true });

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
    showMatchResultDialog.value = false;
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

const photoFilename = computed(() => (selectedPhoto.value?.original_path || selectedPhoto.value?.normal_path || selectedPhoto.value?.thumbnail_path || '').split('/').pop() || '照片');
const photoTechnicalInfo = computed(() => {
  const photo = selectedPhoto.value;
  if (!photo) return '';
  const extension = photoFilename.value.includes('.') ? photoFilename.value.split('.').pop()?.toUpperCase() : '';
  const dimensions = photo.original_width && photo.original_height ? `${photo.original_width} × ${photo.original_height}` : '';
  return [extension, dimensions, photo.file_size != null ? formatFileSize(photo.file_size) : ''].filter(Boolean).join(' / ');
});

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

// 开始编辑所有信息
const startEditingAll = () => {
  editTitle.value = selectedPhoto.value?.title || '';
  editRemark.value = selectedPhoto.value?.remark || '';
  const tagsString = selectedPhoto.value?.tags || '';
  currentTags.value = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
  isEditingAll.value = true;
  editTagsInput.value = currentTags.value.join(',');
};

// 保存所有更改
const saveAll = async () => {
  if (!selectedPhoto.value) return;

  const originalTags = selectedPhoto.value.tags || '';
  const initialTagsInput = originalTags.split(',').map((tag: string) => tag.trim()).filter(Boolean).join(',');
  const tagsChanged = editTagsInput.value !== initialTagsInput;
  if (editTitle.value === (selectedPhoto.value.title || '') &&
      editRemark.value === (selectedPhoto.value.remark || '') && !tagsChanged) {
    isEditingAll.value = false;
    return;
  }

  savingAll.value = true;
  try {
    const tagsString = tagsChanged
      ? [...new Set(editTagsInput.value.split(/[,，]/).map(tag => tag.trim()).filter(Boolean))].join(',')
      : originalTags;
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

    currentTags.value = tagsString ? tagsString.split(',') : [];
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


// 显示回收站
const showRecycleBin = async () => {
  isRecycleBinMode.value = true;
  await fetchDeletedPhotos();
};

// 获取回收站中的照片
const fetchDeletedPhotos = async () => {
  try {
    const response = await getDeletedPhotos({
      page: deletedCurrentPage.value,
      per_page: deletedPageSize.value,
    });

    // request.ts 自动解包了 response，这里 response 就是解包后的 data 部分
    deletedPhotos.value = response.photos || [];
    deletedTotalPhotos.value = response.total || 0;
  } catch (error) {
    console.error('获取回收站照片失败:', error);
    ElMessage.error('获取回收站照片失败');
  }
};

// 从回收站恢复照片
const restorePhoto = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要恢复这张照片吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    const response = await restorePhotoAPI(id);
    ElMessage.success(response.message || '照片恢复成功');
    // 如果当前在回收站页面，刷新回收站列表；否则刷新正常列表
    if (isRecycleBinMode.value) {
      await fetchDeletedPhotos();
    } else {
      await fetchPhotos();
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复照片失败:', error);
      ElMessage.error('恢复失败');
    }
  }
};

// 永久删除照片（从回收站彻底删除）
const permanentDeletePhoto = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要永久删除这张照片吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await permanentDeletePhotosAPI([id]);
    ElMessage.success('照片已永久删除');
    await fetchDeletedPhotos(); // 刷新回收站列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('永久删除照片失败:', error);
      ElMessage.error('永久删除失败');
    }
  }
};

// 批量从回收站恢复照片
const batchRestorePhotos = async () => {
  if (selectedDeletedPhotoIds.value.length === 0) {
    ElMessage.warning('请先选择要恢复的照片');
    return;
  }

  try {
    await ElMessageBox.confirm(`确定要恢复选中的 ${selectedDeletedPhotoIds.value.length} 张照片吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // 批量恢复照片（暂时逐个恢复，因为API可能不支持批量恢复）
    let successCount = 0;
    let errorCount = 0;

    for (const photoId of selectedDeletedPhotoIds.value) {
      try {
        await restorePhotoAPI(photoId);
        successCount++;
      } catch (error) {
        console.error(`恢复照片 ${photoId} 失败:`, error);
        errorCount++;
      }
    }

    if (errorCount > 0) {
      ElMessage.warning(`批量恢复完成: ${successCount} 个成功, ${errorCount} 个失败`);
    } else {
      ElMessage.success(`成功恢复 ${successCount} 张照片`);
    }

    // 重置选择状态并刷新列表
    selectedDeletedPhotoIds.value = [];
    await fetchDeletedPhotos();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量恢复照片失败:', error);
      ElMessage.error('批量恢复失败');
    }
  }
};

// 批量永久删除照片
const batchPermanentDeletePhotos = async () => {
  if (selectedDeletedPhotoIds.value.length === 0) {
    ElMessage.warning('请先选择要永久删除的照片');
    return;
  }

  try {
    await ElMessageBox.confirm(`确定要永久删除选中的 ${selectedDeletedPhotoIds.value.length} 张照片吗？此操作不可恢复！`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    const response = await permanentDeletePhotosAPI(selectedDeletedPhotoIds.value);
    ElMessage.success(response.message || `成功永久删除 ${selectedDeletedPhotoIds.value.length} 张照片`);

    // 重置选择状态并刷新列表
    selectedDeletedPhotoIds.value = [];
    await fetchDeletedPhotos();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量永久删除照片失败:', error);
      ElMessage.error('批量永久删除失败');
    }
  }
};


// 返回正常照片列表
const backToNormalList = () => {
  isRecycleBinMode.value = false;
  fetchPhotos(); // 刷新正常照片列表
};

// 检查回收站中的照片是否被选中
const isDeletedPhotoSelected = (photoId: number) => {
  return selectedDeletedPhotoIds.value.includes(photoId);
};

// 选择回收站中的单个照片
const selectDeletedPhoto = (photoId: number) => {
  const index = selectedDeletedPhotoIds.value.indexOf(photoId);
  if (index > -1) {
    // 已选中，取消选择
    selectedDeletedPhotoIds.value.splice(index, 1);
  } else {
    // 未选中，添加选择
    selectedDeletedPhotoIds.value.push(photoId);
  }
};

// 全选/取消全选回收站中的照片
const toggleSelectAllDeleted = () => {
  if (selectedDeletedPhotoIds.value.length === deletedPhotos.value.length) {
    // 当前已全选，取消全选
    selectedDeletedPhotoIds.value = [];
  } else {
    // 未全选，进行全选
    selectedDeletedPhotoIds.value = deletedPhotos.value.map(photo => photo.id);
  }
};

// 切换回收站中照片的选择状态
const toggleSelectDeletedPhoto = (photo: any) => {
  const index = selectedDeletedPhotoIds.value.indexOf(photo.id);
  if (index > -1) {
    // 已选中，取消选择
    selectedDeletedPhotoIds.value.splice(index, 1);
  } else {
    // 未选中，添加选择
    selectedDeletedPhotoIds.value.push(photo.id);
  }
};

// 回收站分页处理
const handleDeletedSizeChange = (size: number) => {
  deletedPageSize.value = size;
  deletedCurrentPage.value = 1;
  fetchDeletedPhotos();
};

const handleDeletedCurrentChange = (page: number) => {
  deletedCurrentPage.value = page;
  fetchDeletedPhotos();
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
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 20px;
}

.deleted-photo {
  opacity: 0.7;
  border-color: #f56c6c;
}

.photo-deleted-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: rgba(245, 108, 108, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  z-index: 5;
}

.restore-delete-btns {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 5px;
  z-index: 10;
}

.photo-delete-time {
  font-size: 11px;
  color: #e6a23c;
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

:global(.photo-detail-v2-dialog.el-dialog){--el-dialog-padding-primary:0;padding:0;background:#f8f7f3;border-radius:12px;height:94vh;max-height:94vh;overflow:hidden;margin-top:3vh!important;color:#242a30;font-family:Inter,"Microsoft YaHei",system-ui,sans-serif}
:global(.photo-detail-v2-dialog .el-dialog__body){height:100%;overflow-y:auto;overflow-x:hidden}
:global(.photo-detail-v2-dialog .el-dialog__header){padding:0;margin:0}:global(.photo-detail-v2-dialog .el-dialog__headerbtn){z-index:2;top:10px;right:10px}
.v2-shell,.v2-shell *{box-sizing:border-box}.v2-shell{max-width:1260px;min-height:100%;margin:0 auto;padding:20px 30px 28px;color:#242a30;display:flex;flex-direction:column}
.v2-shell button,.v2-shell input,.v2-shell textarea{font:inherit}.v2-shell button{cursor:pointer}.v2-shell button:focus-visible,.v2-shell input:focus-visible,.v2-shell textarea:focus-visible{outline:2px solid #4285ef;outline-offset:2px}
.v2-btn{border:1px solid #d7dce4;background:#fff;color:#273344;border-radius:12px;padding:10px 16px;font-weight:600}.v2-btn:disabled{opacity:.6;cursor:not-allowed}.v2-primary{background:#243d34;color:#fff;border-color:#243d34}
.v2-headline{display:flex;justify-content:flex-end;align-items:center;flex:none;min-height:44px;margin:0 48px 16px 0}.v2-buttons{display:flex;gap:9px;flex-wrap:nowrap}
.v2-layout{display:grid;grid-template-columns:1.25fr .75fr;gap:20px;flex:1;align-items:stretch}.v2-imagecard{background:#e4e9e8;border-radius:26px;padding:25px;min-height:620px;display:flex;flex-direction:column;justify-content:space-between;min-width:0}.v2-imagecard img{display:block;width:100%;height:460px;object-fit:contain;border-radius:16px}.v2-imagefoot{display:flex;justify-content:space-between;align-items:center;gap:15px}.v2-file{min-width:0;overflow-wrap:anywhere}
.v2-small{font-size:12px;color:#66717c}.v2-side{display:grid;grid-template-rows:minmax(390px,auto) auto;gap:17px;min-width:0}.v2-card{background:white;border:1px solid #eae7e0;border-radius:22px;padding:26px;min-width:0}.v2-card h2{margin:0 0 20px;font-size:18px;line-height:normal}.v2-meta{padding:12px 0;border-bottom:1px solid #f0f0ef}.v2-meta:last-child{border-bottom:0}
.v2-fieldname{color:#8792a2;font-size:12px;margin-bottom:7px}.v2-fieldvalue{color:#263344;font-size:14px;line-height:1.6;overflow-wrap:anywhere}.v2-note{white-space:pre-wrap}.v2-tag{display:inline-flex;background:#eaf1ff;color:#2c60aa;padding:5px 10px;border-radius:7px;margin:3px 5px 3px 0;font-size:13px;overflow-wrap:anywhere;max-width:100%}
.v2-editfield{width:100%;padding:9px 11px;border:1px solid #ccd4df;border-radius:9px;background:white;color:#233044}.v2-shell textarea.v2-editfield{height:100px;min-height:100px;max-height:100px;resize:none;overflow:auto}.v2-person{display:flex;align-items:center;gap:12px}.v2-avatar{background:#dfecdd;border-radius:50%;width:42px;height:42px;display:grid;place-items:center;color:#3e6d55;font-weight:700}.v2-time{margin-top:22px}.v2-details{margin-top:16px}
@media(max-width:900px){.v2-layout{grid-template-columns:1fr}.v2-imagecard{min-height:450px}.v2-imagecard img{height:320px}.v2-side{grid-template-rows:minmax(390px,auto) auto}.v2-shell{padding:12px 14px 20px}.v2-card{padding:16px}}

:global(.photo-upload-v2.el-dialog){--el-dialog-padding-primary:0;padding:26px 30px;background:#faf9f6;border-radius:17px;max-height:94vh;overflow-y:auto;margin-top:3vh!important;color:#263138;font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}
:global(.photo-upload-v2 .el-dialog__header){padding:0;margin:0 0 20px}:global(.photo-upload-v2 .el-dialog__title){font-size:23px;font-weight:700;color:#263138}:global(.photo-upload-v2 .el-dialog__headerbtn){top:18px;right:18px}
.pu-form,.pu-form *{box-sizing:border-box}.pu-layout{display:grid;grid-template-columns:1.05fr .95fr;gap:18px;align-items:start}.pu-card{border:1px solid #e7e5de;background:#fff;border-radius:21px;padding:22px;min-width:0}.pu-card h2,.pu-match h2{font-size:17px;margin:0 0 16px;color:#263138;line-height:normal}.pu-form :deep(.el-form-item){margin-bottom:15px}.pu-form :deep(.el-form-item__label){font-size:12px;color:#748390;line-height:1.4;margin-bottom:6px;padding:0}.pu-form :deep(.el-select),.pu-form :deep(.el-input-tag){width:100%}.pu-form :deep(.el-input__wrapper),.pu-form :deep(.el-select__wrapper),.pu-form :deep(.el-input-tag__wrapper){min-height:40px;border-radius:9px}.pu-form :deep(.el-textarea__inner){border-radius:9px;min-height:100px!important}.pu-file-field :deep(.el-form-item__content){display:block}.pu-upload{width:100%}.pu-upload :deep(.el-upload){width:100%;display:block}.pu-upload :deep(.el-upload-dragger){width:100%;min-height:190px;border:2px dashed #b7c8c3;background:#e5eae9;border-radius:17px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;padding:16px;color:#263138}.pu-upload :deep(.el-upload-dragger:hover){background:#dceae5;border-color:#31735d}.pu-upload :deep(.el-upload-list){max-height:150px;overflow:auto}.pu-drop-icon{font-size:36px;color:#416e5c}.pu-muted,.pu-hint{font-size:12px;color:#7b8990;line-height:1.5}.pu-hint{margin:12px 0}.pu-btn{border:1px solid #d4dfe2;background:white;border-radius:10px;padding:9px 15px;color:#34434d;cursor:pointer;font:inherit}.pu-btn:disabled{opacity:.45;cursor:not-allowed}.pu-btn.pu-primary{background:#213e33;border-color:#213e33;color:white}.pu-btn.pu-soft{background:#eef4f1;color:#245b47;border-color:#d4e5db}.pu-footer{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:19px}.pu-actions,.pu-small-actions{display:flex;gap:10px;flex-wrap:wrap}.pu-progress{margin-top:15px}
@media(max-width:800px){.pu-layout{grid-template-columns:1fr}:global(.photo-upload-v2.el-dialog){padding:20px}}

.pu-match{margin-top:18px;background:#fff;border:1px solid #e7e5de;border-radius:21px;padding:23px}.pu-match-head{display:flex;justify-content:space-between;align-items:center;gap:12px}.pu-match-head h2{margin:0}.pu-match-head p{margin:5px 0 0}.pu-pill{font-size:11px;border-radius:99px;padding:3px 8px;background:#e9f1ec;color:#39715a}.pu-match-body{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:18px}.pu-example{background:#f5f7f5;border:1px solid #e3eae5;border-radius:14px;padding:15px;min-width:0}.pu-table-wrap{overflow:auto;border:1px solid #e1e6e2;border-radius:9px;background:white;margin:12px 0}.pu-table-wrap table{width:100%;border-collapse:collapse;white-space:nowrap;font-size:12px}.pu-table-wrap th,.pu-table-wrap td{padding:9px 11px;text-align:left;border-bottom:1px solid #e9eeea}.pu-table-wrap th{background:#edf2ef;color:#53685d}.pu-match-body :deep(.el-textarea){margin-top:9px}.pu-match-body :deep(.el-textarea__inner){min-height:175px!important;font:12px/1.6 ui-monospace,Consolas,monospace}.pu-small-actions{margin-top:12px}.pu-result{margin-top:13px;border-radius:10px;background:#f0f5f2;padding:11px 13px;color:#375b4d;font-size:12px}@media(max-width:800px){.pu-match-body{grid-template-columns:1fr}.pu-match-head{align-items:flex-start;flex-direction:column}}
</style>