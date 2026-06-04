<template>
  <div class="bg-gray-50 border-t border-gray-100 px-4 py-3">
    <!-- 评论列表 -->
    <div v-if="showAllComments.length > 0" class="space-y-1.5 mb-2" :class="showAll ? '' : 'max-h-48 overflow-hidden'">
      <div v-for="comment in showAllComments" :key="comment.id" class="flex items-start gap-2 py-1 group">
        <div class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
          <el-icon :size="12" color="#6b7280"><UserFilled /></el-icon>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium text-gray-600">{{ comment.author }}</span>
            <span class="text-xs text-gray-400">{{ formatTime(comment.created_at) }}</span>
          </div>
          <p class="text-sm text-gray-500 mt-0.5 break-words">{{ comment.content }}</p>
        </div>
        <button v-if="canDelete(comment)"
                class="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 rounded transition-opacity flex-shrink-0"
                @click="handleDelete(comment.id)">
          <el-icon :size="12"><Close /></el-icon>
        </button>
      </div>
    </div>

    <!-- 查看更多 -->
    <button v-if="comments.length > COMMENTS_PREVIEW && !showAll"
            class="text-blue-500 text-xs hover:underline mb-2"
            @click="showAll = true">
      查看更多留言 ({{ comments.length - COMMENTS_PREVIEW }})
    </button>

    <p v-if="comments.length === 0" class="text-gray-400 text-sm text-center py-2">暂无留言，来说点什么吧</p>

    <!-- 输入区 -->
    <div class="flex gap-2 mt-2">
      <input v-model="commentText"
             :placeholder="'写留言...'"
             class="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg
                    focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
             @keydown.enter="handleSubmit" />
      <button class="px-3 py-1.5 bg-blue-500 text-white text-sm rounded-lg
                     hover:bg-blue-600 flex-shrink-0 transition-colors"
              :disabled="submitting" @click="handleSubmit">
        发送
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Close } from '@element-plus/icons-vue'
import type { BlogComment } from '@/types/blog'
import { getComments, createComment, deleteComment } from '@/api/blog'
import { getCurrentUserRole } from '@/utils/authUtils'

const COMMENTS_PREVIEW = 3

const props = defineProps<{
  postId: number
  currentUserId: string
}>()

const emit = defineEmits<{
  (e: 'comment-added'): void
}>()

const comments = ref<BlogComment[]>([])
const commentText = ref('')
const submitting = ref(false)
const showAll = ref(false)

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
