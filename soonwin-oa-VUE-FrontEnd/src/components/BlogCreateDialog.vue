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
        ref="contentInputRef"
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
        <div v-for="(item, index) in mediaPreviews" :key="'new-'+index" class="preview-item"
             :class="{ uploading: !item.uploadDone && item.uploadProgress > 0 }">
          <img v-if="item.type === 'image'" :src="item.url" alt="" />
          <video v-else-if="item.type === 'video'" :src="item.url" controls />
          <div class="preview-badge">{{ item.type === 'video' ? '视频' : '图片' }}</div>
          <!-- 上传进度条 -->
          <div v-if="!item.uploadDone && item.uploadProgress > 0" class="upload-progress-bar">
            <div class="upload-progress-fill" :style="{ width: item.uploadProgress + '%' }"></div>
            <span class="upload-progress-text">{{ item.uploadProgress }}%</span>
          </div>
          <el-button v-if="!item.uploadDone || item.uploadProgress === 0"
            class="preview-remove-btn" type="danger" size="small" circle
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
        <label class="publish-upload-btn">
          <el-icon :size="16"><PictureFilled /></el-icon>
          <span>多媒体</span>
          <input
            type="file"
            accept="image/png,image/jpeg,image/jpg,image/gif,image/webp,video/mp4,video/avi,video/mov,video/mkv,video/wmv"
            multiple
            hidden
            @change="handleFileSelect"
          />
        </label>
        <button class="publish-emoji-btn" @click="emojiPickerVisible = !emojiPickerVisible">
          🙂
        </button>
        <div ref="emojiWrapperRef" class="emoji-wrapper">
          <emoji-picker
            v-if="emojiPickerVisible"
            class="emoji-picker"
            @emoji-click="handleEmojiClick"
          />
        </div>
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
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { PictureFilled, UploadFilled } from '@element-plus/icons-vue'
import 'emoji-picker-element'
import type { BlogPost, BlogMedia } from '@/types/blog'
import { getMediaUrl } from '@/api/blog'

