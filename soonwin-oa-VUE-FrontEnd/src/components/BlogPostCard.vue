<template>
  <article class="post-card bg-white rounded-xl shadow-md overflow-hidden mb-6">
    <!-- 头部：作者信息 + 删除/编辑 -->
    <div class="p-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center overflow-hidden flex-shrink-0">
          <el-icon :size="20" color="#3b82f6"><UserFilled /></el-icon>
        </div>
        <div>
          <p class="font-medium text-gray-800 text-[15px]">{{ post.author }}</p>
          <p class="text-xs text-gray-400">{{ formatTime(post.created_at) }}</p>
        </div>
      </div>
      <div v-if="showActions" class="flex gap-1">
        <el-button v-if="canEdit" text size="small" class="!p-2 !text-gray-400 hover:!text-blue-500" @click="$emit('edit')">
          <el-icon :size="16"><Edit /></el-icon>
        </el-button>
        <el-button v-if="canDelete" text size="small" class="!p-2 !text-gray-400 hover:!text-red-500" @click="$emit('delete')">
          <el-icon :size="16"><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 内容 -->
    <div v-if="post.content" class="px-4 pb-3">
      <p class="text-gray-800 whitespace-pre-wrap break-words text-[15px] leading-relaxed">{{ post.content }}</p>
    </div>

    <!-- 转发来源 -->
    <div v-if="post.repost" class="mx-4 mb-3 p-3 bg-gray-50 rounded-lg border border-gray-100">
      <div class="flex items-center gap-2 mb-1">
        <div class="w-5 h-5 rounded-full bg-blue-50 flex items-center justify-center overflow-hidden">
          <el-icon :size="11" color="#3b82f6"><UserFilled /></el-icon>
        </div>
        <span class="text-xs font-medium text-gray-700">{{ post.repost.author }}</span>
        <span class="text-xs text-gray-400">{{ formatTime(post.repost.created_at) }}</span>
      </div>
      <p v-if="post.repost.content" class="text-sm text-gray-600 whitespace-pre-wrap">{{ post.repost.content }}</p>
    </div>

    <!-- 媒体区域 -->
    <div v-if="post.media && post.media.length > 0" class="post-media-wrapper px-4 pb-3">
      <!-- 展开模式 -->
      <div v-if="expandedIdx !== null" class="expanded-view">
        <div class="expanded-controls">
          <button @click="collapseExpand"><el-icon :size="14"><ArrowUp /></el-icon> 收起</button>
          <div class="flex gap-2">
            <button @click="rotateExpanded"><el-icon :size="14"><Refresh /></el-icon> 旋转</button>
            <button @click="openLightboxFromExpand"><el-icon :size="14"><ZoomIn /></el-icon> 查看原图</button>
          </div>
        </div>
        <div class="expanded-media-wrap" ref="expandWrapRef">
          <div v-if="expandedIdx > 0" class="expand-nav-left" @click="prevExpanded"></div>
          <div v-if="expandedIdx < post.media.length - 1" class="expand-nav-right" @click="nextExpanded"></div>
          <div class="expand-nav-center" @click="collapseExpand"></div>
          <img v-if="expandedMedia.media_type === 'image'"
               :src="getMediaUrl(expandedMedia.file_path)" alt=""
               :style="{ transform: `rotate(${rotateDeg}deg)` }" />
          <video v-else :src="getMediaUrl(expandedMedia.file_path)" controls
                 :style="{ transform: `rotate(${rotateDeg}deg)` }" />
        </div>
      </div>
      <!-- 媒体缩略网格 -->
      <div v-else class="media-grid" :class="post.media.length === 1 ? 'grid-cols-1' : ''">
        <div v-for="(media, index) in post.media" :key="media.id"
             class="media-item" :class="{ collapsed: expandedIdx !== null && expandedIdx !== index }"
             @click="handleMediaClick(media, index)">
          <!-- 图片 -->
          <img v-if="media.media_type === 'image'"
               :src="getMediaUrl(media.thumbnail_path || media.file_path)"
               alt="" loading="lazy" />
          <!-- 视频 - 转码成功 -->
          <video v-else-if="media.media_type === 'video' && media.compress_status === 'success'"
                 :src="getMediaUrl(media.file_path)" preload="metadata" />
          <!-- 视频 - 转码失败 -->
          <div v-else-if="media.media_type === 'video' && media.compress_status === 'failed'"
               class="media-placeholder text-red-400">
            <el-icon :size="24"><VideoCamera /></el-icon>
            <span class="text-xs mt-1">转码失败</span>
          </div>
          <!-- 视频 - 转码中 -->
          <div v-else
               class="media-placeholder text-gray-400">
            <el-icon :size="24"><VideoCamera /></el-icon>
            <span class="text-xs mt-1">转码中</span>
          </div>
          <!-- 视频标记 -->
          <span v-if="media.media_type === 'video'" class="video-badge">
            <el-icon :size="11"><VideoCamera /></el-icon>视频
          </span>
        </div>
      </div>
    </div>

    <!-- 功能条（草稿不显示） -->
    <div v-if="!post.is_draft" class="flex items-center border-t border-gray-50 text-gray-400 text-sm">
      <button class="flex-1 flex items-center justify-center gap-1 py-2.5 hover:text-gray-600 transition-colors"
              @click="$emit('edit')" v-if="canEdit">
        <el-icon :size="15"><Edit /></el-icon>
        <span>编辑</span>
      </button>
      <button class="flex-1 flex items-center justify-center gap-1 py-2.5 hover:text-blue-500 transition-colors"
              @click="showComments = !showComments">
        <el-icon :size="15"><ChatDotRound /></el-icon>
        <span>{{ post.comment_count || '留言' }}</span>
      </button>
      <button class="flex-1 flex items-center justify-center gap-1 py-2.5 hover:text-red-500 transition-colors"
              :class="post.is_liked ? '!text-red-500' : ''"
              @click="$emit('toggle-like')" :disabled="!!post.is_deleted"
              v-if="!post.is_deleted">
        <el-icon :size="15"><Star /></el-icon>
        <span>{{ post.like_count || '点赞' }}</span>
      </button>
      <button v-if="isAdmin" class="flex-1 flex items-center justify-center gap-1 py-2.5 hover:text-gray-600 transition-colors"
              @click="loadHistory">
        <el-icon :size="15"><Clock /></el-icon>
        <span>历史</span>
      </button>
    </div>

    <!-- 留言区 -->
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
      <div v-else class="max-h-[70vh] overflow-y-auto space-y-6">
        <!-- 当前版本 -->
        <div class="p-4 rounded-lg bg-green-50 border border-green-200">
          <div class="flex items-center gap-2.5 mb-3 flex-wrap">
            <el-tag type="success" size="small">当前版本 v{{ post.edit_version }}</el-tag>
            <span class="text-xs text-gray-400">{{ post.updated_at }}</span>
          </div>
          <div v-if="post.content" class="text-sm text-gray-800 whitespace-pre-wrap break-words leading-relaxed mb-3">{{ post.content }}</div>
          <div v-if="post.media && post.media.length > 0" class="media-grid" :class="post.media.length === 1 ? 'grid-cols-1' : ''">
            <div v-for="m in post.media" :key="m.id" class="media-item" @click="handleMediaClick(m, post.media.indexOf(m))">
              <img v-if="m.media_type === 'image'" :src="getMediaUrl(m.thumbnail_path || m.file_path)" alt="" loading="lazy" />
              <video v-else-if="m.compress_status === 'success'" :src="getMediaUrl(m.file_path)" preload="metadata" />
              <div v-else class="media-placeholder text-gray-400"><el-icon :size="20"><VideoCamera /></el-icon><span class="text-xs mt-1">转码中</span></div>
            </div>
          </div>
        </div>
        <!-- 历史版本 -->
        <div v-for="h in editHistories" :key="h.id" class="p-4 rounded-lg bg-gray-50">
          <div class="flex items-center gap-2.5 mb-3 flex-wrap">
            <el-tag type="info" size="small">版本 {{ h.version }}</el-tag>
            <span class="text-xs text-gray-500">编辑者：{{ h.edited_by }}</span>
            <span class="text-xs text-gray-400">{{ h.created_at }}</span>
          </div>
          <div v-if="h.content" class="text-sm text-gray-800 whitespace-pre-wrap break-words leading-relaxed mb-3">{{ h.content }}</div>
          <div v-if="h.media_snapshot && parseMediaSnapshot(h.media_snapshot).length > 0"
               class="media-grid" :class="parseMediaSnapshot(h.media_snapshot).length === 1 ? 'grid-cols-1' : ''">
            <div v-for="(m, mi) in parseMediaSnapshot(h.media_snapshot)" :key="mi" class="media-item"
                 @click="handleHistoryMediaClick(m, parseMediaSnapshot(h.media_snapshot), mi)">
              <img v-if="m.media_type === 'image'" :src="getMediaUrl(m.thumbnail_path || m.file_path)" alt="" loading="lazy" />
              <video v-else-if="m.compress_status === 'success'" :src="getMediaUrl(m.file_path)" preload="metadata" />
              <div v-else class="media-placeholder text-gray-400"><el-icon :size="20"><VideoCamera /></el-icon><span class="text-xs mt-1">转码中</span></div>
            </div>
          </div>
        </div>
        <el-empty v-if="editHistories.length === 0" description="暂无编辑历史" />
      </div>
    </el-dialog>
  </article>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Edit, Delete, VideoCamera, Star, ChatDotRound, Clock, Loading, ArrowUp, Refresh, ZoomIn } from '@element-plus/icons-vue'
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

