/** 博客 API 封装 */
import request from '@/utils/request'

// ============================================================
// 博文 CRUD
// ============================================================

/** 获取已发布博文列表 */
export function getPosts(params?: {
  page?: number
  per_page?: number
  search?: string
}) {
  return request.get('/api/posts', { params })
}

/** 获取单篇博文 */
export function getPost(id: number) {
  return request.get(`/api/posts/${id}`)
}

/** 创建博文 */
export function createPost(formData: FormData) {
  return request.post('/api/posts', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 更新博文 */
export function updatePost(id: number, formData: FormData) {
  return request.put(`/api/posts/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 软删除博文 */
export function deletePost(id: number) {
  return request.delete(`/api/posts/${id}`)
}

// ============================================================
// 草稿
// ============================================================

/** 获取当前用户草稿 */
export function getDraft() {
  return request.get('/api/posts/draft')
}

/** 保存草稿 */
export function saveDraft(formData: FormData) {
  return request.post('/api/posts/draft', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 删除草稿 */
export function deleteDraft() {
  return request.delete('/api/posts/draft')
}

/** 发布草稿 */
export function publishDraft(id: number) {
  return request.put(`/api/posts/${id}/publish`)
}

// ============================================================
// 回收站（管理员）
// ============================================================

/** 获取已删除博文 */
export function getDeletedPosts(params?: {
  page?: number
  per_page?: number
}) {
  return request.get('/api/posts/deleted', { params })
}

/** 恢复已删除博文 */
export function restorePost(id: number) {
  return request.put(`/api/posts/${id}/restore`)
}

/** 彻底删除 */
export function permanentDeletePosts(ids: number[]) {
  return request.delete('/api/posts/permanent-delete', {
    data: { post_ids: ids },
  })
}

// ============================================================
// 编辑历史（管理员）
// ============================================================

/** 获取编辑历史 */
export function getEditHistory(postId: number) {
  return request.get(`/api/posts/${postId}/history`)
}

/** 获取特定版本 */
export function getHistoryVersion(postId: number, version: number) {
  return request.get(`/api/posts/${postId}/history/${version}`)
}

// ============================================================
// 评论
// ============================================================

/** 获取评论 */
export function getComments(postId: number) {
  return request.get(`/api/posts/${postId}/comments`)
}

/** 添加评论 */
export function createComment(postId: number, content: string) {
  return request.post(`/api/posts/${postId}/comments`, { content })
}

/** 删除评论 */
export function deleteComment(postId: number, commentId: number) {
  return request.delete(`/api/posts/${postId}/comments/${commentId}`)
}

// ============================================================
// 点赞
// ============================================================

/** 切换点赞 */
export function toggleLike(postId: number) {
  return request.post(`/api/posts/${postId}/like`)
}

// ============================================================
// 媒体
// ============================================================

/** 获取媒体文件 URL */
export function getMediaUrl(filePath: string): string {
  if (!filePath) return ''
  return `/api/posts/media/${filePath}`
}

/** 上传单个媒体文件 */
export function uploadMedia(formData: FormData) {
  return request.post('/api/posts/media/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
