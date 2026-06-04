<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑博文' : '发布博文'"
    width="700px"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <div class="create-dialog-body">
      <!-- 内容输入 -->
      <el-input
        v-model="content"
        type="textarea"
        :rows="5"
        placeholder="分享你的想法..."
        maxlength="5000"
        show-word-limit
      />

      <!-- 媒体预览区 -->
      <div v-if="mediaPreviews.length > 0" class="media-preview-area">
        <div v-for="(item, index) in mediaPreviews" :key="index" class="preview-item">
          <img v-if="item.type === 'image'" :src="item.url" alt="" />
          <video v-else-if="item.type === 'video'" :src="item.url" controls />
          <div class="preview-badge">{{ item.type === 'video' ? '视频' : '图片' }}</div>
          <el-button
            class="preview-remove-btn"
            type="danger"
            size="small"
            circle
            :icon="Delete"
            @click="removeMedia(index)"
          />
        </div>
      </div>

      <!-- 已有媒体（编辑模式） -->
      <div v-if="isEdit && existingMedia.length > 0" class="existing-media-area">
        <div class="section-label">已有附件：</div>
        <div class="media-preview-area">
          <div v-for="item in existingMedia" :key="item.id" class="preview-item" :class="{ removed: !item.keep }">
            <img v-if="item.media_type === 'image'" :src="getMediaUrl(item.thumbnail_path || item.file_path)" alt="" />
            <video v-else :src="getMediaUrl(item.file_path)" />
            <el-button
              class="preview-remove-btn"
              :type="item.keep ? 'danger' : 'primary'"
              size="small"
              circle
              @click="toggleKeepExisting(item)"
            >
              {{ item.keep ? '×' : '↩' }}
            </el-button>
          </div>
        </div>
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
        <el-button type="primary" plain @click="$refs.fileInputRef.click()">
          <el-icon><PictureFilled /></el-icon> 添加图片/视频
        </el-button>
        <span class="upload-hint">支持 JPG/PNG/GIF/WEBP 图片和 MP4/AVI/MOV 视频</span>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleSaveDraft" :loading="saving">保存草稿</el-button>
        <el-button type="primary" @click="handlePublish" :loading="saving">
          {{ isEdit ? '保存修改' : '发布' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, PictureFilled } from '@element-plus/icons-vue'
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
  set: (val) => emit('update:visible', val),
})

const isEdit = computed(() => !!props.post)

const content = ref('')
const mediaPreviews = ref<MediaPreview[]>([])
const existingMedia = ref<ExistingMediaItem[]>([])
const saving = ref(false)

// 初始化编辑数据
watch(() => props.visible, (val) => {
  if (val) {
    content.value = props.post?.content || ''
    mediaPreviews.value = []
    existingMedia.value = (props.post?.media || []).map(m => ({ ...m, keep: true }))
  }
})

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const isVideo = file.type.startsWith('video/')
    const url = URL.createObjectURL(file)
    mediaPreviews.value.push({
      type: isVideo ? 'video' : 'image',
      url,
      file,
    })
  }
  input.value = ''
}

function removeMedia(index: number) {
  URL.revokeObjectURL(mediaPreviews.value[index].url)
  mediaPreviews.value.splice(index, 1)
}

function toggleKeepExisting(item: ExistingMediaItem) {
  item.keep = !item.keep
}

function buildFormData(): FormData {
  const formData = new FormData()
  formData.append('content', content.value)
  mediaPreviews.value.forEach(item => {
    formData.append('media', item.file)
  })
  if (isEdit.value) {
    const keepIds = existingMedia.value.filter(m => m.keep).map(m => m.id).join(',')
    formData.append('keep_media_ids', keepIds)
  }
  return formData
}

async function handlePublish() {
  if (!content.value.trim() && mediaPreviews.value.length === 0
      && existingMedia.value.filter(m => m.keep).length === 0) {
    ElMessage.warning('请输入内容或添加媒体文件')
    return
  }
  saving.value = true
  try {
    const { createPost, updatePost } = await import('@/api/blog')
    const formData = buildFormData()
    if (isEdit.value && props.post) {
      await updatePost(props.post.id, formData)
      ElMessage.success('博文已更新')
    } else {
      await createPost(formData)
      ElMessage.success('博文已发布')
    }
    emit('saved')
    dialogVisible.value = false
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleSaveDraft() {
  if (!content.value.trim() && mediaPreviews.value.length === 0) {
    ElMessage.warning('请输入草稿内容')
    return
  }
  saving.value = true
  try {
    const { saveDraft } = await import('@/api/blog')
    const formData = new FormData()
    formData.append('content', content.value)
    mediaPreviews.value.forEach(item => {
      formData.append('media', item.file)
    })
    await saveDraft(formData)
    ElMessage.success('草稿已保存')
    emit('draft-saved')
    dialogVisible.value = false
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '保存草稿失败')
  } finally {
    saving.value = false
  }
}

function handleClose() {
  mediaPreviews.value.forEach(item => URL.revokeObjectURL(item.url))
  mediaPreviews.value = []
  content.value = ''
  existingMedia.value = []
}
</script>

<style scoped>
.create-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
