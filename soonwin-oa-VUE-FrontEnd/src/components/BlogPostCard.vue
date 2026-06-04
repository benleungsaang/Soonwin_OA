<template>
  <article class="post-card">
    <!-- 头部：作者信息 + 删除/编辑 -->
    <div class="post-header">
      <div class="post-author">
        <div class="post-avatar">
          <el-icon :size="20" color="#3b82f6"><UserFilled /></el-icon>
        </div>
        <div>
          <p class="post-author-name">{{ post.author }}</p>
          <p class="post-author-time">{{ formatTime(post.created_at) }}</p>
        </div>
      </div>
      <div v-if="showActions" class="post-header-actions">
        <button v-if="canEdit" class="post-icon-btn" title="编辑" @click="$emit('edit')">
          <el-icon :size="16"><Edit /></el-icon>
        </button>
        <button v-if="canDelete" class="post-icon-btn post-icon-btn-danger" title="删除" @click="$emit('delete')">
          <el-icon :size="16"><Delete /></el-icon>
        </button>
      </div>
    </div>

    <!-- 内容 -->
    <div v-if="post.content" class="post-body">
      <p class="post-text">{{ post.content }}</p>
    </div>

    <!-- 转发来源 -->
    <div v-if="post.repost" class="post-repost">
      <div class="post-repost-header">
        <div class="post-repost-avatar">
          <el-icon :size="11" color="#3b82f6"><UserFilled /></el-icon>
        </div>
        <span class="post-repost-author">{{ post.repost.author }}</span>
        <span class="post-repost-time">{{ formatTime(post.repost.created_at) }}</span>
      </div>
      <p v-if="post.repost.content" class="post-repost-text">{{ post.repost.content }}</p>
    </div>

    <!-- 媒体区域 -->
    <div v-if="post.media && post.media.length > 0" class="post-media-wrapper">
      <!-- 展开模式 -->
      <div v-if="expandedIdx !== null" class="expanded-view">
        <div class="expanded-controls">
          <button @click="collapseExpand"><el-icon :size="14"><ArrowUp /></el-icon>收起</button>
          <div class="expanded-controls-right">
            <button @click="rotateExpanded"><el-icon :size="14"><Refresh /></el-icon>旋转</button>
            <button @click="openLightboxFromExpand"><el-icon :size="14"><ZoomIn /></el-icon>查看原图</button>
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
      <div v-else class="media-grid" :class="post.media.length === 1 ? 'media-grid-single' : ''">
        <div v-for="(media, index) in post.media" :key="media.id"
             class="media-item" @click="handleMediaClick(media, index)">
          <img v-if="media.media_type === 'image'"
               :src="getMediaUrl(media.thumbnail_path || media.file_path)"
               alt="" loading="lazy" />
          <!-- 视频：pending 才显示转码中，processing/success 都尝试播放 -->
          <video v-else-if="media.media_type === 'video' && media.compress_status !== 'pending'"
                 :src="getMediaUrl(media.file_path)" preload="metadata"
                 @error="($event.target as HTMLVideoElement).style.display='none'" />
          <div v-else-if="media.media_type === 'video'"
               class="media-placeholder">
            <el-icon :size="24"><VideoCamera /></el-icon>
            <span>转码中</span>
          </div>
          <span v-if="media.media_type === 'video'" class="video-badge">
            <el-icon :size="11"><VideoCamera /></el-icon>视频
          </span>
        </div>
      </div>
    </div>

    <!-- 功能条（草稿不显示） -->
    <div v-if="!post.is_draft" class="post-actions">
      <button v-if="canEdit" class="post-action-btn" @click="$emit('edit')">
        <el-icon :size="15"><Edit /></el-icon>
        <span>编辑</span>
      </button>
      <button class="post-action-btn" @click="showComments = !showComments">
        <el-icon :size="15"><ChatDotRound /></el-icon>
        <span>{{ post.comment_count || '留言' }}</span>
      </button>
      <button v-if="!post.is_deleted" class="post-action-btn"
              :class="{ 'post-action-btn-liked': post.is_liked }"
              :disabled="!!post.is_deleted" @click="$emit('toggle-like')">
        <el-icon :size="15"><Star /></el-icon>
        <span>{{ post.like_count || '点赞' }}</span>
      </button>
      <button v-if="isAdmin" class="post-action-btn" @click="loadHistory">
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
      <div v-if="loadingHistory" style="text-align:center;padding:40px 0">
        <el-icon class="is-loading" :size="28"><Loading /></el-icon>
        <p style="margin-top:12px;color:#909399">加载中...</p>
      </div>
      <div v-else class="history-list">
        <div class="history-version history-version-current">
          <div class="history-version-head">
            <el-tag type="success" size="small">当前版本 v{{ post.edit_version }}</el-tag>
            <span class="history-version-time">{{ post.updated_at }}</span>
          </div>
          <div v-if="post.content" class="history-version-text">{{ post.content }}</div>
          <div v-if="post.media && post.media.length > 0" class="media-grid" :class="post.media.length === 1 ? 'media-grid-single' : ''">
            <div v-for="m in post.media" :key="m.id" class="media-item" @click="handleMediaClick(m, post.media.indexOf(m))">
              <img v-if="m.media_type === 'image'" :src="getMediaUrl(m.thumbnail_path || m.file_path)" alt="" loading="lazy" />
              <video v-else-if="m.compress_status !== 'pending'" :src="getMediaUrl(m.file_path)" preload="metadata" />
              <div v-else class="media-placeholder"><el-icon :size="20"><VideoCamera /></el-icon><span>转码中</span></div>
            </div>
          </div>
        </div>
        <div v-for="h in editHistories" :key="h.id" class="history-version">
          <div class="history-version-head">
            <el-tag type="info" size="small">版本 {{ h.version }}</el-tag>
            <span class="history-version-editor">编辑者：{{ h.edited_by }}</span>
            <span class="history-version-time">{{ h.created_at }}</span>
          </div>
          <div v-if="h.content" class="history-version-text">{{ h.content }}</div>
          <div v-if="h.media_snapshot && parseMediaSnapshot(h.media_snapshot).length > 0"
               class="media-grid" :class="parseMediaSnapshot(h.media_snapshot).length === 1 ? 'media-grid-single' : ''">
            <div v-for="(m, mi) in parseMediaSnapshot(h.media_snapshot)" :key="mi" class="media-item"
                 @click="handleHistoryMediaClick(m, parseMediaSnapshot(h.media_snapshot), mi)">
              <img v-if="m.media_type === 'image'" :src="getMediaUrl(m.thumbnail_path || m.file_path)" alt="" loading="lazy" />
              <video v-else-if="m.compress_status !== 'pending'" :src="getMediaUrl(m.file_path)" preload="metadata" />
              <div v-else class="media-placeholder"><el-icon :size="20"><VideoCamera /></el-icon><span>转码中</span></div>
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

