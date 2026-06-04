<template>
  <!-- 博文卡片 - Tailwind 风格 -->
  <div class="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow mb-4 overflow-hidden">
    <!-- 头部：作者信息 -->
    <div class="flex items-center justify-between p-4 pb-2">
      <div class="flex items-center gap-3">
        <el-avatar :size="40" :icon="UserFilled" class="flex-shrink-0" />
        <div>
          <div class="font-semibold text-sm text-gray-900">{{ post.author }}</div>
          <div class="text-xs text-gray-400">{{ formatTime(post.created_at) }}</div>
        </div>
      </div>
      <div v-if="showActions" class="flex gap-1">
        <el-button v-if="canEdit" text size="small" @click="$emit('edit')">
          <el-icon><Edit /></el-icon>
        </el-button>
        <el-button v-if="canDelete" text size="small" type="danger" @click="$emit('delete')">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 内容 -->
    <div v-if="post.content" class="px-4 pb-3">
      <p class="text-gray-800 leading-relaxed whitespace-pre-wrap break-words text-[15px]">{{ post.content }}</p>
    </div>

    <!-- 转发来源 -->
    <div v-if="post.repost" class="mx-4 mb-3 bg-gray-50 border-l-4 border-blue-500 rounded-r-lg px-4 py-2.5 text-sm">
      <div class="text-xs text-gray-400 mb-0.5">转发自 {{ post.repost.author }}</div>
      <p class="text-gray-600">{{ post.repost.content }}</p>
    </div>

    <!-- 媒体网格 -->
    <div v-if="post.media && post.media.length > 0" class="px-2 pb-3">
      <div class="grid gap-1.5 rounded-lg overflow-hidden"
           :class="mediaGridClass">
        <div v-for="(media, index) in post.media" :key="media.id"
             class="relative bg-gray-100 cursor-pointer overflow-hidden"
             :class="mediaItemClass"
             @click="handleMediaClick(media, index)">
          <!-- 图片 -->
          <img v-if="media.media_type === 'image'"
               :src="getMediaUrl(media.thumbnail_path || media.file_path)"
               alt="" class="w-full h-full object-cover" loading="lazy" />
          <!-- 视频 -->
          <template v-else>
            <div v-if="media.compress_status === 'pending' || media.compress_status === 'processing'"
                 class="w-full h-full flex flex-col items-center justify-center bg-gray-100 text-gray-400 text-xs gap-1">
              <el-icon :size="22"><VideoCamera /></el-icon>
              <span>转码中</span>
            </div>
            <div v-else-if="media.compress_status === 'failed'"
                 class="w-full h-full flex flex-col items-center justify-center bg-gray-100 text-red-400 text-xs gap-1">
              <el-icon :size="22"><VideoCamera /></el-icon>
              <span>转码失败</span>
            </div>
            <video v-else :src="getMediaUrl(media.file_path)" class="w-full h-full object-cover" preload="metadata" />
          </template>
          <!-- 视频标记 -->
          <div v-if="media.media_type === 'video'" class="absolute top-1.5 left-1.5 bg-black/55 text-white text-[10px] px-1.5 py-0.5 rounded">
            <el-icon :size="12"><VideoCamera /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏（草稿不显示） -->
    <div v-if="!post.is_draft" class="flex items-center gap-3 px-4 py-2.5 border-t border-gray-100">
      <button class="flex items-center gap-1 text-sm hover:text-red-500 transition-colors"
              :class="post.is_liked ? 'text-red-500' : 'text-gray-500'"
              @click="$emit('toggle-like')"
              :disabled="!!post.is_deleted">
        <el-icon :size="16"><Star /></el-icon>
        <span v-if="post.like_count">{{ post.like_count }}</span>
      </button>
      <button class="flex items-center gap-1 text-sm text-gray-500 hover:text-blue-500 transition-colors"
              @click="showComments = !showComments">
        <el-icon :size="16"><ChatDotRound /></el-icon>
        <span v-if="post.comment_count">{{ post.comment_count }}</span>
      </button>
      <div class="flex-1"></div>
      <button v-if="isAdmin" class="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
              @click="loadHistory">
        <el-icon :size="14"><Clock /></el-icon>历史
      </button>
    </div>

    <!-- 评论区 -->
    <BlogCommentSection
      v-if="showComments"
      :post-id="post.id"
      :current-user-id="currentUserId"
      @comment-added="post.comment_count++"
    />

    <!-- 编辑历史对话框 -->
    <el-dialog v-if="isAdmin && historyVisible" v-model="historyVisible"
               title="编辑历史" width="750px" destroy-on-close top="2vh">
      <div v-if="loadingHistory" class="text-center py-10">
        <el-icon class="is-loading" :size="28"><Loading /></el-icon>
        <p class="mt-3 text-gray-400">加载中...</p>
      </div>
      <div v-else class="max-h-[70vh] overflow-y-auto space-y-5">
        <!-- 当前版本 -->
        <div class="p-4 rounded-lg bg-green-50 border border-green-200">
          <div class="flex items-center gap-2.5 mb-2.5 flex-wrap">
            <el-tag type="success" size="small">当前版本 v{{ post.edit_version }}</el-tag>
            <span class="text-xs text-gray-400">{{ post.updated_at }}</span>
          </div>
          <div v-if="post.content" class="text-sm text-gray-800 whitespace-pre-wrap break-words leading-relaxed">{{ post.content }}</div>
          <div v-if="post.media && post.media.length > 0" class="grid gap-1.5 mt-2 rounded-lg overflow-hidden"
               :class="`grid-cols-${Math.min(post.media.length, 3)}`">
            <div v-for="m in post.media" :key="m.id"
                 class="relative aspect-square bg-gray-100 cursor-pointer overflow-hidden rounded"
                 @click="handleMediaClick(m, post.media.indexOf(m))">
              <img v-if="m.media_type === 'image'" :src="getMediaUrl(m.thumbnail_path || m.file_path)" alt="" class="w-full h-full object-cover" loading="lazy" />
              <video v-else-if="m.compress_status === 'success'" :src="getMediaUrl(m.file_path)" class="w-full h-full object-cover" preload="metadata" />
              <div v-else class="w-full h-full flex flex-col items-center justify-center bg-gray-100 text-gray-400 text-xs gap-1">
                <el-icon :size="18"><VideoCamera /></el-icon><span>{{ m.compress_status === 'failed' ? '转码失败' : '转码中' }}</span>
              </div>
            </div>
          </div>
        </div>
        <!-- 历史版本 -->
        <div v-for="h in editHistories" :key="h.id" class="p-4 rounded-lg bg-gray-50">
          <div class="flex items-center gap-2.5 mb-2.5 flex-wrap">
            <el-tag type="info" size="small">版本 {{ h.version }}</el-tag>
            <span class="text-xs text-gray-500">编辑者：{{ h.edited_by }}</span>
            <span class="text-xs text-gray-400">{{ h.created_at }}</span>
          </div>
          <div v-if="h.content" class="text-sm text-gray-800 whitespace-pre-wrap break-words leading-relaxed">{{ h.content }}</div>
          <div v-if="h.media_snapshot && parseMediaSnapshot(h.media_snapshot).length > 0"
               class="grid gap-1.5 mt-2 rounded-lg overflow-hidden"
               :class="`grid-cols-${Math.min(parseMediaSnapshot(h.media_snapshot).length, 3)}`">
            <div v-for="(m, mi) in parseMediaSnapshot(h.media_snapshot)" :key="mi"
                 class="relative aspect-square bg-gray-100 cursor-pointer overflow-hidden rounded"
                 @click="handleHistoryMediaClick(m, parseMediaSnapshot(h.media_snapshot), mi)">
              <img v-if="m.media_type === 'image'" :src="getMediaUrl(m.thumbnail_path || m.file_path)" alt="" class="w-full h-full object-cover" loading="lazy" />
              <video v-else-if="m.compress_status === 'success'" :src="getMediaUrl(m.file_path)" class="w-full h-full object-cover" preload="metadata" />
              <div v-else class="w-full h-full flex flex-col items-center justify-center bg-gray-100 text-gray-400 text-xs gap-1">
                <el-icon :size="18"><VideoCamera /></el-icon><span>{{ m.compress_status === 'failed' ? '转码失败' : '转码中' }}</span>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-if="editHistories.length === 0" description="暂无编辑历史" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Edit, Delete, VideoCamera, Star, ChatDotRound, Clock, Loading } from '@element-plus/icons-vue'
