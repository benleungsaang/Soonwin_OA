<template>
  <div class="comment-section">
    <!-- 评论列表 -->
    <div v-if="comments.length > 0" class="comment-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-header">
          <span class="comment-author">{{ comment.author }}</span>
          <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          <el-button
            v-if="canDelete(comment)"
            text
            size="small"
            type="danger"
            @click="handleDelete(comment.id)"
          >删除</el-button>
        </div>
        <div class="comment-content">{{ comment.content }}</div>
      </div>
    </div>

    <!-- 评论输入 -->
    <div class="comment-input-area">
      <el-input
        v-model="commentText"
        placeholder="写下你的评论..."
        maxlength="500"
        @keyup.enter="handleSubmit"
      >
        <template #append>
          <el-button :loading="submitting" @click="handleSubmit">发送</el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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
  } catch {
    // ignore
  }
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
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return dateStr.slice(0, 16)
}
</script>

<style scoped>
.comment-section {
  margin-top: 12px;
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.comment-list {
  margin-bottom: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.comment-item {
  padding: 8px 0;
  border-bottom: 1px dashed #f2f3f5;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.comment-author {
  font-weight: 600;
  color: #409eff;
}

.comment-time {
  color: #c0c4cc;
  font-size: 12px;
}

.comment-content {
  margin-top: 4px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.comment-input-area {
  margin-top: 8px;
}
</style>
