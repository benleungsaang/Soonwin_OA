/** 博客 API 封装 */
import request, { multipartRequest } from '@/utils/request'
import type { AxiosProgressEvent } from 'axios'

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

/** 创建博文（支持上传进度） */
export function createPost(
  formData: FormData,
  onProgress?: (pct: number) => void
) {
  return multipartRequest.post('/api/posts', formData, {
    onUploadProgress: (e: AxiosProgressEvent) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
}

/** 更新博文（支持上传进度） */
export function updatePost(
  id: number,
  formData: FormData,
  onProgress?: (pct: number) => void
) {
  return multipartRequest.put(`/api/posts/${id}`, formData, {
    onUploadProgress: (e: AxiosProgressEvent) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
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

/** 保存草稿（支持上传进度） */
export function saveDraft(
  formData: FormData,
  onProgress?: (pct: number) => void
) {
  return multipartRequest.post('/api/posts/draft', formData, {
    onUploadProgress: (e: AxiosProgressEvent) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
}

/** 彻底删除草稿（不进回收站） */
export function deleteDraft(draftId: number) {
  return request.delete(`/api/posts/draft/${draftId}`)
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

/** 获取点赞用户列表 */
export function getPostLikes(postId: number) {
  return request.get(`/api/posts/${postId}/likes`)
}

// ============================================================
// 媒体
// ============================================================

/** 获取媒体文件 URL（走 nginx 直接发送，与视频管理一致） */
export function getMediaUrl(filePath: string): string {
  if (!filePath) return ''
  return `/assets/PostsMedia/${filePath}`
}

/** 上传单个媒体文件 */
export function uploadMedia(formData: FormData) {
  return request.post('/api/posts/media/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
