<template>
  <div class="bg-gray-50 border-t border-gray-100 px-4 py-3">
    <!-- 留言列表 -->
    <div v-if="visibleComments.length > 0" class="space-y-1.5 mb-2" :class="showAll ? '' : 'max-h-48 overflow-hidden'">
      <div v-for="comment in visibleComments" :key="comment.id" class="flex items-start gap-2 py-1 group">
        <div class="w-6 h-6 rounded-full bg-gray-200 flex-shrink-0 overflow-hidden flex items-center justify-center">
          <img v-if="comment.author_id" :src="`/api/posts/avatar/${comment.author_id}`"
            class="w-full h-full object-cover" @error="($event.target as HTMLImageElement).style.display='none'" />
          <el-icon v-if="!comment.author_id" :size="12" color="#6b7280"><UserFilled /></el-icon>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium text-gray-600">{{ comment.author_name }}</span>
            <span class="text-xs text-gray-400">{{ formatTime(comment.created_at) }}</span>
          </div>
          <p class="text-sm text-gray-500 mt-0.5 break-words">{{ comment.content }}</p>
        </div>
        <!-- 删除按钮 -->
        <button v-if="canDelete(comment)" class="comment-delete-btn" @click="handleDelete(comment.id)">
          <el-icon :size="11"><Close /></el-icon>
        </button>
      </div>
    </div>

    <!-- 查看更多 -->
    <button v-if="comments.length > COMMENTS_PREVIEW && !showAll" class="comment-more-btn" @click="showAll = true">
      查看更多留言 ({{ comments.length - COMMENTS_PREVIEW }})
    </button>

    <p v-if="comments.length === 0" class="text-gray-400 text-sm text-center py-2">暂无留言，来说点什么吧</p>

    <!-- 输入区 -->
    <div class="flex gap-2 mt-2">
      <input ref="commentInputRef" v-model="commentText" placeholder="写留言..." class="comment-input"
        @keydown.enter="handleSubmit" />
      <div class="comment-emoji-area">
        <button class="comment-emoji-btn" @click="commentEmojiVisible = !commentEmojiVisible">🙂</button>
        <div ref="commentEmojiWrapperRef" class="emoji-wrapper">
          <emoji-picker v-if="commentEmojiVisible" class="emoji-picker" @emoji-click="handleCommentEmoji" />
        </div>
      </div>
      <button class="comment-send-btn" :disabled="submitting" @click="handleSubmit">发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled, Close } from '@element-plus/icons-vue'
import 'emoji-picker-element'
import { getTaskComments, createTaskComment, deleteTaskComment } from '@/api/task'

const COMMENTS_PREVIEW = 3

const props = defineProps<{
  taskId: number
  currentUserId: string
  isAdmin: boolean
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'comment-added'): void
  (e: 'comment-deleted'): void
}>()

const comments = ref<any[]>([])
const commentText = ref('')
const submitting = ref(false)
const showAll = ref(false)

const commentEmojiVisible = ref(false)
const commentEmojiWrapperRef = ref<HTMLElement | null>(null)
const commentInputRef = ref<HTMLInputElement | null>(null)

function handleCommentEmoji(event: any) {
  const emoji: string = event.detail.emoji.unicode
  const input = commentInputRef.value
  if (input) {
    const s = input.selectionStart; const e = input.selectionEnd
    commentText.value = commentText.value.substring(0, s) + emoji + commentText.value.substring(e)
    nextTick(() => { const p = s + emoji.length; input.setSelectionRange(p, p); input.focus() })
  } else {
    commentText.value += emoji
  }
  commentEmojiVisible.value = false
}

function onCommentEmojiOutsideClick(e: MouseEvent) {
  if (!commentEmojiVisible.value) return
  const target = e.target as HTMLElement
  if (commentEmojiWrapperRef.value?.contains(target)) return
  if (target.closest('.comment-emoji-btn')) return
  commentEmojiVisible.value = false
}
onMounted(() => document.addEventListener('mousedown', onCommentEmojiOutsideClick))
onUnmounted(() => document.removeEventListener('mousedown', onCommentEmojiOutsideClick))

const visibleComments = computed(() => showAll.value ? comments.value : comments.value.slice(0, COMMENTS_PREVIEW))

onMounted(async () => {
  try {
    const res: any = await getTaskComments(props.taskId)
    comments.value = res || []
  } catch { /* ignore */ }
})

function canDelete(comment: any): boolean {
  return props.isAdmin || comment.author_id === props.currentUserId
}

async function handleSubmit() {
  if (!commentText.value.trim()) return
  submitting.value = true
  try {
    const res: any = await createTaskComment(props.taskId, commentText.value.trim())
    if (res) {
      comments.value.push(res)
      commentText.value = ''
      emit('comment-added')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '留言失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(commentId: number) {
  try {
    await ElMessageBox.confirm('确定要删除这条留言吗？', '删除确认', { type: 'warning' })
    await deleteTaskComment(commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
    ElMessage.success('留言已删除')
    emit('comment-deleted')
  } catch (err: any) {
    if (err === 'cancel') return
    ElMessage.error(err?.response?.data?.message || '删除失败')
  }
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
  return `${date.getMonth() + 1}月${date.getDate()}日 ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
</script>

<style scoped>
.comment-delete-btn {
  opacity: 0; padding: 2px; color: #9ca3af; background: none; border: none;
  border-radius: 4px; cursor: pointer; transition: opacity 0.15s, color 0.15s;
  flex-shrink: 0; display: flex; align-items: center;
}
.group:hover .comment-delete-btn { opacity: 1; }
.comment-delete-btn:hover { color: #ef4444; }

.comment-more-btn {
  background: none; border: none; color: #3b82f6; font-size: 12px;
  cursor: pointer; padding: 0; margin-bottom: 8px;
}
.comment-more-btn:hover { text-decoration: underline; }

.comment-input {
  flex: 1; padding: 6px 12px; font-size: 13px; border: 1px solid #e5e7eb;
  border-radius: 8px; outline: none; background: #fff; box-sizing: border-box;
}
.comment-input:focus { border-color: #3b82f6; }
.comment-emoji-area { position: relative; display: flex; align-items: center; }
.comment-emoji-btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 6px 8px; background: none; border: none; cursor: pointer;
  border-radius: 8px; font-size: 18px; line-height: 1; transition: all 0.15s;
  color: #9ca3af;
}
.comment-emoji-btn:hover { color: #3b82f6; background: #f3f4f6; }
.comment-emoji-area .emoji-wrapper { position: relative; }
.comment-emoji-area .emoji-picker {
  position: absolute; bottom: 100%; right: 0; z-index: 200;
  margin-bottom: 4px; height: 260px; border-radius: 12px;
  --num-columns: 8; --border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.comment-send-btn {
  padding: 6px 12px; background: #3b82f6; color: #fff; border: none;
  border-radius: 8px; font-size: 13px; cursor: pointer; flex-shrink: 0;
  transition: background 0.15s;
}
.comment-send-btn:hover { background: #2563eb; }
.comment-send-btn:disabled { opacity: 0.6; cursor: default; }
</style>