const props = defineProps<{ post: BlogPost; showActions?: boolean }>()
const emit = defineEmits<{
  (e: 'edit'): void; (e: 'delete'): void; (e: 'toggle-like'): void
  (e: 'media-click', media: any, index: number, mediaList?: any[]): void
}>()

const showComments = ref(false)
const historyVisible = ref(false)
const editHistories = ref<BlogEditHistory[]>([])
const loadingHistory = ref(false)

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
  if (media.compress_status === 'pending') return
  if (media.media_type === 'video') {
    emit('media-click', media, index)
  } else if (expandedIdx.value === index) {
    collapseExpand()
  } else {
    expandMedia(index)
  }
}

function expandMedia(index: number) { collapseExpand(); expandedIdx.value = index; rotateDeg.value = 0 }
function collapseExpand() { expandedIdx.value = null; rotateDeg.value = 0 }
function prevExpanded() { if (expandedIdx.value !== null && expandedIdx.value > 0) expandMedia(expandedIdx.value - 1) }
function nextExpanded() { if (expandedIdx.value !== null && props.post.media && expandedIdx.value < props.post.media.length - 1) expandMedia(expandedIdx.value + 1) }
function rotateExpanded() {
  rotateDeg.value += 90
  const wrap = expandWrapRef.value
  const el = wrap?.querySelector('img') || wrap?.querySelector('video')
  if (!wrap || !el) return
  wrap.style.minHeight = wrap.getBoundingClientRect().height + 'px'
  requestAnimationFrame(() => {
    if ((rotateDeg.value % 360) === 90 || (rotateDeg.value % 360) === 270) {
      wrap.style.minHeight = el.getBoundingClientRect().width + 'px'; wrap.style.maxHeight = '2000px'
    } else {
      wrap.style.minHeight = '150px'; wrap.style.maxHeight = 'calc(50vh - 40px)'
    }
  })
}
function openLightboxFromExpand() {
  if (expandedIdx.value !== null) { const i = expandedIdx.value; collapseExpand(); emit('media-click', props.post.media![i], i) }
}

