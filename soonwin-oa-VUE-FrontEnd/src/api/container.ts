import request from '@/utils/request'

/**
 * 货柜排布方案相关 API
 * 路径前缀：/api/container-layouts
 *
 * 重要：request.ts 拦截器会自动解包后端响应的 `data` 字段，
 * 所以前端拿到的就是后端的 data 内容，不再有 success/data 包装。
 * 错误（非 2xx 响应）由拦截器统一处理（ElMessage 提示并 reject）。
 */

/** 单个货柜的尺寸数据 */
export interface ContainerData {
  version: number
  container: { name: string; l: number; w: number; h: number }
  cargos: Array<{
    name: string
    sx: number
    sy: number
    sz: number
    px: number
    py: number
    pz: number
    color: string
  }>
  allowOverflow: boolean
  interactionMode: 'direct' | 'select'
  colorIndex: number
}

/** 方案摘要（列表展示用） */
export interface ContainerLayout {
  id: number
  name: string
  author_id: string
  author_name: string
  is_owner: boolean
  created_at: string
  updated_at: string
  // 详情中包含，列表中可能为空
  container_name?: string
  container_size?: string
  cargo_count?: number
}

/** 方案详情（含完整布局数据） */
export interface ContainerLayoutDetail extends ContainerLayout {
  data: ContainerData
}

/** 列表分页响应（后端 data 字段，request 已解包） */
export interface ListResponse {
  items: ContainerLayout[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/** 列表查询参数 */
export interface ListLayoutsParams {
  page?: number
  per_page?: number
  search?: string
  scope?: 'mine' | 'all'
}

/**
 * 获取货柜排布方案列表
 * 返回：ListResponse（后端 data 已解包）
 */
export function listContainerLayouts(params: ListLayoutsParams) {
  return request.get<ListResponse>('/api/container-layouts', { params })
}

/**
 * 获取单个方案详情（含完整布局数据）
 * 返回：ContainerLayoutDetail（后端 data 已解包）
 */
export function getContainerLayout(id: number) {
  return request.get<ContainerLayoutDetail>(`/api/container-layouts/${id}`)
}

/**
 * 创建方案（仅创建元数据，data 字段可选）
 * 返回：ContainerLayoutDetail（后端 data 已解包）
 */
export function createContainerLayout(body: { name: string; data?: ContainerData }) {
  return request.post<ContainerLayoutDetail>('/api/container-layouts', body)
}

/**
 * 更新方案（仅作者或管理员）
 * 返回：ContainerLayoutDetail（后端 data 已解包）
 */
export function updateContainerLayout(
  id: number,
  body: { data?: ContainerData; name?: string }
) {
  return request.put<ContainerLayoutDetail>(`/api/container-layouts/${id}`, body)
}

/**
 * 删除方案（仅作者或管理员，软删除）
 * 返回：null（后端 data 通常为 None）
 */
export function deleteContainerLayout(id: number) {
  return request.delete<null>(`/api/container-layouts/${id}`)
}