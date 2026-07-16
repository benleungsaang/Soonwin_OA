/**
 * 待办事项（Todo）API 封装
 *
 * 设计要点：
 * - request 已自动解包 data 字段，直接 await 拿业务数据
 * - 用户隔离：后端按 author_id 过滤（管理员看全部）
 * - 管理员或任务创建人可添加留言，仅管理员可删除留言
 * - emoji 直接通过 JSON 传输，无需特殊处理
 */
import request, { multipartRequest } from '@/utils/request'

// ============================================================
// 类型定义
// ============================================================
export interface TodoItem {
  id: number
  author_id: string
  author_name: string
  content: string
  date: string                  // YYYY-MM-DD（按它分组）
  color: string                 // white/red/yellow/green/blue/purple
  note: string
  image_url: string
  status: 'pending' | 'completed'
  completion_note: string
  completion_image_url: string
  completed_at: string | null
  is_deleted: boolean
  unread_count: number
  created_at: string
  updated_at: string
  messages?: TodoMessage[]       // 仅详情接口返回
}

export interface TodoMessage {
  id: number
  todo_id: number
  author_id: string
  author_name: string
  content: string
  is_deleted: boolean
  created_at: string
}

export interface TodoNotification {
  todo_id: number
  unread_count: number
  latest_message: {
    id: number
    content: string
    author_name: string
    created_at: string
  }
  todo_content_preview: string
}

// ============================================================
// Todo CRUD
// ============================================================

/** 获取 todo 列表 */
export function getTodos(params?: {
  search?: string
  status?: 'pending' | 'completed' | 'all'
  date?: string                  // YYYY-MM-DD
}) {
  return request.get('/api/todos', { params })
}

/** 获取 todo 详情（含留言列表） */
export function getTodo(id: number) {
  return request.get(`/api/todos/${id}`)
}

/** 创建 todo */
export function createTodo(data: {
  content: string
  date?: string
  color?: string
  note?: string
  image_url?: string
}) {
  return request.post('/api/todos', data)
}

/** 更新 todo */
export function updateTodo(id: number, data: Partial<{
  content: string
  date: string
  color: string
  note: string
  image_url: string
}>) {
  return request.put(`/api/todos/${id}`, data)
}

/** 软删除 todo */
export function deleteTodo(id: number) {
  return request.delete(`/api/todos/${id}`)
}

// ============================================================
// 完成 / 撤销
// ============================================================

/** 标记完成（completion_note 与 completion_image_url 二选一必填） */
export function completeTodo(id: number, data: {
  completion_note?: string
  completion_image_url?: string
}) {
  return request.post(`/api/todos/${id}/complete`, data)
}

/** 撤销完成 */
export function uncompleteTodo(id: number) {
  return request.post(`/api/todos/${id}/uncomplete`)
}

// ============================================================
// 图片上传（独立接口，业务接口只接 URL）
// ============================================================

/** 上传图片，返回 { image_url } */
export function uploadTodoImage(file: File, sub_dir: 'todo' | 'completion' = 'todo') {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('sub_dir', sub_dir)
  return multipartRequest.post('/api/todos/upload-image', fd)
}

// ============================================================
// 留言（仅管理员可 POST/DELETE）
// ============================================================

/** 获取留言列表（创建人/管理员可访问） */
export function getTodoMessages(todoId: number) {
  return request.get(`/api/todos/${todoId}/messages`)
}

/** 添加留言（管理员或任务创建人可调用） */
export function addTodoMessage(todoId: number, content: string) {
  return request.post(`/api/todos/${todoId}/messages`, { content })
}

/** 管理员删除留言 */
export function deleteTodoMessage(todoId: number, msgId: number) {
  return request.delete(`/api/todos/${todoId}/messages/${msgId}`)
}

// ============================================================
// 通知（红点未读）
// ============================================================

/** 获取未读统计 */
export function getTodoNotifications() {
  return request.get('/api/todos/notifications')
}

/** 标记已读（todoId 不传则标记全部已读） */
export function clearTodoNotifications(todoId?: number) {
  return request.post('/api/todos/notifications/clear', todoId ? { todo_id: todoId } : {})
}