// 展开模式
const expandedIdx = ref<number | null>(null)
const rotateDeg = ref(0)
const expandWrapRef = ref<HTMLElement | null>(null)

const expandedMedia = computed(() => {
  if (expandedIdx.value === null || !props.post.media) return null
  return props.post.media[expandedIdx.value] || null
})

const isAdmin = computed(() => getCurrentUserRole() === 'admin')
const currentUserId = computed(() => getCurrentUserEmpId() || '')
const canEdit = computed(() => isAdmin.value || props.post.author_id === currentUserId.value)
const canDelete = computed(() => isAdmin.value || props.post.author_id === currentUserId.value)

function handleMediaClick(media: any, index: number) {
  if (media.compress_status === 'pending' || media.compress_status === 'processing' || media.compress_status === 'failed') return
  if (media.media_type === 'video') {
    // 视频直接打开灯箱
    emit('media-click', media, index)
  } else {
    // 图片展开模式
    if (expandedIdx.value === index) {
      collapseExpand()
    } else {
      expandMedia(index)
    }
  }
}

// ========== 展开模式 ==========
function expandMedia(index: number) {
  collapseExpand()
  expandedIdx.value = index
  rotateDeg.value = 0
}

function collapseExpand() {
  expandedIdx.value = null
  rotateDeg.value = 0
}

