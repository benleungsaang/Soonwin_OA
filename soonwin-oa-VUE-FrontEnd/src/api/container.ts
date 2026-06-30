import request from '@/utils/request'

/**
 * 货柜排布方案相关 API
 * 路径前缀：/api/container-layouts
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

/** 列表分页响应 */
export interface ListResponse<T> {
  items: T[]
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

/** 通用响应 */
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
}

/**
 * 获取货柜排布方案列表
 */
export function listContainerLayouts(params: ListLayoutsParams) {
  return request.get<ApiResponse<ListResponse<ContainerLayout>>>(
    '/api/container-layouts',
    { params }
  )
}

/**
 * 获取单个方案详情（含完整布局数据）
 */
export function getContainerLayout(id: number) {
  return request.get<ApiResponse<ContainerLayoutDetail>>(
    `/api/container-layouts/${id}`
  )
}

/**
 * 创建方案（仅创建元数据，data 字段可选）
 */
export function createContainerLayout(body: { name: string; data?: ContainerData }) {
  return request.post<ApiResponse<ContainerLayoutDetail>>(
    '/api/container-layouts',
    body
  )
}

/**
 * 更新方案（仅作者或管理员）
 */
export function updateContainerLayout(
  id: number,
  body: { data?: ContainerData; name?: string }
) {
  return request.put<ApiResponse<ContainerLayoutDetail>>(
    `/api/container-layouts/${id}`,
    body
  )
}

/**
 * 删除方案（仅作者或管理员，软删除）
 */
export function deleteContainerLayout(id: number) {
  return request.delete<ApiResponse<null>>(`/api/container-layouts/${id}`)
}