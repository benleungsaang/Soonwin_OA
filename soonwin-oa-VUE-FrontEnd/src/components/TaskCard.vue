<template>
  <article class="task-card" :style="cardStyle">
    <!-- 头部 -->
    <div class="task-header">
      <div class="task-author">
        <div class="task-avatar">
          <img v-if="task.author_id" :src="`/api/posts/avatar/${task.author_id}`" class="w-full h-full object-cover"
            @error="($event.target as HTMLImageElement).style.display='none'" />
          <el-icon v-else :size="14" color="#6b7280"><UserFilled /></el-icon>
        </div>
        <p class="task-author-name">{{ task.author_name }}</p>
      </div>
      <div class="task-header-right">
        <span class="task-header-time">{{ formatTime(task.created_at) }}</span>
        <div class="task-header-actions">
        <!-- 修改历史（仅管理员） -->
        <button v-if="isAdmin && !readonly" class="task-icon-btn" title="修改历史" @click="$emit('history', task)">
          <el-icon :size="15"><Clock /></el-icon>
        </button>
        <!-- 可见性设置（仅管理员） -->
        <button v-if="isAdmin && !readonly" class="task-icon-btn" title="可见性设置" @click="$emit('visibility', task)">
          <el-icon :size="15"><View /></el-icon>
        </button>
        <!-- 底色选择（仅作者或管理员） -->
        <button v-if="canEdit && !readonly" class="task-icon-btn" title="底色" @click="openColorPicker">
          <el-icon :size="15"><Brush /></el-icon>
        </button>
        <!-- 编辑 -->
        <button v-if="canEdit && !readonly" class="task-icon-btn" title="编辑" @click="$emit('edit', task)">
          <el-icon :size="15"><Edit /></el-icon>
        </button>
        <!-- 删除 -->
        <button v-if="canEdit && !readonly" class="task-icon-btn task-icon-btn-danger" title="删除" @click="$emit('delete', task)">
          <el-icon :size="15"><Delete /></el-icon>
        </button>
      </div>
      </div>
    </div>

    <!-- 待办内容 -->
    <div class="task-body">
      <div class="task-content-row">
        <!-- 复选框 -->
        <button class="task-checkbox" :class="{ 'task-checkbox-checked': task.status === 'completed' }"
          @click="$emit('toggle-complete', task)" :title="task.status === 'completed' ? '点击回退到待办' : '点击标记完成'">
          <el-icon v-if="task.status === 'completed'" :size="14" color="#fff"><Check /></el-icon>
        </button>
        <p class="task-text" :class="{ 'task-text-done': task.status === 'completed' }">
          {{ task.content }}
        </p>
      </div>

      <!-- 待办附图 -->
      <div v-if="task.todo_image_url" class="task-image-wrap">
        <img :src="getMediaUrl(task.todo_image_url)" class="task-image" @click="openImage(task.todo_image_url)" />
      </div>

      <!-- 完成内容（仅 completed 状态显示） -->
      <div v-if="task.status === 'completed' && (task.completion_note || task.completion_image_url)" class="task-completion">
        <div v-if="task.completion_note" class="task-completion-note">
          <span class="task-completion-label">完成</span>
          <span class="task-completion-text">{{ task.completion_note }}</span>
        </div>
        <img v-if="task.completion_image_url" :src="getMediaUrl(task.completion_image_url)"
          class="task-image task-image-small" @click="openImage(task.completion_image_url)" />
        <div v-if="task.completed_at" class="text-xs text-gray-400 mt-1">完成时间：{{ formatTime(task.completed_at) }}</div>
      </div>

      <!-- 预计完成日期 -->
      <div v-if="task.expected_date" class="task-expected" :class="expectedDateClass">
        <el-icon :size="12"><Calendar /></el-icon>
        <span>预计完成：{{ task.expected_date }}</span>
      </div>

      <!-- 可见性徽标（仅本人/管理员视角，非默认时显示） -->
      <div v-if="isAdmin && task.visibilities && task.visibilities.length > 0" class="task-visibility-tag">
        <el-icon :size="11"><View /></el-icon>
        <span>自定义可见：{{ task.visibilities.length }} 项</span>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="task-actions">
      <button class="task-action-btn" @click="showComments = !showComments">
        <el-icon :size="14"><ChatDotRound /></el-icon>
        <span>{{ task.comment_count || '留言' }}</span>
      </button>
      <button class="task-action-btn" :class="{ 'task-action-btn-liked': task.is_liked }"
        @click="$emit('like', task)" @mouseenter="onLikeEnter" @mouseleave="onLikeLeave">
        <svg class="like-svg" viewBox="0 0 24 24" width="15" height="15"
          stroke="currentColor" stroke-width="2" :fill="task.is_liked ? 'currentColor' : 'none'"
          stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
        </svg>
        <span v-if="task.like_count" class="like-count">{{ task.like_count }}</span>
        <div v-if="likers.length > 0" v-show="showLikersTooltip" class="likers-tooltip">
          <div v-for="user in likers" :key="user.user_id" class="liker-row">
            <img :src="`/api/posts/avatar/${user.user_id}`" class="liker-avatar" />
            <span class="liker-name">{{ user.name }}</span>
          </div>
        </div>
      </button>
    </div>

    <!-- 留言区 -->
    <TaskCommentSection
      v-if="showComments"
      :task-id="task.id"
      :current-user-id="currentUserId"
      :is-admin="isAdmin"
      @comment-added="task.comment_count++"
      @comment-deleted="task.comment_count = Math.max(0, (task.comment_count || 1) - 1)"
    />
  </article>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Check, Edit, Delete, Clock, ChatDotRound, View, Brush, Calendar } from '@element-plus/icons-vue'