function prevExpanded() {
  if (expandedIdx.value !== null && expandedIdx.value > 0) {
    expandMedia(expandedIdx.value - 1)
  }
}

function nextExpanded() {
  if (expandedIdx.value !== null && props.post.media && expandedIdx.value < props.post.media.length - 1) {
    expandMedia(expandedIdx.value + 1)
  }
}

function rotateExpanded() {
  rotateDeg.value += 90
  const wrap = expandWrapRef.value
  const el = wrap?.querySelector('img') || wrap?.querySelector('video')
  if (!wrap || !el) return
  const effectiveDeg = rotateDeg.value % 360
  wrap.style.minHeight = wrap.getBoundingClientRect().height + 'px'
  requestAnimationFrame(() => {
    if (effectiveDeg === 90 || effectiveDeg === 270) {
      const targetH = el.getBoundingClientRect().width
      wrap.style.minHeight = targetH + 'px'
      wrap.style.maxHeight = '2000px'
    } else {
      wrap.style.minHeight = '150px'
      wrap.style.maxHeight = 'calc(50vh - 40px)'
    }
  })
}

function openLightboxFromExpand() {
  if (expandedIdx.value !== null) {
    collapseExpand()
    emit('media-click', expandedMedia.value, expandedIdx.value || 0)
  }
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
    if (res && res.history) editHistories.value = res.history
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
  const diff = (now.getTime() - date.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  const pad = (n: number) => String(n).padStart(2, '0')
  const time = `${pad(date.getHours())}:${pad(date.getMinutes())}`
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return `昨天 ${time}`
  if (date.getFullYear() === now.getFullYear()) return `${date.getMonth() + 1}月${date.getDate()}日 ${time}`
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${time}`
}

defineExpose({ loadHistory })
</script>

<style scoped>
/* 媒体网格 - 与参考 posts.html 一致 */
.media-grid {
  display: grid;
  gap: 4px;
  grid-template-columns: 1fr 1fr 1fr;
}

.media-grid.grid-cols-1 {
  grid-template-columns: 1fr;
}

.media-item {
  position: relative;
  overflow: hidden;
  background: #000;
  border-radius: 8px;
  cursor: pointer;
}

.media-item img,
.media-item video {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}

.media-placeholder {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
}

.video-badge {
  position: absolute;
  right: 6px;
  bottom: 6px;
  background: rgba(0,0,0,0.65);
  color: #fff;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 3px;
  pointer-events: none;
}

.post-media-wrapper {
  padding: 0;
}

.post-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.post-card:hover {
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

/* 展开模式 - 匹配参考 posts.html */
.expanded-view {
  max-height: 50vh;
  overflow: hidden;
  background: #f3f4f6;
  border-radius: 8px;
  transition: max-height 0.35s ease;
}

.expanded-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: rgba(0,0,0,0.05);
  border-radius: 8px 8px 0 0;
}

.expanded-controls button {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.expanded-controls button:hover {
  background: #e5e7eb;
}

.expanded-media-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  max-height: calc(50vh - 40px);
  overflow: hidden;
  min-height: 150px;
  transition: min-height 0.35s ease, max-height 0.35s ease;
}

.expanded-media-wrap img {
  max-width: 100%;
  max-height: calc(50vh - 56px);
  object-fit: contain;
  transition: transform 0.3s;
}

.expanded-media-wrap video {
  max-width: 100%;
  max-height: calc(50vh - 56px);
}

.expand-nav-left,
.expand-nav-right {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 33.33%;
  z-index: 2;
}

.expand-nav-left {
  left: 0;
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Cpolyline points='16,4 8,12 16,20' fill='none' stroke='%23666' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") 12 12, w-resize;
}

.expand-nav-right {
  right: 0;
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Cpolyline points='8,4 16,12 8,20' fill='none' stroke='%23666' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") 12 12, e-resize;
}

.expand-nav-center {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 33.33%;
  right: 33.33%;
  z-index: 2;
  cursor: zoom-out;
}

.media-item.collapsed {
  display: none;
}

/* 移动端 */
@media screen and (max-width: 768px) {
  .media-grid {
    gap: 8px;
  }
  .media-item img,
  .media-item video {
    height: auto;
    aspect-ratio: 1;
    max-height: 200px;
  }
  .post-card:active {
    transform: scale(0.98);
  }
}

@media screen and (max-width: 640px) {
  .media-grid {
    grid-template-columns: 1fr 1fr !important;
  }
}

@media (hover: none) {
  .post-card:active {
    transform: scale(0.98);
  }
}
</style>