interface MediaPreview {
  type: 'image' | 'video'
  url: string
  file: File
  uploadProgress: number  // 0-100，单文件上传进度
  uploadDone: boolean      // 是否已上传完成
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
const contentInputRef = ref<any>(null)
const emojiPickerVisible = ref(false)
const emojiWrapperRef = ref<HTMLElement | null>(null)
const mediaPreviews = ref<MediaPreview[]>([])
const existingMedia = ref<ExistingMediaItem[]>([])
const saving = ref(false)
const dragOver = ref(false)

// 缓存已上传文件的元数据（用于提交失败后重试时复用，避免重复上传）
const cachedUploadedMedia = ref<import('@/api/blog').UploadedMediaInfo[]>([])

// 点击 emoji 面板外部时关闭
function onEmojiOutsideClick(e: MouseEvent) {
  if (!emojiPickerVisible.value) return
  const target = e.target as HTMLElement
  if (emojiWrapperRef.value?.contains(target)) return
  if (target.closest('.publish-emoji-btn')) return
  emojiPickerVisible.value = false
}
onMounted(() => document.addEventListener('mousedown', onEmojiOutsideClick))
onUnmounted(() => document.removeEventListener('mousedown', onEmojiOutsideClick))

// 初始化数据
watch(() => props.visible, (val) => {
  if (val) {
    content.value = props.post?.content || ''
    mediaPreviews.value = []
    existingMedia.value = (props.post?.media || []).map(m => ({ ...m, keep: true }))
    cachedUploadedMedia.value = []
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
  cachedUploadedMedia.value = []
  emit('update:visible', false)
}

function cleanupPreviews() {
  mediaPreviews.value.forEach(item => URL.revokeObjectURL(item.url))
  mediaPreviews.value = []
}

// ========== 文件处理 ==========

function addFiles(files: FileList | File[]) {
  cachedUploadedMedia.value = []  // 新文件加入，缓存失效
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) continue
    const url = URL.createObjectURL(file)
    mediaPreviews.value.push({
      type: file.type.startsWith('video/') ? 'video' : 'image',
      url,
      file,
      uploadProgress: 0,
      uploadDone: false,
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
  cachedUploadedMedia.value = []  // 文件变更，缓存失效
  URL.revokeObjectURL(mediaPreviews.value[index].url)
  mediaPreviews.value.splice(index, 1)
}

function toggleKeepExisting(item: ExistingMediaItem) {
  item.keep = !item.keep
  cachedUploadedMedia.value = []  // 媒体集合变更，缓存失效
}

// ========== Emoji ==========

function handleEmojiClick(event: any) {
  const emoji: string = event.detail.emoji.unicode
  const textarea = contentInputRef.value?.$el?.querySelector('textarea')
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    content.value =
      content.value.substring(0, start) + emoji + content.value.substring(end)
    nextTick(() => {
      const pos = start + emoji.length
      textarea.setSelectionRange(pos, pos)
      textarea.focus()
    })
  } else {
    content.value += emoji
  }
  emojiPickerVisible.value = false
}

// ========== 两阶段上传 ==========

/**
 * 阶段一：逐个上传文件（每个文件独立请求、独立超时、独立进度）
 *
 * 这是根治超时误报的核心逻辑：
 * - 旧方案：所有文件塞进一个 FormData → 单请求可能 30s 超时
 * - 新方案：每个文件单独上传 → 每文件 120s 独立超时 → 不会因总量大而误报
 *
 * 返回已上传文件的元数据，供阶段二提交博文时引用。
 * 若之前已上传成功（缓存存在），直接复用，避免重复上传。
 */
async function uploadAllFiles(): Promise<import('@/api/blog').UploadedMediaInfo[]> {
  // 如果已有缓存（上次提交失败但文件上传成功），直接复用
  if (cachedUploadedMedia.value.length > 0) {
    return cachedUploadedMedia.value
  }

  const { uploadSingleFile } = await import('@/api/blog')
  const results: import('@/api/blog').UploadedMediaInfo[] = []

  for (const item of mediaPreviews.value) {
    if (item.uploadDone) continue
    item.uploadProgress = 0
    const result = await uploadSingleFile(item.file, (pct) => {
      item.uploadProgress = pct
    })
    item.uploadDone = true
    item.uploadProgress = 100
    results.push(result)
  }

  // 缓存结果，防止提交失败后重试时丢失
  cachedUploadedMedia.value = results
  return results
}

// ========== 提交 ==========

function buildFormData(): FormData {
  // 保留向后兼容（未被新流程使用的场景）
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
    const { createPostFromUploaded, updatePostFromUploaded, publishDraft } = await import('@/api/blog')

    // 阶段一：逐个上传文件（每文件独立超时，不会误报）
    const uploadedMedia = await uploadAllFiles()

    // 阶段二：提交博文元数据（仅有文本 + 文件路径引用，请求瞬间完成）
    if (isDraft.value && props.post) {
      await updatePostFromUploaded(props.post.id, content.value, uploadedMedia,
        existingMedia.value.filter(m => m.keep).map(m => m.id))
      await publishDraft(props.post.id)
      ElMessage.success('草稿已发布')
    } else if (isEdit.value && props.post) {
      await updatePostFromUploaded(props.post.id, content.value, uploadedMedia,
        existingMedia.value.filter(m => m.keep).map(m => m.id))
      ElMessage.success('博文已更新')
    } else {
      await createPostFromUploaded(content.value, uploadedMedia)
      ElMessage.success('博文已发布')
    }
    emit('saved')
    forceClose()
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

async function handleSaveDraftThenClose() {
  saving.value = true
  try {
    const uploadedMedia = await uploadAllFiles()
    const { saveDraftFromUploaded } = await import('@/api/blog')
    await saveDraftFromUploaded(content.value, uploadedMedia)
    ElMessage.success('草稿已保存')
    emit('draft-saved')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || err?.message || '保存草稿失败')
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
    const uploadedMedia = await uploadAllFiles()
    const { updatePostFromUploaded } = await import('@/api/blog')
    await updatePostFromUploaded(props.post.id, content.value, uploadedMedia,
      existingMedia.value.filter(m => m.keep).map(m => m.id))
    ElMessage.success('草稿已保存')
    emit('saved')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || err?.message || '保存失败')
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
    const uploadedMedia = await uploadAllFiles()
    const { updatePostFromUploaded } = await import('@/api/blog')
    await updatePostFromUploaded(props.post.id, content.value, uploadedMedia,
      existingMedia.value.filter(m => m.keep).map(m => m.id))
    ElMessage.success('草稿已保存')
    emit('draft-saved')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || err?.message || '保存失败')
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

.preview-item.uploading {
  opacity: 0.7;
}

.upload-progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: rgba(0, 0, 0, 0.45);
  border-radius: 0 0 8px 8px;
}

.upload-progress-fill {
  height: 100%;
  background: #409eff;
  border-radius: 0 0 0 8px;
  transition: width 0.3s ease;
}

.upload-progress-text {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
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
  gap: 4px;
  flex-wrap: wrap;
  position: relative;
}

.publish-upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s;
}
.publish-upload-btn:hover {
  color: #3b82f6;
  background: #f3f4f6;
}

.publish-emoji-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 8px;
  font-size: 18px;
  line-height: 1;
  transition: all 0.15s;
}
.publish-emoji-btn:hover {
  background: #f3f4f6;
}

.emoji-wrapper {
  position: relative;
}

.emoji-picker {
  position: absolute;
  bottom: 100%;
  left: 0;
  z-index: 200;
  margin-bottom: 4px;
  height: 320px;
  border-radius: 12px;
  --num-columns: 8;
  --border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
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
