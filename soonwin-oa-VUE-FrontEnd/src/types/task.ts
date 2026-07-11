/** 任务可见性配置 */
export interface TaskVisibility {
  id: number
  task_id: number
  visibility_type: 'role' | 'employee'
  visibility_value: string
  created_at: string
}

/** 任务 */
export interface Task {
  id: number
  author_id: string
  author_name: string
  content: string
  status: 'pending' | 'completed'
  completion_note: string
  completion_image_url: string
  todo_image_url: string
  expected_date: string  // YYYY-MM-DD 或 ''
  background_color: string  // hex 颜色，如 "#ff5500" 或 ''
  like_count: number
  is_deleted: boolean
  comment_count: number
  is_liked: boolean
  created_at: string
  updated_at: string
  completed_at: string | null
  visibilities?: TaskVisibility[]
}

/** 任务留言 */
export interface TaskComment {
  id: number
  task_id: number
  author_id: string
  author_name: string
  content: string
  is_deleted: boolean
  deleted_at: string | null
  deleted_by: string
  created_at: string
}

/** 任务修改历史 */
export interface TaskHistory {
  id: number
  task_id: number
  modified_by: string
  modified_at: string
  snapshot?: string
}

/** 任务列表响应 */
export interface TaskListResponse {
  tasks: Task[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/** 通知项（留言/点赞） */
export interface TaskNotificationComment {
  id: number
  task_id: number
  author_name: string
  author_id: string
  content: string
  created_at: string
  task_content_preview: string
}

export interface TaskNotificationLike {
  task_id: number
  user_id: string
  name: string
  created_at: string
  task_content_preview: string
}

export interface TaskNotificationsResponse {
  comments: TaskNotificationComment[]
  likes: TaskNotificationLike[]
  unread_count: number
}

/** 创建任务的表单 */
export interface TaskFormData {
  content: string
  expected_date?: string
  background_color?: string
  todo_image?: File
}