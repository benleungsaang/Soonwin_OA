<template>
  <div class="blog-page">
    <CommonHeader title="微博客" />

    <div class="blog-container">
      <!-- 发布框（内联） -->
      <div v-if="activeTab !== 'deleted'" class="publish-box">
        <div class="flex gap-3">
          <div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
            <el-icon :size="20" color="#3b82f6"><UserFilled /></el-icon>
          </div>
          <div class="flex-1">
            <textarea v-model="publishContent" placeholder="分享生活点滴..." rows="3"
              class="publish-textarea"
              @paste="onPublishPaste" @dragover.prevent @drop.prevent="onPublishDrop" />
            <!-- 媒体预览 -->
            <div v-if="publishFiles.length > 0" class="flex flex-wrap gap-2 mt-2">
              <div v-for="(f, i) in publishFiles" :key="i" class="publish-preview-item">
                <img v-if="f.type === 'image'" :src="f.url" class="w-full h-full object-cover" />
                <video v-else :src="f.url" class="w-full h-full object-cover" />
                <button class="publish-preview-remove" @click="removePublishFile(i)">&times;</button>
              </div>
            </div>
            <div class="flex items-center justify-between pt-3 border-t border-gray-100 mt-2">
              <div class="flex gap-2">
                <label class="publish-upload-btn">
                  <el-icon :size="16"><PictureFilled /></el-icon><span class="text-sm ml-1">图片</span>
                  <input type="file" accept="image/*" multiple hidden @change="onPublishImageSelect" />
                </label>
                <label class="publish-upload-btn">
                  <el-icon :size="16"><VideoCamera /></el-icon><span class="text-sm ml-1">视频</span>
                  <input type="file" accept="video/*" hidden @change="onPublishVideoSelect" />
                </label>
              </div>
              <button class="publish-submit-btn" :disabled="publishing" @click="handlePublish">
                {{ publishing ? '发布中...' : '发布' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 搜索栏 -->
      <div v-if="activeTab === 'published'" class="search-box">
        <el-icon :size="16" color="#9ca3af" class="absolute left-3 top-1/2 -translate-y-1/2"><Search /></el-icon>
        <input v-model="searchKeyword" placeholder="搜索动态..." @input="onSearchInput"
          class="search-input" />
      </div>

      <!-- 工具栏标签 -->
      <div class="blog-tabs">
        <button v-for="tab in tabs" :key="tab.key" @click="switchTab(tab.key)"
          class="blog-tab" :class="{ active: activeTab === tab.key }">
          {{ tab.label }}
          <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
        </button>
      </div>

      <!-- 博文列表 -->
      <div v-loading="loading" class="blog-feed">
        <template v-if="posts.length > 0">
          <BlogPostCard
            v-for="post in posts" :key="post.id" :post="post" :show-actions="true"
            :readonly="activeTab === 'deleted'"
            @edit="openEditDialog(post)"
            @delete="handleDelete(post)"
            @toggle-like="handleToggleLike(post)"
            @media-click="handleMediaClick" />

          <div v-if="totalPages > 1" class="flex justify-center mt-6">
            <el-pagination v-model:current-page="currentPage" :total="total"
              :page-size="perPage" layout="prev, pager, next" @current-change="loadPosts" />
          </div>
        </template>
        <el-empty v-else-if="!loading" :description="emptyText" />
      </div>
    </div>

    <!-- 编辑对话框 -->
    <BlogCreateDialog v-model:visible="showCreateDialog" :post="editingPost"
      @saved="onPostSaved" @draft-saved="onDraftSaved" />

    <!-- 媒体 Lightbox -->
    <BlogMediaLightbox v-model:visible="showLightbox" :media-list="lightboxMediaList"
      :initial-index="lightboxIndex" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, PictureFilled, VideoCamera, UserFilled } from '@element-plus/icons-vue'
import CommonHeader from '@/components/CommonHeader.vue'
import BlogPostCard from '@/components/BlogPostCard.vue'
import BlogCreateDialog from '@/components/BlogCreateDialog.vue'
import BlogMediaLightbox from '@/components/BlogMediaLightbox.vue'
import type { BlogPost, BlogMedia } from '@/types/blog'
import {
  getPosts, getDraft, deletePost, deleteDraft, toggleLike,
  getDeletedPosts, restorePost, permanentDeletePosts, createPost,
} from '@/api/blog'
import { getCurrentUserRole } from '@/utils/authUtils'
import request from '@/utils/request'

const loading = ref(false)
const posts = ref<BlogPost[]>([])
const currentPage = ref(1)
const perPage = ref(20)
const total = ref(0)
const totalPages = ref(0)
const searchKeyword = ref('')
const activeTab = ref<'published' | 'favorites' | 'draft' | 'deleted'>('published')

const showCreateDialog = ref(false)
const editingPost = ref<BlogPost | null>(null)
const draftCount = ref(0)

const showLightbox = ref(false)
const lightboxMediaList = ref<BlogMedia[]>([])
const lightboxIndex = ref(0)

const isAdmin = computed(() => getCurrentUserRole() === 'admin')

const tabs = computed(() => {
  const list: any[] = [{ key: 'published', label: '全部博文' }]
  list.push({ key: 'favorites', label: '收藏' })
  if (draftCount.value > 0) list.push({ key: 'draft', label: '草稿', badge: draftCount.value })
  if (isAdmin.value) list.push({ key: 'deleted', label: '回收站' })
  return list
})

const emptyText = computed(() => {
  if (activeTab.value === 'deleted') return '回收站为空'
  if (activeTab.value === 'draft') return '暂无草稿'
  if (activeTab.value === 'favorites') return '暂无收藏'
  if (searchKeyword.value) return '未找到匹配的博文'
  return '暂无博文，快来发布第一条吧！'
})

// ===== 内联发布 =====
const publishContent = ref('')
const publishFiles = ref<{ type: string; url: string; file: File }[]>([])
const publishing = ref(false)

function addPublishFiles(files: FileList | File[]) {
  for (let i = 0; i < files.length; i++) {
    const f = files[i]
    if (!f.type.startsWith('image/') && !f.type.startsWith('video/')) continue
    publishFiles.value.push({ type: f.type.startsWith('video/') ? 'video' : 'image', url: URL.createObjectURL(f), file: f })
  }
}
function onPublishImageSelect(e: Event) { const inp = e.target as HTMLInputElement; if (inp.files) addPublishFiles(inp.files); inp.value = '' }
function onPublishVideoSelect(e: Event) { const inp = e.target as HTMLInputElement; if (inp.files) addPublishFiles(inp.files); inp.value = '' }
function onPublishPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items; if (!items) return
  const files: File[] = []
  for (let i = 0; i < items.length; i++) { const f = items[i].getAsFile(); if (f) files.push(f) }
  if (files.length > 0) { e.preventDefault(); addPublishFiles(files) }
}
function onPublishDrop(e: DragEvent) { if (e.dataTransfer?.files) addPublishFiles(e.dataTransfer.files) }
function removePublishFile(i: number) { URL.revokeObjectURL(publishFiles.value[i].url); publishFiles.value.splice(i, 1) }

