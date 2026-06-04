<template>
  <div class="border-t border-gray-100 bg-gray-50/50 px-4 py-3">
    <!-- 评论列表 -->
    <div v-if="comments.length > 0" class="space-y-3 mb-3 max-h-72 overflow-y-auto">
      <div v-for="comment in comments" :key="comment.id" class="flex gap-2.5">
        <el-avatar :size="28" :icon="UserFilled" class="flex-shrink-0" />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-semibold text-blue-500">{{ comment.author }}</span>
            <span class="text-[11px] text-gray-300">{{ formatTime(comment.created_at) }}</span>
            <el-button v-if="canDelete(comment)" text size="small" type="danger"
                       class="!ml-auto !p-0 !h-auto !text-[11px]" @click="handleDelete(comment.id)">
              删除
            </el-button>
          </div>
          <p class="text-sm text-gray-700 mt-0.5 break-words leading-relaxed">{{ comment.content }}</p>
        </div>
      </div>
    </div>

    <!-- 评论输入 -->
    <div class="flex gap-2 items-center">
      <el-input v-model="commentText" placeholder="写下评论..." maxlength="500"
                size="small" class="flex-1" @keyup.enter="handleSubmit" />
      <el-button size="small" type="primary" :loading="submitting" @click="handleSubmit" class="flex-shrink-0">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import type { BlogComment } from '@/types/blog'
import { getComments, createComment, deleteComment } from '@/api/blog'
import { getCurrentUserRole, getCurrentUserEmpId } from '@/utils/authUtils'

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
    ElMessage.success('评论已删除')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.message || '删除失败')
  }
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr.replace(/-/g, '/'))
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
  return dateStr.slice(0, 10)
}
</script>