function handleHistoryMediaClick(media: any, historyMedias: any[], index: number) {
  const validMedias = historyMedias.filter((m: any) => m.media_type === 'image' || (m.media_type === 'video' && m.compress_status !== 'pending'))
  const lightboxIndex = validMedias.findIndex((m: any) => m.file_path === media.file_path)
  if (lightboxIndex >= 0) emit('media-click', media, lightboxIndex, validMedias as any)
}

async function loadHistory() {
  historyVisible.value = true; loadingHistory.value = true
  try { const res: any = await getEditHistory(props.post.id); if (res?.history) editHistories.value = res.history }
  catch { ElMessage.error('加载编辑历史失败') }
  finally { loadingHistory.value = false }
}

function parseMediaSnapshot(snapshot: string): any[] { try { return JSON.parse(snapshot) || [] } catch { return [] } }

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr.replace(/-/g, '/')); const now = new Date()
  const diff = (now.getTime() - date.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  const pad = (n: number) => String(n).padStart(2, '0'); const time = `${pad(date.getHours())}:${pad(date.getMinutes())}`
  const yesterday = new Date(now); yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return `昨天 ${time}`
  if (date.getFullYear() === now.getFullYear()) return `${date.getMonth() + 1}月${date.getDate()}日 ${time}`
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${time}`
}

defineExpose({ loadHistory })
</script>

<style scoped>
/* ===== 卡片 ===== */
.post-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
  margin-bottom: 24px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.post-card:hover { box-shadow: 0 8px 25px rgba(0,0,0,0.1); }

/* ===== 头部 ===== */
.post-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 8px 16px;
}
.post-author { display: flex; align-items: center; gap: 12px; }
.post-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: #eff6ff; display: flex; align-items: center; justify-content: center;
  overflow: hidden; flex-shrink: 0;
}
.post-author-name { font-weight: 500; color: #1f2937; font-size: 15px; margin: 0; }
.post-author-time { font-size: 12px; color: #9ca3af; margin: 2px 0 0 0; }
.post-header-actions { display: flex; gap: 4px; }

/* ===== 内容 ===== */
.post-body { padding: 0 16px 12px 16px; }
.post-text { color: #1f2937; white-space: pre-wrap; word-break: break-word; font-size: 15px; line-height: 1.6; margin: 0; }

/* ===== 转发 ===== */
.post-repost {
  margin: 0 16px 12px 16px; padding: 12px;
  background: #f9fafb; border-radius: 8px; border: 1px solid #f3f4f6;
}
.post-repost-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.post-repost-avatar {
  width: 20px; height: 20px; border-radius: 50%; background: #eff6ff;
  display: flex; align-items: center; justify-content: center; overflow: hidden;
}
.post-repost-author { font-size: 12px; font-weight: 500; color: #374151; }
.post-repost-time { font-size: 12px; color: #9ca3af; }
.post-repost-text { font-size: 14px; color: #4b5563; white-space: pre-wrap; margin: 4px 0 0 0; }

/* ===== 功能条按钮 ===== */
.post-actions {
  display: flex;
  align-items: center;
  border-top: 1px solid #f9fafb;
  color: #9ca3af;
  font-size: 14px;
}
.post-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 10px 0;
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  font-size: inherit;
  transition: color 0.2s;
}
.post-action-btn:hover { color: #4b5563; }
.post-action-btn-liked { color: #ef4444 !important; }
.post-action-btn:disabled { opacity: 0.5; cursor: default; }

.post-icon-btn {
  padding: 8px;
  background: none;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s, background 0.2s;
}
.post-icon-btn:hover { color: #3b82f6; background: #f3f4f6; }
.post-icon-btn-danger:hover { color: #ef4444; }

/* ===== 媒体网格 ===== */
.post-media-wrapper { padding: 0 16px 12px 16px; }
.media-grid { display: grid; gap: 4px; grid-template-columns: 1fr 1fr 1fr; }
.media-grid-single { grid-template-columns: 1fr; }
.media-item {
  position: relative; overflow: hidden; background: #000;
  border-radius: 8px; cursor: pointer;
}
.media-item img, .media-item video {
  width: 100%; height: 200px; object-fit: cover; display: block;
}
.media-placeholder {
  width: 100%; height: 200px; display: flex;
  flex-direction: column; align-items: center; justify-content: center;
  background: #f3f4f6; color: #9ca3af; font-size: 12px; gap: 4px;
}
.video-badge {
  position: absolute; right: 6px; bottom: 6px;
  background: rgba(0,0,0,0.65); color: #fff; font-size: 11px;
  padding: 2px 6px; border-radius: 4px;
  display: flex; align-items: center; gap: 3px; pointer-events: none;
}

/* ===== 展开模式 ===== */
.expanded-view {
  max-height: 50vh; overflow: hidden; background: #f3f4f6;
  border-radius: 8px; transition: max-height 0.35s ease;
}
.expanded-controls {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; background: rgba(0,0,0,0.05); border-radius: 8px 8px 0 0;
}
.expanded-controls button {
  padding: 5px 12px; font-size: 12px; border-radius: 6px;
  border: 1px solid #d1d5db; background: #fff; cursor: pointer;
  display: flex; align-items: center; gap: 3px;
}
.expanded-controls button:hover { background: #e5e7eb; }
.expanded-controls-right { display: flex; gap: 8px; }
.expanded-media-wrap {
  position: relative; display: flex; align-items: center; justify-content: center;
  max-height: calc(50vh - 40px); overflow: hidden; min-height: 150px;
  transition: min-height 0.35s ease, max-height 0.35s ease;
}
.expanded-media-wrap img { max-width: 100%; max-height: calc(50vh - 56px); object-fit: contain; transition: transform 0.3s; }
.expanded-media-wrap video { max-width: 100%; max-height: calc(50vh - 56px); }
.expand-nav-left, .expand-nav-right {
  position: absolute; top: 0; bottom: 0; width: 33.33%; z-index: 2;
}
.expand-nav-left { left: 0; cursor: w-resize; }
.expand-nav-right { right: 0; cursor: e-resize; }
.expand-nav-center {
  position: absolute; top: 0; bottom: 0; left: 33.33%; right: 33.33%;
  z-index: 2; cursor: zoom-out;
}

/* ===== 编辑历史 ===== */
.history-list { max-height: 70vh; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }
.history-version { padding: 16px; border-radius: 8px; background: #f9fafb; }
.history-version-current { background: #f0fdf4; border: 1px solid #dcfce7; }
.history-version-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.history-version-time { font-size: 12px; color: #9ca3af; }
.history-version-editor { font-size: 12px; color: #4b5563; }
.history-version-text { white-space: pre-wrap; word-break: break-word; line-height: 1.6; font-size: 14px; color: #1f2937; margin-bottom: 8px; }

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .media-grid { gap: 8px; }
  .media-item img, .media-item video { height: auto; aspect-ratio: 1; max-height: 200px; }
  .post-card:active { transform: scale(0.98); }
}
@media (max-width: 640px) {
  .media-grid { grid-template-columns: 1fr 1fr !important; }
}
@media (hover: none) {
  .post-card:active { transform: scale(0.98); }
}
</style>
