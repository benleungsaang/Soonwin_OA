<template>
  <div class="bg-gray-50 border-t border-gray-100 px-4 py-3">
    <!-- 评论列表 -->
    <div v-if="showAllComments.length > 0" class="space-y-1.5 mb-2" :class="showAll ? '' : 'max-h-48 overflow-hidden'">
      <div v-for="comment in showAllComments" :key="comment.id" class="flex items-start gap-2 py-1 group">
        <div class="w-6 h-6 rounded-full bg-gray-200 flex-shrink-0 overflow-hidden flex items-center justify-center">
          <img v-if="comment.author_id" :src="`/api/posts/avatar/${comment.author_id}`"
               class="w-full h-full object-cover" @error="($event.target as HTMLImageElement).style.display='none'" />
          <el-icon v-if="!comment.author_id" :size="12" color="#6b7280"><UserFilled /></el-icon>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium text-gray-600">{{ comment.author }}</span>
            <span class="text-xs text-gray-400">{{ formatTime(comment.created_at) }}</span>
          </div>
          <p class="text-sm text-gray-500 mt-0.5 break-words">{{ comment.content }}</p>
        </div>
        <button v-if="canDelete(comment)"
                class="comment-delete-btn"
                @click="handleDelete(comment.id)">
          <el-icon :size="11"><Close /></el-icon>
        </button>
      </div>
    </div>

    <!-- 查看更多 -->
    <button v-if="comments.length > COMMENTS_PREVIEW && !showAll"
            class="comment-more-btn"
            @click="showAll = true">
      查看更多留言 ({{ comments.length - COMMENTS_PREVIEW }})
    </button>

    <p v-if="comments.length === 0" class="text-gray-400 text-sm text-center py-2">暂无留言，来说点什么吧</p>

    <!-- 输入区（只读模式隐藏） -->
    <div v-if="!readonly" class="flex gap-2 mt-2">
      <input ref="commentInputRef" v-model="commentText" placeholder="写留言..."
             class="comment-input" @keydown.enter="handleSubmit" />
      <div class="comment-emoji-area">
        <button class="comment-emoji-btn" @click="commentEmojiVisible = !commentEmojiVisible">
          🙂
        </button>
        <div ref="commentEmojiWrapperRef" class="emoji-wrapper">
          <emoji-picker
            v-if="commentEmojiVisible"
            class="emoji-picker"
            @emoji-click="handleCommentEmoji"
          />
        </div>
      </div>
      <button class="comment-send-btn" :disabled="submitting" @click="handleSubmit">
        发送
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Close } from '@element-plus/icons-vue'
import 'emoji-picker-element'
import type { BlogComment } from '@/types/blog'
import { getComments, createComment, deleteComment } from '@/api/blog'
import { getCurrentUserRole } from '@/utils/authUtils'

const COMMENTS_PREVIEW = 3

const props = defineProps<{
  postId: number
  currentUserId: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'comment-added'): void
}>()

const comments = ref<BlogComment[]>([])
const commentText = ref('')
const submitting = ref(false)
const showAll = ref(false)

// Emoji
const commentEmojiVisible = ref(false)
const commentEmojiWrapperRef = ref<HTMLElement | null>(null)
const commentInputRef = ref<HTMLInputElement | null>(null)

function handleCommentEmoji(event: any) {
  const emoji: string = event.detail.emoji.unicode
  const input = commentInputRef.value
  if (input) {
    const start = input.selectionStart
    const end = input.selectionEnd
    commentText.value =
      commentText.value.substring(0, start) + emoji + commentText.value.substring(end)
    nextTick(() => {
      const pos = start + emoji.length
      input.setSelectionRange(pos, pos)
      input.focus()
    })
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

const showAllComments = computed(() => {
  return showAll.value ? comments.value : comments.value.slice(0, COMMENTS_PREVIEW)
})

onMounted(async () => {
  try {
    const res: any = await getComments(props.postId)
    comments.value = res || []
  } catch { /* ignore */ }
})

function canDelete(comment: BlogComment): boolean {
  return getCurrentUserRole() === 'admin' || comment.author_id === props.currentUserId
}

async function handleSubmit() {
  if (!commentText.value.trim()) return
  submitting.value = true
  try {
    const res: any = await createComment(props.postId, commentText.value.trim())
    if (res) {
      comments.value.push(res)
      commentText.value = ''
      emit('comment-added')
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '评论失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(commentId: number) {
  try {
    await deleteComment(props.postId, commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
  } catch (err: any) {
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
  const time = `${pad(date.getHours())}:${pad(date.getMinutes())}`
  return `${date.getMonth() + 1}月${date.getDate()}日 ${time}`
}
</script>

<style scoped>
/* 留言删除按钮 - hover显示 */
.comment-delete-btn {
  opacity: 0;
  padding: 2px;
  color: #9ca3af;
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: opacity 0.15s, color 0.15s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
.group:hover .comment-delete-btn { opacity: 1; }
.comment-delete-btn:hover { color: #ef4444; }

/* 查看更多按钮 */
.comment-more-btn {
  background: none; border: none; color: #3b82f6; font-size: 12px;
  cursor: pointer; padding: 0; margin-bottom: 8px;
}
.comment-more-btn:hover { text-decoration: underline; }

/* 输入框和发送按钮 */
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
