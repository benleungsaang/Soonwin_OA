<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="700px"
    :close-on-click-modal="true"
    destroy-on-close
    :before-close="handleBeforeClose"
  >
    <!-- 拖放区域 -->
    <div
      class="create-dialog-body"
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop.prevent="handleDrop"
    >
      <!-- 内容输入 -->
      <el-input
        v-model="content"
        type="textarea"
        :rows="5"
        placeholder="分享你的想法...（支持 Ctrl+V 粘贴图片/视频）"
        maxlength="5000"
        show-word-limit
        @paste="handlePaste"
      />

      <!-- 媒体预览区（新选择的文件） -->
      <div v-if="mediaPreviews.length > 0" class="media-preview-area">
        <div v-for="(item, index) in mediaPreviews" :key="'new-'+index" class="preview-item">
          <img v-if="item.type === 'image'" :src="item.url" alt="" />
          <video v-else-if="item.type === 'video'" :src="item.url" controls />
          <div class="preview-badge">{{ item.type === 'video' ? '视频' : '图片' }}</div>
          <el-button class="preview-remove-btn" type="danger" size="small" circle
            @click="removeMedia(index)">×</el-button>
        </div>
      </div>

      <!-- 已有媒体（编辑模式 - 保留/删除切换） -->
      <div v-if="isEdit && existingMedia.length > 0" class="existing-media-area">
        <div class="section-label">已有附件（点击 × 移除，点击 ↩ 恢复）：</div>
        <div class="media-preview-area">
          <div v-for="item in existingMedia" :key="item.id" class="preview-item"
               :class="{ removed: !item.keep }">
            <img v-if="item.media_type === 'image'"
                 :src="getMediaUrl(item.thumbnail_path || item.file_path)" alt="" />
            <video v-else :src="getMediaUrl(item.file_path)" />
            <el-button class="preview-remove-btn"
              :type="item.keep ? 'danger' : 'primary'" size="small" circle
              @click="toggleKeepExisting(item)">
              {{ item.keep ? '×' : '↩' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 拖放提示 -->
      <div v-if="dragOver" class="drop-overlay">
        <el-icon :size="36"><UploadFilled /></el-icon>
        <span>释放以添加文件</span>
      </div>

      <!-- 文件选择按钮 -->
      <div class="upload-actions">
        <input
          ref="fileInputRef"
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/gif,image/webp,video/mp4,video/avi,video/mov,video/mkv,video/wmv"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />
        <el-button type="primary" plain @click="($refs.fileInputRef as HTMLInputElement).click()">
          <el-icon><PictureFilled /></el-icon> 多媒体
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button v-if="isDraft" @click="handleSaveCurrentDraft" :loading="saving">保存</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="saving">
          {{ submitBtnText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { PictureFilled, UploadFilled } from '@element-plus/icons-vue'
import type { BlogPost, BlogMedia } from '@/types/blog'
import { getMediaUrl } from '@/api/blog'

interface MediaPreview {
  type: 'image' | 'video'
  url: string
  file: File
}

interface ExistingMediaItem extends BlogMedia {
  keep: boolean
}

const props = defineProps<{
  visible: boolean
  post?: BlogPost | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
  (e: 'draft-saved'): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => {
    if (!val) {
      // 关闭由 before-close 统一处理，这里直接同步
      forceClose()
    } else {
      emit('update:visible', val)
    }
  },
})

const isEdit = computed(() => !!props.post)
const isDraft = computed(() => props.post?.is_draft === true)

const dialogTitle = computed(() => {
  if (isDraft.value) return '编辑草稿'
  if (isEdit.value) return '编辑博文'
  return '发布博文'
})

const submitBtnText = computed(() => {
  if (isDraft.value) return '发布'
  if (isEdit.value) return '保存修改'
  return '发布'
})

const content = ref('')
const mediaPreviews = ref<MediaPreview[]>([])
const existingMedia = ref<ExistingMediaItem[]>([])
const saving = ref(false)
const dragOver = ref(false)

// 初始化数据
watch(() => props.visible, (val) => {
  if (val) {
    content.value = props.post?.content || ''
    mediaPreviews.value = []
    existingMedia.value = (props.post?.media || []).map(m => ({ ...m, keep: true }))
  }
})

// 检查是否有未保存内容
function hasContent(): boolean {
  return !!content.value.trim() || mediaPreviews.value.length > 0
}

// 尝试关闭（弹窗确认保存草稿）
function tryCloseDialog() {
  if (hasContent()) {
    const confirmText = isDraft.value ? '是否保存当前草稿的修改？' : '当前编辑内容尚未保存，是否保存为草稿？'
    ElMessageBox.confirm(
      confirmText,
      '提示',
      { confirmButtonText: '保存', cancelButtonText: '不保存', type: 'warning',
        distinguishCancelAndClose: true, closeOnClickModal: false }
    ).then(() => {
      // 编辑草稿时 → 更新原草稿；新发布时 → 创建新草稿
      if (isDraft.value) {
        handleSaveCurrentDraftThenClose()
      } else {
        handleSaveDraftThenClose()
      }
    }).catch((action: string) => {
      if (action === 'cancel') {
        forceClose()
      }
    })
  } else {
    forceClose()
  }
}

async function handleBeforeClose(done: () => void) {
  if (hasContent()) {
    const confirmText = isDraft.value ? '是否保存当前草稿的修改？' : '当前编辑内容尚未保存，是否保存为草稿？'
    try {
      await ElMessageBox.confirm(
        confirmText,
        '提示',
        { confirmButtonText: '保存', cancelButtonText: '不保存', type: 'warning',
          distinguishCancelAndClose: true }
      )
      if (isDraft.value) {
        await handleSaveCurrentDraftThenClose()
      } else {
        await handleSaveDraftThenClose()
      }
      done()
    } catch (action: any) {
      if (action === 'cancel') {
        done()
      }
    }
  } else {
    done()
  }
}

function forceClose() {
  cleanupPreviews()
  content.value = ''
  existingMedia.value = []
  emit('update:visible', false)
}

function cleanupPreviews() {
  mediaPreviews.value.forEach(item => URL.revokeObjectURL(item.url))
  mediaPreviews.value = []
}

// ========== 文件处理 ==========

function addFiles(files: FileList | File[]) {
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) continue
    const url = URL.createObjectURL(file)
    mediaPreviews.value.push({
      type: file.type.startsWith('video/') ? 'video' : 'image',
      url,
      file,
    })
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) addFiles(input.files)
  input.value = ''
}

function handleDrop(e: DragEvent) {
  dragOver.value = false
  if (e.dataTransfer?.files) addFiles(e.dataTransfer.files)
}

function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  const files: File[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.startsWith('image/') || item.type.startsWith('video/')) {
      const file = item.getAsFile()
      if (file) files.push(file)
    }
  }
  if (files.length > 0) {
    e.preventDefault()
    addFiles(files)
  }
}