async function handlePublish() {
  if (!publishContent.value.trim() && publishFiles.value.length === 0) { ElMessage.warning('请输入内容或添加媒体'); return }
  publishing.value = true
  try {
    const fd = new FormData(); fd.append('content', publishContent.value)
    publishFiles.value.forEach(f => fd.append('media', f.file))
    await createPost(fd)
    ElMessage.success('发布成功')
    publishContent.value = ''
    publishFiles.value.forEach(f => URL.revokeObjectURL(f.url))
    publishFiles.value = []
    currentPage.value = 1; activeTab.value = 'published'; await loadPosts()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '发布失败') }
  finally { publishing.value = false }
}

// ===== 数据加载 =====
onMounted(async () => { await loadPosts(); checkDraft() })

let searchTimer: any = null
function onSearchInput() { clearTimeout(searchTimer); searchTimer = setTimeout(() => { currentPage.value = 1; loadPosts() }, 300) }

function switchTab(key: string) { activeTab.value = key as any; currentPage.value = 1; loadPosts() }

async function checkDraft() {
  try { const res: any = await getDraft(); draftCount.value = Array.isArray(res) ? res.length : (res ? 1 : 0) }
  catch { /* ignore */ }
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
      total.value = posts.value.length; totalPages.value = 1; loading.value = false; return
    } else if (activeTab.value === 'favorites') {
      res = await request.get('/api/posts/favorites', { params: { page: currentPage.value, per_page: perPage.value } })
    } else {
      res = await getPosts({ page: currentPage.value, per_page: perPage.value, search: searchKeyword.value })
    }
    if (res) { posts.value = res.posts || []; total.value = res.total || 0; totalPages.value = res.total_pages || 0 }
  } catch (e: any) { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openEditDialog(post: BlogPost) { editingPost.value = post; showCreateDialog.value = true }
async function onPostSaved() { showCreateDialog.value = false; editingPost.value = null; currentPage.value = 1; await loadPosts(); await checkDraft() }
async function onDraftSaved() { await checkDraft() }

async function handleDelete(post: BlogPost) {
  let action: string
  if (activeTab.value === 'deleted') { action = '彻底删除后将无法恢复，确定删除？' }
  else if (post.is_draft) { action = '确定彻底删除此草稿？' }
  else { action = '确定将此博文移至回收站？' }
  try {
    await ElMessageBox.confirm(action, '提示', { type: 'warning' })
    if (activeTab.value === 'deleted') { await permanentDeletePosts([post.id]); ElMessage.success('已彻底删除') }
    else if (post.is_draft) { await deleteDraft(post.id); ElMessage.success('草稿已删除') }
    else { await deletePost(post.id); ElMessage.success('已移至回收站') }
    await loadPosts(); if (post.is_draft) await checkDraft()
  } catch { /* cancelled */ }
}

async function handleToggleLike(post: BlogPost) {
  try { const res: any = await toggleLike(post.id); if (res) { post.is_liked = res.liked; post.like_count += res.liked ? 1 : -1 } }
  catch { /* ignore */ }
}

function handleMediaClick(media: any, index: number, mediaList?: any[]) {
  if (mediaList) { lightboxMediaList.value = mediaList; lightboxIndex.value = index; showLightbox.value = true; return }
  for (const post of posts.value) {
    const idx = post.media.findIndex(m => m.id === media.id)
    if (idx >= 0) {
      lightboxMediaList.value = post.media.filter((m: any) => m.media_type === 'image' || (m.media_type === 'video' && m.compress_status !== 'pending'))
      lightboxIndex.value = lightboxMediaList.value.findIndex(m => m.id === media.id); showLightbox.value = true; return
    }
  }
}
</script>

<style scoped>
.blog-page { min-height: 100vh; background: #f3f4f6; }
.blog-container { max-width: 672px; margin: 0 auto; padding: 16px; }
@media (max-width: 768px) { .blog-container { padding: 12px 8px; } }

/* 发布框 */
.publish-box { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 16px; margin-bottom: 16px; }
.publish-textarea { width: 100%; border: 0; resize: none; outline: none; font-size: 15px; color: #1f2937; padding: 8px; background: transparent; }
.publish-textarea::placeholder { color: #9ca3af; }
.publish-upload-btn { display: flex; align-items: center; padding: 8px 10px; color: #9ca3af; cursor: pointer; border-radius: 8px; transition: all 0.15s; }
.publish-upload-btn:hover { color: #3b82f6; background: #f3f4f6; }
.publish-submit-btn { background: #3b82f6; color: #fff; border: none; padding: 8px 24px; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.15s; }
.publish-submit-btn:hover { background: #2563eb; }
.publish-submit-btn:disabled { opacity: 0.6; cursor: default; }
.publish-preview-item { position: relative; width: 72px; height: 72px; border-radius: 8px; overflow: hidden; border: 1px solid rgba(0,0,0,0.06); }
.publish-preview-remove { position: absolute; top: 2px; right: 2px; width: 18px; height: 18px; background: #ef4444; color: #fff; border: none; border-radius: 50%; font-size: 12px; line-height: 1; cursor: pointer; display: flex; align-items: center; justify-content: center; }

/* 搜索框 */
.search-box { position: relative; margin-bottom: 12px; }
.search-input { width: 100%; padding: 10px 16px 10px 38px; border: 1px solid #e5e7eb; border-radius: 12px; font-size: 14px; outline: none; background: #fff; transition: border-color 0.15s; box-sizing: border-box; }
.search-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.1); }

/* 工具栏 */
.blog-tabs { display: flex; gap: 4px; margin-bottom: 16px; background: #fff; border-radius: 10px; padding: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.blog-tab { flex: 1; padding: 8px 0; border: none; background: transparent; border-radius: 8px; font-size: 13px; color: #6b7280; cursor: pointer; transition: all 0.15s; position: relative; display: flex; align-items: center; justify-content: center; gap: 4px; }
.blog-tab:hover { color: #374151; background: #f3f4f6; }
.blog-tab.active { color: #3b82f6; background: #eff6ff; font-weight: 500; }
.tab-badge { font-size: 11px; background: #3b82f6; color: #fff; border-radius: 10px; padding: 1px 6px; min-width: 16px; text-align: center; }

.blog-feed { min-height: 300px; }
</style>
