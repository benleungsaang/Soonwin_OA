import request from '@/utils/request'

export interface Customer {
  id?: number
  company_name: string
  contact_person: string
  phone?: string
  email?: string
  area?: string
  customer_type?: string
  source?: string
  source_id?: number
  remark?: string
  creator_id?: string
  creator_name?: string
  create_time?: string
  update_time?: string
}

export interface CustomerSimple {
  id: number
  company_name: string
  contact_person: string
  phone?: string
  area?: string
}

export interface CustomerQueryParams {
  page?: number
  size?: number
  search?: string
}

export interface CustomerRecords {
  inquiries: any[]
  order_records: any[]
}

// 获取客户列表
export function getCustomers(params: CustomerQueryParams) {
  return request.get<{
    list: Customer[]
    total: number
    page: number
    size: number
  }>('/api/customers', { params })
}

// 创建客户
export function createCustomer(data: Customer) {
  return request.post<Customer>('/api/customers', data)
}

// 获取客户详情
export function getCustomer(id: number) {
  return request.get<Customer>(`/api/customers/${id}`)
}

// 更新客户
export function updateCustomer(id: number, data: Customer) {
  return request.put<Customer>(`/api/customers/${id}`, data)
}

// 删除客户
export function deleteCustomer(id: number) {
  return request.delete(`/api/customers/${id}`)
}

// 获取客户简单信息
export function getCustomerSimple(id: number) {
  return request.get<CustomerSimple>(`/api/customers/${id}/simple`)
}

// 获取客户关联记录
export function getCustomerRecords(id: number) {
  return request.get<CustomerRecords>(`/api/customers/${id}/records`)
}

// 从询盘导入客户
export function importFromInquiry(inquiryId: number) {
  return request.post<Customer>('/api/customers/import-from-inquiry', { inquiry_id: inquiryId })
}

// 从订单记录导入客户
export function importFromOrderRecord(orderRecordId: number) {
  return request.post<Customer>('/api/customers/import-from-order-record', { order_record_id: orderRecordId })
}

// 从询盘页面直接创建客户（同时绑定）
export function createCustomerFromInquiry(inquiryId: number, data: Partial<Customer>) {
  return request.post<Customer>(`/api/customers/create-from-inquiry/${inquiryId}`, data)
}

// 从订单记录页面直接创建客户（同时绑定）
export function createCustomerFromOrderRecord(orderRecordId: number, data: Partial<Customer>) {
  return request.post<Customer>(`/api/customers/create-from-order-record/${orderRecordId}`, data)
}

// 绑定询盘到客户
export function bindInquiry(customerId: number, inquiryId: number) {
  return request.post(`/api/customers/${customerId}/bind-inquiry`, { inquiry_id: inquiryId })
}

// 解绑询盘
export function unbindInquiry(customerId: number, inquiryId: number) {
  return request.post(`/api/customers/${customerId}/unbind-inquiry`, { inquiry_id: inquiryId })
}

// 绑定订单记录到客户
export function bindOrderRecord(customerId: number, orderRecordId: number) {
  return request.post(`/api/customers/${customerId}/bind-order-record`, { order_record_id: orderRecordId })
}

// 解绑订单记录
export function unbindOrderRecord(customerId: number, orderRecordId: number) {
  return request.post(`/api/customers/${customerId}/unbind-order-record`, { order_record_id: orderRecordId })
}