function removeMedia(index: number) {
  URL.revokeObjectURL(mediaPreviews.value[index].url)
  mediaPreviews.value.splice(index, 1)
}

function toggleKeepExisting(item: ExistingMediaItem) {
  item.keep = !item.keep
}

// ========== 提交 ==========

function buildFormData(): FormData {
  const formData = new FormData()
  formData.append('content', content.value)
  mediaPreviews.value.forEach(item => formData.append('media', item.file))
  if (isEdit.value) {
    const keepIds = existingMedia.value.filter(m => m.keep).map(m => m.id).join(',')
    formData.append('keep_media_ids', keepIds)
  }
  return formData
}

async function handleSubmit() {
  if (!content.value.trim() && mediaPreviews.value.length === 0
      && existingMedia.value.filter(m => m.keep).length === 0) {
    ElMessage.warning('请输入内容或添加媒体文件')
    return
  }
  saving.value = true
  try {
    const { createPost, updatePost, publishDraft } = await import('@/api/blog')
    const formData = buildFormData()

    if (isDraft.value && props.post) {
      // 编辑草稿 → 先更新再发布
      await updatePost(props.post.id, formData)
      await publishDraft(props.post.id)
      ElMessage.success('草稿已发布')
    } else if (isEdit.value && props.post) {
      await updatePost(props.post.id, formData)
      ElMessage.success('博文已更新')
    } else {
      await createPost(formData)
      ElMessage.success('博文已发布')
    }
    emit('saved')
    forceClose()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleSaveDraftThenClose() {
  saving.value = true
  try {
    const { saveDraft } = await import('@/api/blog')
    const formData = new FormData()
    formData.append('content', content.value)
    mediaPreviews.value.forEach(item => formData.append('media', item.file))
    await saveDraft(formData)
    ElMessage.success('草稿已保存')
    emit('draft-saved')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '保存草稿失败')
  } finally {
    saving.value = false
    forceClose()
  }
}

// 保存当前草稿（更新原草稿，不新建）
async function handleSaveCurrentDraft() {
  if (!props.post) return
  saving.value = true
  try {
    const { updatePost } = await import('@/api/blog')
    const formData = buildFormData()
    await updatePost(props.post.id, formData)
    ElMessage.success('草稿已保存')
    emit('saved')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleSaveCurrentDraftThenClose() {
  if (!props.post) {
    forceClose()
    return
  }
  saving.value = true
  try {
    const { updatePost } = await import('@/api/blog')
    const formData = buildFormData()
    await updatePost(props.post.id, formData)
    ElMessage.success('草稿已保存')
    emit('draft-saved')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
    forceClose()
  }
}
</script>

<style scoped>
.create-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  min-height: 120px;
}

.drop-overlay {
  position: absolute;
  inset: 0;
  background: rgba(64, 158, 255, 0.08);
  border: 2px dashed #409eff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #409eff;
  font-size: 15px;
  z-index: 10;
  pointer-events: none;
}

.media-preview-area {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.preview-item {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}

.preview-item img,
.preview-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-item.removed {
  opacity: 0.35;
}

.preview-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 11px;
  padding: 0 6px;
  border-radius: 3px;
}

.preview-remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  min-width: 20px;
  font-size: 12px;
}

.section-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.existing-media-area {
  margin-top: 4px;
}

.upload-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
