<template>
  <div class="blog-page">
    <CommonHeader title="微博客" />

    <div class="blog-container">
      <!-- 顶部操作栏 -->
      <div class="blog-toolbar">
        <div class="toolbar-left">
          <el-radio-group v-model="activeTab" size="small" @change="onTabChange">
            <el-radio-button value="published">全部博文</el-radio-button>
            <el-radio-button v-if="draftCount > 0" value="draft">草稿{{ draftCount > 0 ? `(${draftCount})` : '' }}</el-radio-button>
            <el-radio-button v-if="isAdmin" value="deleted">回收站</el-radio-button>
          </el-radio-group>
        </div>
        <div class="toolbar-right">
          <el-input
            v-if="activeTab === 'published'"
            v-model="searchKeyword"
            placeholder="搜索博文..."
            clearable
            :prefix-icon="Search"
            style="width: 240px"
            @clear="loadPosts"
            @keyup.enter="loadPosts"
          />
          <el-button type="primary" @click="openCreateDialog" v-if="activeTab !== 'deleted'">
            <el-icon><Plus /></el-icon> 发布博文
          </el-button>
        </div>
      </div>

      <!-- 博文列表 -->
      <div v-loading="loading" class="blog-feed">
        <template v-if="posts.length > 0">
          <BlogPostCard
            v-for="post in posts"
            :key="post.id"
            :post="post"
            :show-actions="true"
            :ref="setPostCardRef(post.id)"
            @edit="openEditDialog(post)"
            @delete="handleDelete(post)"
            @toggle-like="handleToggleLike(post)"
            @media-click="handleMediaClick"
          />

          <!-- 分页 -->
          <div v-if="totalPages > 1" class="blog-pagination">
            <el-pagination
              v-model:current-page="currentPage"
              :total="total"
              :page-size="perPage"
              layout="prev, pager, next"
              @current-change="loadPosts"
            />
          </div>
        </template>

        <el-empty v-else-if="!loading" :description="emptyText" />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <BlogCreateDialog
      v-model:visible="showCreateDialog"
      :post="editingPost"
      @saved="onPostSaved"
      @draft-saved="onDraftSaved"
    />

    <!-- 媒体 Lightbox -->
    <BlogMediaLightbox
      v-model:visible="showLightbox"
      :media-list="lightboxMediaList"
      :initial-index="lightboxIndex"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import CommonHeader from '@/components/CommonHeader.vue'
import BlogPostCard from '@/components/BlogPostCard.vue'
import BlogCreateDialog from '@/components/BlogCreateDialog.vue'
import BlogMediaLightbox from '@/components/BlogMediaLightbox.vue'
import type { BlogPost, BlogMedia } from '@/types/blog'
import {
  getPosts, getPost, getDraft, deletePost, deleteDraft, toggleLike,
  getDeletedPosts, restorePost, permanentDeletePosts,
} from '@/api/blog'
import { getCurrentUserRole } from '@/utils/authUtils'

const loading = ref(false)
const posts = ref<BlogPost[]>([])
const currentPage = ref(1)
const perPage = ref(20)
const total = ref(0)
const totalPages = ref(0)
const searchKeyword = ref('')
const activeTab = ref<'published' | 'draft' | 'deleted'>('published')

const showCreateDialog = ref(false)
const editingPost = ref<BlogPost | null>(null)
const draftCount = ref(0)

const showLightbox = ref(false)
const lightboxMediaList = ref<BlogMedia[]>([])
const lightboxIndex = ref(0)

// Post card refs for calling methods like loadHistory
const postCardRefs: Record<number, any> = {}

const isAdmin = computed(() => getCurrentUserRole() === 'admin')

const emptyText = computed(() => {
  if (activeTab.value === 'deleted') return '回收站为空'
  if (activeTab.value === 'draft') return '暂无草稿'
  if (searchKeyword.value) return '未找到匹配的博文'
  return '暂无博文，快来发布第一条吧！'
})

function setPostCardRef(postId: number) {
  return (el: any) => {
    if (el) postCardRefs[postId] = el
  }
}

onMounted(async () => {
  await loadPosts()
  checkDraft()
})

