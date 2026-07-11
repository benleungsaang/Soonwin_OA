/** 任务跟踪 API 封装 */
import request, { multipartRequest } from '@/utils/request'

// ============================================================
// 任务 CRUD
// ============================================================

/** 获取任务列表 */
export function getTasks(params?: {
  page?: number
  per_page?: number
  search?: string
  status?: 'pending' | 'completed' | 'all'
  show_deleted?: '0' | '1'
}) {
  return request.get('/api/tasks', { params })
}

/** 获取任务详情 */
export function getTask(id: number) {
  return request.get(`/api/tasks/${id}`)
}

/** 创建任务（JSON 模式，无图） */
export function createTask(data: {
  content: string
  expected_date?: string
  background_color?: string
  todo_image_url?: string
}) {
  return request.post('/api/tasks', data)
}

/** 创建任务（带图片，multipart） */
export function createTaskWithImage(
  content: string,
  todoImage?: File,
  options?: { expected_date?: string; background_color?: string }
) {
  const fd = new FormData()
  fd.append('content', content)
  if (todoImage) fd.append('todo_image', todoImage)
  if (options?.expected_date) fd.append('expected_date', options.expected_date)
  if (options?.background_color) fd.append('background_color', options.background_color)
  return multipartRequest.post('/api/tasks', fd)
}

/** 更新任务（JSON 模式） */
export function updateTask(id: number, data: Partial<{
  content: string
  expected_date: string
  background_color: string
  completion_note: string
  completion_image_url: string
  todo_image_url: string
  status: 'pending' | 'completed'
}>) {
  return request.put(`/api/tasks/${id}`, data)
}

/** 软删除任务 */
export function deleteTask(id: number) {
  return request.delete(`/api/tasks/${id}`)
}

/** 恢复任务 */
export function restoreTask(id: number) {
  return request.post(`/api/tasks/${id}/restore`)
}

// ============================================================
// 留言
// ============================================================

/** 获取留言列表 */
export function getTaskComments(taskId: number) {
  return request.get(`/api/tasks/${taskId}/comments`)
}

/** 添加留言 */
export function createTaskComment(taskId: number, content: string) {
  return request.post(`/api/tasks/${taskId}/comments`, { content })
}

/** 删除留言（软删） */
export function deleteTaskComment(commentId: number) {
  return request.delete(`/api/tasks/comments/${commentId}`)
}

// ============================================================
// 点赞
// ============================================================

/** 切换点赞 */
export function toggleTaskLike(taskId: number) {
  return request.post(`/api/tasks/${taskId}/like`)
}

/** 获取点赞用户列表 */
export function getTaskLikes(taskId: number) {
  return request.get(`/api/tasks/${taskId}/likes`)
}

// ============================================================
// 可见性 / 底色 / 历史
// ============================================================

/** 设置可见性（仅管理员） */
export function updateTaskVisibility(taskId: number, visibilities: Array<{
  visibility_type: 'role' | 'employee'
  visibility_value: string
}>) {
  return request.put(`/api/tasks/${taskId}/visibility`, { visibilities })
}

/** 设置底色（hex 颜色，传空字符串清除） */
export function updateTaskBackground(taskId: number, background_color: string) {
  return request.put(`/api/tasks/${taskId}/background`, { background_color })
}

/** 获取修改历史（仅管理员） */
export function getTaskHistory(taskId: number) {
  return request.get(`/api/tasks/${taskId}/history`)
}

// ============================================================
// 通知
// ============================================================

/** 获取未读通知（当前用户可见卡片内） */
export function getTaskNotifications() {
  return request.get('/api/tasks/notifications')
}

/** 清除全部通知 */
export function clearTaskNotifications() {
  return request.post('/api/tasks/notifications/clear')
}

// ============================================================
// 可见性辅助数据（管理员）
// ============================================================

/** 获取所有 SimpleRole 列表（仅管理员） */
export function getAllRoles() {
  return request.get<Array<{ id: number; name: string; remark: string }>>('/api/admin/all-roles')
}

/** 获取所有 Employee 列表（仅管理员，最小化字段） */
export function getAllEmployees() {
  return request.get<Array<{ emp_id: string; name: string }>>('/api/admin/all-employees')
}

/** 获取任务附图 URL（走 nginx，与博客一致） */
export function getTaskMediaUrl(filePath: string): string {
  if (!filePath) return ''
  return `/assets/TasksMedia/${filePath}`
}