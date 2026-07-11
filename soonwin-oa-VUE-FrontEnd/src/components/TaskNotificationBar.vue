<template>
  <div v-if="visible" class="task-notification-bar">
    <!-- 回到顶部 -->
    <el-button class="notif-btn" title="回到顶部" @click="scrollToTop">
      <el-icon :size="18"><Top /></el-icon>
    </el-button>

    <!-- 留言 + 点赞 合并通知 -->
    <div class="notif-item-wrapper" @mouseenter="onNotifEnter" @mouseleave="onNotifLeave">
      <el-badge :value="totalUnreadCount" :max="99" :hidden="totalUnreadCount === 0">
        <el-button class="notif-btn" title="通知（留言+点赞）" @click="onNotifClick">
          <el-icon :size="18"><ChatDotRound /></el-icon>
        </el-button>
      </el-badge>
      <div v-if="showNotifPanel" class="notif-dropdown">
        <div class="notif-dropdown-header">
          <span class="notif-header-title">
            <span>通知</span>
            <span v-if="totalUnreadCount > 0" class="notif-header-count">{{ totalUnreadCount }}</span>
          </span>
          <button class="notif-clear-btn" @click="clearAll">清除全部</button>
        </div>
        <div v-if="mergedNotifications.length === 0" class="notif-empty">暂无通知</div>
        <div v-else class="notif-list">
          <div v-for="n in mergedNotifications" :key="n.key" class="notif-row" @click="jumpToTask(n.task_id)">
            <img :src="`/api/posts/avatar/${n.user_id}`" class="notif-avatar" />
            <div class="notif-row-body">
              <div class="notif-row-title">
                <span class="notif-tag" :class="`notif-tag-${n.type}`">{{ n.typeLabel }}</span>
                <span class="notif-row-name">{{ n.name }}</span>
              </div>
              <div v-if="n.content" class="notif-row-content">{{ n.content }}</div>
              <div class="notif-row-meta">{{ n.task_content_preview }} · {{ n.timeText }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建任务 -->
    <div class="notif-item-wrapper">
      <el-button class="notif-btn" title="新建任务" @click="scrollToPublish">
        <el-icon :size="18"><EditPen /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Top, ChatDotRound, EditPen } from '@element-plus/icons-vue'
import { getTaskNotifications, clearTaskNotifications } from '@/api/task'
import { hasToken as checkHasToken } from '@/utils/authUtils'

const props = defineProps<{
  visible: boolean
}>()

const hasToken = ref(false)
const comments = ref<any[]>([])
const likes = ref<any[]>([])
const showNotifPanel = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null
let panelTimer: ReturnType<typeof setTimeout> | null = null

// 合并留言 + 点赞的总未读数
const totalUnreadCount = computed(() => comments.value.length + likes.value.length)

// 合并并按 created_at 倒序
const mergedNotifications = computed(() => {
  const items: any[] = []
  for (const c of comments.value) {
    items.push({
      type: 'comment',
      typeLabel: '留言',
      key: `c_${c.id}`,
      task_id: c.task_id,
      user_id: c.author_id,
      name: c.author_name,
      content: c.content || '',
      task_content_preview: c.task_content_preview || '',
      created_at: c.created_at,
      timeText: formatRelativeTime(c.created_at),
    })
  }
  for (const l of likes.value) {
    items.push({
      type: 'like',
      typeLabel: '点赞',
      key: `l_${l.task_id}_${l.user_id}`,
      task_id: l.task_id,
      user_id: l.user_id,
      name: l.name,
      content: '',
      task_content_preview: l.task_content_preview || '',
      created_at: l.created_at,
      timeText: formatRelativeTime(l.created_at),
    })
  }
  return items.sort((a, b) => {
    const ta = a.created_at ? new Date(a.created_at.replace(/-/g, '/')).getTime() : 0
    const tb = b.created_at ? new Date(b.created_at.replace(/-/g, '/')).getTime() : 0
    return tb - ta
  })
})

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

async function clearAll() {
  try {
    await clearTaskNotifications()
    comments.value = []
    likes.value = []
    showNotifPanel.value = false
    ElMessage.success('通知已清除')
  } catch (e: any) {
    ElMessage.error('清除失败')
  }
}

function onNotifEnter() {
  if (panelTimer) { clearTimeout(panelTimer); panelTimer = null }
  showNotifPanel.value = true
}
function onNotifLeave() {
  panelTimer = setTimeout(() => { showNotifPanel.value = false }, 200)
}
function onNotifClick() {
  // 点击切换面板显示
  showNotifPanel.value = !showNotifPanel.value
}

function formatRelativeTime(s: string): string {
  if (!s) return ''
  const d = new Date(s.replace(/-/g, '/'))
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 0) return ''
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
function scrollToPublish() {
  const el = document.querySelector('.publish-box')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function jumpToTask(taskId: number) {
  // 关闭面板并滚到顶部（v-for 内 ref 不可靠，简化处理）
  showNotifPanel.value = false
  scrollToTop()
}

onMounted(() => {
  hasToken.value = checkHasToken()
  if (hasToken.value) {
    fetchNotifications()
    pollTimer = setInterval(fetchNotifications, 30000)
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
  /* 锁定宽度，防止被 hover 列表"撑开" */
  width: 60px;
  flex-shrink: 0;
}

.notif-item-wrapper {
  position: relative;
  width: 44px;
  flex-shrink: 0;
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

/* hover 冒泡：默认在工具栏**左边**展开（right: 100% + 8px 间距） */
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

.notif-dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  background: #fafafa;
}
.notif-header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}
.notif-header-count {
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  line-height: 1.4;
}

.notif-clear-btn {
  background: none;
  border: none;
  color: #3b82f6;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
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
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #e5e7eb;
  object-fit: cover;
}
.notif-row-body {
  flex: 1;
  min-width: 0;
}
.notif-row-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #1f2937;
}
.notif-tag {
  font-size: 10px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
  line-height: 1.5;
}
.notif-tag-comment {
  background: #dbeafe;
  color: #1d4ed8;
}
.notif-tag-like {
  background: #fce7f3;
  color: #be185d;
}
.notif-row-name {
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}
.notif-row-content {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notif-row-meta {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .task-notification-bar {
    right: 12px;
    padding: 6px;
    width: 52px;
  }
  .notif-btn { width: 40px !important; height: 40px !important; }
  .notif-item-wrapper { width: 40px; }
  .notif-dropdown {
    width: 260px;
    right: calc(100% + 8px);
  }
}
</style>