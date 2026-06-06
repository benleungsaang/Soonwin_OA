/** 博客媒体文件 */
export interface BlogMedia {
  id: number
  post_id: number
  media_type: 'image' | 'video'
  file_path: string
  thumbnail_path: string
  display_path: string  // 展示用 WebP（1600px，展开轮播使用，灯箱才加载原图 file_path）
  has_v2_thumbnails: boolean  // 是否已生成 v2 WebP 缩略图（旧图片为 false，无需 DB 查询）
  original_filename: string
  file_size: number
  width: number
  height: number
  duration: number
  compress_status: 'pending' | 'processing' | 'success' | 'failed'
  created_at: string
}

/** 博文 */
export interface BlogPost {
  id: number
  content: string
  author: string
  author_id: string
  is_draft: boolean
  is_deleted: boolean
  repost_from: number | null
  repost?: BlogPost | null
  edit_version: number
  comment_count: number
  like_count: number
  favorite_count: number
  is_liked: boolean
  is_favorited: boolean
  media: BlogMedia[]
  created_at: string
  updated_at: string
  deleted_at?: string
  deleted_by?: string
}

/** 评论 */
export interface BlogComment {
  id: number
  post_id: number
  author: string
  author_id: string
  content: string
  is_deleted: boolean
  created_at: string
}

/** 编辑历史 */
export interface BlogEditHistory {
  id: number
  post_id: number
  version: number
  content?: string
  media_snapshot?: string
  edited_by: string
  created_at: string
}

/** 博文列表响应 */
export interface BlogListResponse {
  posts: BlogPost[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/** 创建/更新博文的表单数据 */
export interface BlogFormData {
  content: string
  files: File[]
  keepMediaIds?: number[]
  repost_from?: number
}