import { getTaskLikes } from '@/api/task'
import TaskCommentSection from './TaskCommentSection.vue'

const props = defineProps<{
  task: any
  currentUserId: string
  isAdmin: boolean
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-complete'): void
  (e: 'edit'): void
  (e: 'delete'): void
  (e: 'like'): void
  (e: 'add-comment', payload: { task: any; content: string }): void
  (e: 'visibility'): void
  (e: 'background', payload: { task: any; color: string }): void
  (e: 'history'): void
}>()

const showComments = ref(false)

// 卡片底色
const cardStyle = computed(() => {
  if (props.task.background_color) {
    return { backgroundColor: props.task.background_color }
  }
  return {}
})

// 预计完成日期颜色
const expectedDateClass = computed(() => {
  if (!props.task.expected_date) return ''
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expected = new Date(props.task.expected_date)
  const diffDays = Math.floor((expected.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  if (props.task.status === 'completed') return ''
  if (diffDays < 0) return 'expected-overdue'
  if (diffDays <= 3) return 'expected-soon'
  return ''
})

const canEdit = computed(() => props.isAdmin || props.task.author_id === props.currentUserId)

// 底色选择弹窗
const colorPickerVisible = ref(false)
const presetColors = [
  '', '#ef4444', '#f97316', '#eab308', '#22c55e',
  '#3b82f6', '#a855f7', '#1f2937', '#f3f4f6',
  '#ec4899', '#92400e',
]
function openColorPicker() {
  // 简易实现：直接循环切换预设色
  const idx = presetColors.indexOf(props.task.background_color || '')
  const nextIdx = (idx + 1) % presetColors.length
  const next = presetColors[nextIdx]
  emit('background', { task: props.task, color: next })
}

// 点赞悬停
const likers = ref<Array<{ user_id: string; name: string }>>([])
const showLikersTooltip = ref(false)
let likersLoaded = false
let likeLeaveTimer: ReturnType<typeof setTimeout> | null = null

async function loadLikers(force = false) {
  if (!force && likersLoaded) return
  try {
    const res: any = await getTaskLikes(props.task.id)
    if (Array.isArray(res)) likers.value = res
    likersLoaded = true
  } catch { /* ignore */ }
}

watch(() => props.task.like_count, () => {
  likersLoaded = false
  loadLikers(true)
})

function onLikeEnter() {
  if (likeLeaveTimer) { clearTimeout(likeLeaveTimer); likeLeaveTimer = null }
  loadLikers()
  showLikersTooltip.value = true
}
function onLikeLeave() {
  likeLeaveTimer = setTimeout(() => { showLikersTooltip.value = false }, 200)
}

function getMediaUrl(path: string) {
  if (!path) return ''
  return `/assets/TasksMedia/${path}`
}

function openImage(path: string) {
  const url = getMediaUrl(path)
  window.open(url, '_blank')
}

function formatTime(s: string) {
  if (!s) return ''
  const d = new Date(s.replace(/-/g, '/'))
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<style scoped>
.task-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  margin-bottom: 12px;
  padding: 14px 16px;
  transition: background-color 0.2s;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.task-author { display: flex; align-items: center; gap: 10px; }
.task-avatar { width: 32px; height: 32px; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0; }
.task-author-name { font-size: 14px; font-weight: 500; color: #1f2937; margin: 0; }

/* 头部右侧：时间 + 操作按钮 */
.task-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.task-header-time {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  padding-right: 50px;
  white-space: nowrap;
}

.task-header-actions { display: flex; gap: 4px; }
.task-icon-btn {
  width: 28px; height: 28px; border-radius: 6px;
  background: transparent; border: none; color: #6b7280;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.task-icon-btn:hover { background: rgba(0,0,0,0.05); color: #374151; }
.task-icon-btn-danger:hover { color: #ef4444; background: #fef2f2; }

.task-body { padding-left: 0; }
.task-content-row { display: flex; align-items: flex-start; gap: 10px; }

.task-checkbox {
  width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0;
  border: 2px solid #d1d5db; background: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  margin-top: 2px; padding: 0;
  transition: all 0.15s;
}
.task-checkbox:hover { border-color: #3b82f6; }
.task-checkbox-checked { background: #22c55e; border-color: #22c55e; }
.task-checkbox-checked:hover { background: #16a34a; border-color: #16a34a; }

.task-text { font-size: 15px; color: #1f2937; line-height: 1.6; margin: 0; flex: 1; word-break: break-word; }
.task-text-done { text-decoration: line-through; color: #9ca3af; }

.task-image-wrap { margin-top: 10px; margin-left: 30px; }
.task-image { max-width: 240px; max-height: 320px; border-radius: 8px; cursor: pointer; display: block; }
.task-image-small { max-width: 160px; max-height: 200px; }

.task-completion {
  margin-top: 12px; margin-left: 30px;
  padding: 10px 12px; background: rgba(34, 197, 94, 0.08);
  border-left: 3px solid #22c55e; border-radius: 6px;
}
.task-completion-note { display: flex; align-items: flex-start; gap: 8px; }
.task-completion-label { font-size: 11px; background: #22c55e; color: #fff; padding: 1px 6px; border-radius: 4px; flex-shrink: 0; }
.task-completion-text { font-size: 14px; color: #166534; line-height: 1.5; word-break: break-word; }

.task-expected {
  margin-top: 10px; margin-left: 30px;
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; padding: 2px 8px; border-radius: 4px;
  background: #f3f4f6; color: #6b7280;
}
.task-expected.expected-soon { background: #fff7ed; color: #c2410c; }
.task-expected.expected-overdue { background: #fef2f2; color: #dc2626; font-weight: 500; }

.task-visibility-tag {
  margin-top: 8px; margin-left: 30px;
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; color: #6b7280; background: #f3f4f6;
  padding: 2px 8px; border-radius: 4px;
}

.task-actions {
  display: flex; gap: 16px; padding-top: 10px;
  margin-top: 10px; border-top: 1px solid #f3f4f6;
}
.task-action-btn {
  display: inline-flex; align-items: center; gap: 4px;
  background: none; border: none; cursor: pointer;
  color: #6b7280; font-size: 12px; padding: 4px 6px;
  border-radius: 6px; transition: all 0.15s; position: relative;
}
.task-action-btn:hover { background: #f3f4f6; color: #374151; }
.task-action-btn-liked { color: #ef4444; }
.like-svg { transition: all 0.15s; }
.like-count { font-size: 12px; }

/* 点赞悬停提示 */
.likers-tooltip {
  position: absolute; bottom: calc(100% + 6px); left: 0;
  background: #fff; border: 1px solid #e5e7eb;
  border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 8px; min-width: 140px; max-height: 200px; overflow: auto;
  z-index: 50;
}
.liker-row { display: flex; align-items: center; gap: 6px; padding: 4px; }
.liker-avatar { width: 20px; height: 20px; border-radius: 50%; }
.liker-name { font-size: 12px; color: #374151; }
</style>