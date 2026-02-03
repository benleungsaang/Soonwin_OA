import request from '@/utils/request';
import { OrderBasicInfo, OrderProgressDetail, ProgressItem } from '@/types/order';
import axios from 'axios';

// 获取订单列表（仅返回非敏感基础数据）
export const getOrderList = (params?: any): Promise<any> => {
  return request.get('/api/orders', { params });
};

// 获取订单进度详情
export const getOrderProgress = (orderId: string | number): Promise<any> => {
  return request.get(`/api/orders/${orderId}/progress`);
};

// 更新订单进度状态
export const updateProgressStatus = (orderId: string | number, statusData: any): Promise<any> => {
  return request.put(`/api/orders/${orderId}/progress/status`, statusData);
};

// 创建进度状态
export const createProgressStatus = (orderId: string | number, statusData: any): Promise<any> => {
  return request.post(`/api/orders/${orderId}/progress/status`, statusData);
};

// 新增进度项
export const addProgressItem = (data: Partial<ProgressItem>): Promise<any> => {
  return request.post('/api/progress/items', data);
};

// 更新进度项
export const updateProgressItem = (data: Partial<ProgressItem>): Promise<any> => {
  return request.put(`/api/progress/items/${data.id}`, {
    title: data.title,
    status: data.status,
    remark: data.remark
  });
};

// 删除进度项
export const deleteProgressItem = (itemId: string): Promise<any> => {
  return request.delete(`/api/progress/items/${itemId}`);
};

// 上传进度项多媒体文件
export const uploadProgressMedia = (file: File, itemId: string): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('item_id', itemId);
  
  // 使用axios直接上传，因为需要特殊处理FormData
  const token = localStorage.getItem('oa_token');
  const config = {
    headers: {
      'Content-Type': 'multipart/form-data',
      'Authorization': `Bearer ${token}`
    }
  };
  
  return axios.post(`${import.meta.env.VITE_API_BASE_URL || ''}/api/progress/media/upload`, formData, config)
    .then(response => {
      // 检查响应格式并返回相应的内容
      const res = response.data;
      if (res && res.code === 200) {
        return res.data || res;
      } else {
        throw new Error(res.msg || '上传失败');
      }
    });
};

// 删除进度项多媒体文件
export const deleteProgressMedia = (mediaId: string): Promise<any> => {
  return request.delete(`/api/progress/media/${mediaId}`);
};

// 创建订单（带进度表）
export const createOrderWithProgress = (data: any): Promise<any> => {
  return request.post('/api/orders', data);
};

// 删除订单进度
export const deleteOrderProgress = (orderId: string | number): Promise<any> => {
  return request.delete(`/api/orders/${orderId}/progress`);
};

// 清空订单进度状态（只清空当前状态，保留进度项数据）
export const clearProgressStatus = (orderId: string | number): Promise<any> => {
  return request.delete(`/api/orders/${orderId}/progress/status`);
};