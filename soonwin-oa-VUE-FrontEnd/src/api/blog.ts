/** 博客 API 封装 */
import request, { multipartRequest } from '@/utils/request'
import type { AxiosProgressEvent } from 'axios'

// ============================================================
// 类型定义
// ============================================================

/** 预上传媒体文件的返回信息（两阶段上传） */
export interface UploadedMediaInfo {
  file_path: string
  thumbnail_path: string
  media_type: 'image' | 'video'
  file_size: number
  filename: string
  width: number
  height: number
  duration: number
}

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

/** 切换收藏 */
export function toggleFavorite(postId: number) {
  return request.post(`/api/posts/${postId}/favorite`)
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

/** 上传单个媒体文件（两阶段上传的阶段一：独立超时 + 进度）
 *
 * 与旧版 uploadMedia 的关键区别：
 * 1. 使用 multipartRequest（超时更长）而非 request（15s）
 * 2. 支持 onProgress 回调，前端可显示每个文件的上传进度
 * 3. 每个文件独立请求，不会因为合并上传大文件导致超时误报
 * 4. 后端完整处理（图片缩略图 + 视频元数据提取），不堆积到 POST /posts
 */
export function uploadSingleFile(
  file: File,
  onProgress?: (pct: number) => void
): Promise<UploadedMediaInfo> {
  const fd = new FormData()
  fd.append('file', file)
  return multipartRequest.post('/api/posts/media/upload', fd, {
    timeout: 120000, // 单文件 2 分钟，足够大文件上传
    onUploadProgress: (e: AxiosProgressEvent) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
}

/** 上传单个媒体文件（旧接口，保留向后兼容） */
export function uploadMedia(formData: FormData) {
  return multipartRequest.post('/api/posts/media/upload', formData, {
    timeout: 120000,
  })
}

// ============================================================
// 两阶段上传 API（推荐使用，根治超时问题）
// ============================================================

/** 创建博文（使用已上传的文件引用，不含二进制数据，请求瞬间完成） */
export function createPostFromUploaded(
  content: string,
  uploadedMedia: UploadedMediaInfo[],
  repostFrom?: number
) {
  const fd = new FormData()
  fd.append('content', content)
  fd.append('uploaded_media', JSON.stringify(uploadedMedia))
  if (repostFrom) fd.append('repost_from', String(repostFrom))
  return multipartRequest.post('/api/posts', fd)
}

/** 更新博文（使用已上传的文件引用） */
export function updatePostFromUploaded(
  id: number,
  content: string,
  uploadedMedia: UploadedMediaInfo[],
  keepMediaIds: number[]
) {
  const fd = new FormData()
  fd.append('content', content)
  fd.append('uploaded_media', JSON.stringify(uploadedMedia))
  fd.append('keep_media_ids', keepMediaIds.join(','))
  return multipartRequest.put(`/api/posts/${id}`, fd)
}

/** 保存草稿（使用已上传的文件引用） */
export function saveDraftFromUploaded(
  content: string,
  uploadedMedia: UploadedMediaInfo[]
) {
  const fd = new FormData()
  fd.append('content', content)
  fd.append('uploaded_media', JSON.stringify(uploadedMedia))
  return multipartRequest.post('/api/posts/draft', fd)
}
