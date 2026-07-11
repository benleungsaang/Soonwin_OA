<template>
  <div v-if="visible" class="task-notification-bar">
    <el-button class="notif-btn" title="回到顶部" @click="scrollToTop">
      <el-icon :size="18"><Top /></el-icon>
    </el-button>
    <div class="notif-item-wrapper" @mouseenter="onCommentEnter" @mouseleave="onCommentLeave">
      <el-badge :value="unreadCommentCount" :max="99" :hidden="unreadCommentCount === 0">
        <el-button class="notif-btn" title="留言通知" @click="onCommentClick">
          <el-icon :size="18"><ChatDotRound /></el-icon>
        </el-button>
      </el-badge>
      <div v-if="showCommentPanel" class="notif-dropdown notif-dropdown-right">
        <div class="notif-dropdown-header">
          <span>留言通知</span>
          <button class="notif-clear-btn" @click="clearComments">清除</button>
        </div>
        <div v-if="comments.length === 0" class="notif-empty">暂无留言通知</div>
        <div v-else class="notif-list">
          <div v-for="c in comments" :key="c.id" class="notif-row" @click="jumpToTask(c.task_id)">
            <img v-if="c.author_id" :src="`/api/posts/avatar/${c.author_id}`" class="notif-avatar" />
            <div class="flex-1 min-w-0">
              <div class="notif-row-title">{{ c.author_name }} 留言了</div>
              <div class="notif-row-content">{{ c.content }}</div>
              <div class="notif-row-meta">{{ c.task_content_preview }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="notif-item-wrapper" @mouseenter="onLikeEnter" @mouseleave="onLikeLeave">
      <el-badge :value="unreadLikeCount" :max="99" :hidden="unreadLikeCount === 0">
        <el-button class="notif-btn" title="点赞通知" @click="onLikeClick">
          <el-icon :size="18"><Star /></el-icon>
        </el-button>
      </el-badge>
      <div v-if="showLikePanel" class="notif-dropdown notif-dropdown-right">
        <div class="notif-dropdown-header">
          <span>点赞通知</span>
          <button class="notif-clear-btn" @click="clearLikes">清除</button>
        </div>
        <div v-if="likes.length === 0" class="notif-empty">暂无点赞通知</div>
        <div v-else class="notif-list">
          <div v-for="l in likes" :key="l.task_id + l.user_id" class="notif-row" @click="jumpToTask(l.task_id)">
            <img :src="`/api/posts/avatar/${l.user_id}`" class="notif-avatar" />
            <div class="flex-1 min-w-0">
              <div class="notif-row-title">{{ l.name }} 点赞了你的任务</div>
              <div class="notif-row-meta">{{ l.task_content_preview }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="notif-item-wrapper">
      <el-button class="notif-btn" title="新建任务" @click="scrollToPublish">
        <el-icon :size="18"><EditPen /></el-icon>
      </el-button>
    </div>
    <div v-if="showCommentPanel || showLikePanel" class="notif-dropdown-footer">
      <el-button size="small" @click="clearAll">清除全部通知</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Top, ChatDotRound, Star, EditPen } from '@element-plus/icons-vue'
import { getTaskNotifications, clearTaskNotifications } from '@/api/task'
import { hasToken as checkHasToken } from '@/utils/authUtils'

const props = defineProps<{
  visible: boolean
}>()

const hasToken = ref(false)
const comments = ref<any[]>([])
const likes = ref<any[]>([])
const showCommentPanel = ref(false)
const showLikePanel = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null
let panelTimer: ReturnType<typeof setTimeout> | null = null
const lastSeenCommentIds = ref<Set<number>>(new Set())
const lastSeenLikeKeys = ref<Set<string>>(new Set())

const unreadCommentCount = computed(() => comments.value.length)
const unreadLikeCount = computed(() => likes.value.length)

async function fetchNotifications() {
  if (!hasToken.value) return
  try {
    const res: any = await getTaskNotifications()
    if (res) {
      comments.value = res.comments || []
      likes.value = res.likes || []
    }
  } catch { /* ignore */ }
}

function clearComments() {
  lastSeenCommentIds.value = new Set(comments.value.map(c => c.id))
  comments.value = []
}
function clearLikes() {
  lastSeenLikeKeys.value = new Set(likes.value.map(l => `${l.task_id}_${l.user_id}`))
  likes.value = []
}
async function clearAll() {
  try {
    await clearTaskNotifications()
    comments.value = []
    likes.value = []
    ElMessage.success('通知已清除')
  } catch (e: any) {
    ElMessage.error('清除失败')
  }
}

function onCommentEnter() {
  if (panelTimer) { clearTimeout(panelTimer); panelTimer = null }
  showCommentPanel.value = true
  showLikePanel.value = false
}
function onCommentLeave() {
  panelTimer = setTimeout(() => { showCommentPanel.value = false }, 200)
}
function onLikeEnter() {
  if (panelTimer) { clearTimeout(panelTimer); panelTimer = null }
  showLikePanel.value = true
  showCommentPanel.value = false
}
function onLikeLeave() {
  panelTimer = setTimeout(() => { showLikePanel.value = false }, 200)
}
function onCommentClick() {
  // 点击 badge 直接清除
  clearComments()
}
function onLikeClick() {
  clearLikes()
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
function scrollToPublish() {
  // 跳到主页面发布区
  const el = document.querySelector('.publish-box')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function jumpToTask(taskId: number) {
  // 滚动到对应卡片（用 DOM 查询，v-for 内 ref 不可靠）
  const cards = document.querySelectorAll('.task-card')
  // 这里简单通过 contenteditable 文本匹配不强，依赖 task id 顺序；简化方案：滚动到顶部即可
  scrollToTop()
  showCommentPanel.value = false
  showLikePanel.value = false
}

onMounted(() => {
  hasToken.value = checkHasToken()
  if (hasToken.value) {
    fetchNotifications()
    pollTimer = setInterval(fetchNotifications, 30000) // 30 秒轮询
  }
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (panelTimer) clearTimeout(panelTimer)
})
</script>

<style scoped>
.task-notification-bar {
  position: fixed;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.12);
  padding: 8px;
  border: 1px solid #e5e7eb;
}

.notif-item-wrapper {
  position: relative;
}

.notif-btn {
  width: 44px !important;
  height: 44px !important;
  border-radius: 12px !important;
  padding: 0 !important;
  background: #f9fafb !important;
  border: 1px solid transparent !important;
  color: #374151 !important;
  transition: all 0.15s !important;
}
.notif-btn:hover {
  background: #eff6ff !important;
  color: #3b82f6 !important;
  border-color: #bfdbfe !important;
}

.notif-dropdown {
  position: absolute;
  top: 50%;
  right: calc(100% + 8px);
  transform: translateY(-50%);
  width: 320px;
  max-height: 480px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 110;
}

.notif-dropdown-right {
  right: auto;
  left: calc(100% + 8px);
}

.notif-dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  background: #fafafa;
}

.notif-clear-btn {
  background: none; border: none; color: #3b82f6;
  font-size: 12px; cursor: pointer; padding: 0;
}
.notif-clear-btn:hover { text-decoration: underline; }

.notif-empty {
  padding: 40px 16px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}

.notif-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}

.notif-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.notif-row:hover { background: #f3f4f6; }
.notif-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  background: #e5e7eb; object-fit: cover;
}
.notif-row-title {
  font-size: 13px; color: #1f2937; font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.notif-row-content {
  font-size: 12px; color: #6b7280; margin-top: 2px;
  word-break: break-word;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.notif-row-meta {
  font-size: 11px; color: #9ca3af; margin-top: 4px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.notif-dropdown-footer {
  padding: 8px;
  border-top: 1px solid #f3f4f6;
  background: #fafafa;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .task-notification-bar {
    right: 12px;
    padding: 6px;
  }
  .notif-btn { width: 40px !important; height: 40px !important; }
  .notif-dropdown {
    width: 260px;
    right: auto;
    left: calc(100% + 8px);
  }
}
</style>