async function checkDraft() {
  try {
    const res: any = await getDraft()
    draftCount.value = Array.isArray(res) ? res.length : (res ? 1 : 0)
  } catch { /* ignore */ }
}

async function loadPosts() {
  loading.value = true
  try {
    let res: any
    if (activeTab.value === 'deleted') {
      res = await getDeletedPosts({ page: currentPage.value, per_page: perPage.value })
    } else if (activeTab.value === 'draft') {
      const drafts: any = await getDraft()
      posts.value = Array.isArray(drafts) ? drafts : (drafts ? [drafts] : [])
      total.value = posts.value.length
      totalPages.value = 1
      loading.value = false
      return
    } else {
      res = await getPosts({
        page: currentPage.value,
        per_page: perPage.value,
        search: searchKeyword.value,
      })
    }
    if (res) {
      posts.value = res.posts || []
      total.value = res.total || 0
      totalPages.value = res.total_pages || 0
    }
  } catch (err: any) {
    ElMessage.error('加载博文失败')
  } finally {
    loading.value = false
  }
}

function onTabChange() {
  currentPage.value = 1
  loadPosts()
}

function openCreateDialog() {
  editingPost.value = null
  showCreateDialog.value = true
}

function openEditDialog(post: BlogPost) {
  editingPost.value = post
  showCreateDialog.value = true
}

async function onPostSaved() {
  showCreateDialog.value = false
  editingPost.value = null
  currentPage.value = 1
  await loadPosts()
  await checkDraft()
}

async function onDraftSaved() {
  await checkDraft()
}

async function handleDelete(post: BlogPost) {
  let action: string
  if (activeTab.value === 'deleted') {
    action = '彻底删除后将无法恢复，确定删除？'
  } else if (post.is_draft) {
    action = '确定彻底删除此草稿？此操作不可恢复。'
  } else {
    action = '确定将此博文移至回收站？'
  }
  try {
    await ElMessageBox.confirm(action, '提示', { type: 'warning' })
    if (activeTab.value === 'deleted') {
      await permanentDeletePosts([post.id])
      ElMessage.success('已彻底删除')
    } else if (post.is_draft) {
      await deleteDraft(post.id)
      ElMessage.success('草稿已删除')
    } else {
      await deletePost(post.id)
      ElMessage.success('已移至回收站')
    }
    await loadPosts()
    if (post.is_draft) await checkDraft()
  } catch { /* cancelled */ }
}

async function handleRestore(post: BlogPost) {
  try {
    await ElMessageBox.confirm('确定恢复此博文？', '提示', { type: 'info' })
    await restorePost(post.id)
    ElMessage.success('已恢复')
    await loadPosts()
  } catch { /* cancelled */ }
}

async function handleToggleLike(post: BlogPost) {
  try {
    const res: any = await toggleLike(post.id)
    if (res) {
      post.is_liked = res.liked
      post.like_count += res.liked ? 1 : -1
    }
  } catch { /* ignore */ }
}

function handleMediaClick(media: any, index: number, mediaList?: any[]) {
  // 如果传入了第三个参数（来自历史版本），直接使用
  if (mediaList) {
    lightboxMediaList.value = mediaList
    lightboxIndex.value = index
    showLightbox.value = true
    return
  }
  // 否则在当前博文列表中查找
  for (const post of posts.value) {
    const idx = post.media.findIndex(m => m.id === media.id)
    if (idx >= 0) {
      lightboxMediaList.value = post.media.filter(
        m => m.media_type === 'image' || (m.media_type === 'video' && m.compress_status !== 'pending')
      )
      lightboxIndex.value = lightboxMediaList.value.findIndex(m => m.id === media.id)
      showLightbox.value = true
      return
    }
  }
}
</script>

<style scoped>
.blog-page {
  min-height: 100vh;
  background: #f3f4f6;
}

.blog-container {
  max-width: 672px;
  margin: 0 auto;
  padding: 16px 16px;
}

@media (max-width: 768px) {
  .blog-container {
    padding: 12px 8px;
  }
}

.blog-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.blog-feed {
  min-height: 300px;
}

.blog-pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