import type { BlogPost, BlogEditHistory } from '@/types/blog'
import { getMediaUrl, getEditHistory } from '@/api/blog'
import { getCurrentUserRole, getCurrentUserEmpId } from '@/utils/authUtils'
import BlogCommentSection from './BlogCommentSection.vue'

const props = defineProps<{
  post: BlogPost
  showActions?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit'): void
  (e: 'delete'): void
  (e: 'toggle-like'): void
  (e: 'media-click', media: any, index: number, mediaList?: any[]): void
}>()

const showComments = ref(false)
const historyVisible = ref(false)
const editHistories = ref<BlogEditHistory[]>([])
const loadingHistory = ref(false)

const isAdmin = computed(() => getCurrentUserRole() === 'admin')
const currentUserId = computed(() => getCurrentUserEmpId() || '')
const canEdit = computed(() => isAdmin.value || props.post.author_id === currentUserId.value)
const canDelete = computed(() => isAdmin.value || props.post.author_id === currentUserId.value)

const mediaGridClass = computed(() => {
  const count = Math.min(props.post.media?.length || 0, 3)
  return count === 1 ? 'grid-cols-1' : count === 2 ? 'grid-cols-2' : 'grid-cols-3'
})

const mediaItemClass = computed(() => {
  const count = props.post.media?.length || 0
  return count === 1 ? 'aspect-[16/9] rounded-lg' : 'aspect-square rounded-md'
})

function handleMediaClick(media: any, index: number) {
  if (media.compress_status === 'failed' || media.compress_status === 'pending' || media.compress_status === 'processing') return
  emit('media-click', media, index)
}

function handleHistoryMediaClick(media: any, historyMedias: any[], index: number) {
  const validMedias = historyMedias.filter(
    (m: any) => m.media_type === 'image' || (m.media_type === 'video' && m.compress_status === 'success')
  )
  const lightboxIndex = validMedias.findIndex((m: any) => m.file_path === media.file_path)
  if (lightboxIndex >= 0) {
    emit('media-click', media, lightboxIndex, validMedias as any)
  }
}

async function loadHistory() {
  historyVisible.value = true
  loadingHistory.value = true
  try {
    const res: any = await getEditHistory(props.post.id)
    if (res && res.history) {
      editHistories.value = res.history
    }
  } catch {
    ElMessage.error('加载编辑历史失败')
  } finally {
    loadingHistory.value = false
  }
}

function parseMediaSnapshot(snapshot: string): any[] {
  try { return JSON.parse(snapshot) || [] } catch { return [] }
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr.replace(/-/g, '/'))
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  return dateStr.slice(0, 10)
}

defineExpose({ loadHistory })
</script>
