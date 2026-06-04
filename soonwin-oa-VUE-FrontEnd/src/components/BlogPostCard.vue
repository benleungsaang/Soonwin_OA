<template>
  <el-card class="post-card" shadow="hover">
    <!-- 头部：作者信息 + 操作 -->
    <div class="post-header">
      <div class="author-info">
        <el-avatar :size="40" :icon="UserFilled" />
        <div class="author-text">
          <div class="author-name">{{ post.author }}</div>
          <div class="post-time">{{ formatTime(post.created_at) }}</div>
        </div>
      </div>
      <div v-if="showActions" class="post-actions">
        <el-button v-if="canEdit" text size="small" @click="$emit('edit')">
          <el-icon><Edit /></el-icon>
        </el-button>
        <el-button v-if="canDelete" text size="small" type="danger" @click="$emit('delete')">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 内容 -->
    <div class="post-content" v-if="post.content">
      <p>{{ post.content }}</p>
    </div>

    <!-- 转发来源 -->
    <div v-if="post.repost" class="repost-source">
      <div class="repost-label">转发自 {{ post.repost.author }}：</div>
      <p>{{ post.repost.content }}</p>
    </div>

    <!-- 媒体网格 -->
    <div v-if="post.media && post.media.length > 0" class="media-grid" :class="`media-count-${Math.min(post.media.length, 3)}`">
      <div
        v-for="(media, index) in post.media"
        :key="media.id"
        class="media-item"
        @click="handleMediaClick(media, index)"
      >
        <!-- 视频：转码中状态 -->
        <template v-if="media.media_type === 'video'">
          <div v-if="media.compress_status === 'pending' || media.compress_status === 'processing'"
               class="transcoding-placeholder">
            <el-icon :size="28"><VideoCamera /></el-icon>
            <span>转码中</span>
          </div>
          <div v-else-if="media.compress_status === 'failed'" class="transcoding-placeholder failed">
            <el-icon :size="28"><VideoCamera /></el-icon>
            <span>转码失败</span>
          </div>
          <video v-else :src="getMediaUrl(media.file_path)" preload="metadata" />
        </template>
        <!-- 图片 -->
        <img v-else :src="getMediaUrl(media.thumbnail_path || media.file_path)" alt="" loading="lazy" />
        <!-- 类型标记 -->
        <div v-if="media.media_type === 'video'" class="media-type-badge">
          <el-icon><VideoCamera /></el-icon>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="post-footer">
      <el-button text :type="post.is_liked ? 'danger' : ''" @click="$emit('toggle-like')">
        <el-icon><HeartFilled v-if="post.is_liked" /><Star v-else /></el-icon>
        {{ post.like_count || '' }}
      </el-button>
      <el-button text @click="showComments = !showComments">
        <el-icon><ChatDotRound /></el-icon>
        {{ post.comment_count || '' }}
      </el-button>
      <el-button v-if="isAdmin" text @click="loadHistory" style="margin-left: auto;">
        <el-icon><Clock /></el-icon>历史
      </el-button>
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
               title="编辑历史" width="700px" destroy-on-close>
      <div v-if="loadingHistory" style="text-align:center;padding:20px;">
        <el-icon class="is-loading"><Loading /></el-icon> 加载中...
      </div>
      <el-timeline v-else>
        <el-timeline-item
          v-for="h in editHistories"
          :key="h.id"
          :timestamp="h.created_at"
          placement="top"
        >
          <el-card>
            <div><strong>版本 {{ h.version }}</strong> — 编辑者：{{ h.edited_by }}</div>
            <div style="white-space: pre-wrap; margin-top: 8px;">{{ h.content }}</div>
            <div v-if="h.media_snapshot" style="margin-top: 4px; color: #909399; font-size: 12px;">
              包含 {{ JSON.parse(h.media_snapshot).length }} 个媒体文件
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled, Edit, Delete, VideoCamera, Star, ChatDotRound, Clock, Loading, HeartFilled } from '@element-plus/icons-vue'
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
  (e: 'media-click', media: any, index: number): void
}>()

const showComments = ref(false)
const historyVisible = ref(false)
const editHistories = ref<BlogEditHistory[]>([])
const loadingHistory = ref(false)

const isAdmin = computed(() => getCurrentUserRole() === 'admin')
const currentUserId = computed(() => getCurrentUserEmpId() || '')
const canEdit = computed(() => isAdmin.value || props.post.author_id === currentUserId.value)
const canDelete = computed(() => isAdmin.value || props.post.author_id === currentUserId.value)

function handleMediaClick(media: any, index: number) {
  if (media.media_type === 'video' && media.compress_status === 'success') {
    emit('media-click', media, index)
  } else if (media.media_type === 'image') {
    emit('media-click', media, index)
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

// 暴露给父组件调用
defineExpose({ loadHistory })

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
</script>

<style scoped>
.post-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.author-name {
  font-weight: 600;
  font-size: 15px;
}

.post-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.post-actions {
  display: flex;
  gap: 4px;
}

.post-content {
  margin-bottom: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.repost-source {
  background: #f5f7fa;
  border-left: 3px solid #409eff;
  padding: 10px 14px;
  margin-bottom: 12px;
  border-radius: 0 6px 6px 0;
  font-size: 13px;
}

.repost-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.media-grid {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.media-count-1 { grid-template-columns: 1fr; }
.media-count-2 { grid-template-columns: 1fr 1fr; }
.media-count-3 { grid-template-columns: 1fr 1fr 1fr; }

.media-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #f5f7fa;
  aspect-ratio: 1;
}

.media-item img,
.media-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.transcoding-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f0f2f5;
  color: #909399;
  font-size: 12px;
  gap: 6px;
}

.transcoding-placeholder.failed {
  color: #f56c6c;
}

.media-type-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
}

.post-footer {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
}
</style>
