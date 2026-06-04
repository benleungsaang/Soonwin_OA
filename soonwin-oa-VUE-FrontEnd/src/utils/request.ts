import axios, { AxiosRequestConfig, AxiosResponse, AxiosError, AxiosProgressEvent } from 'axios';
import { ElMessage } from 'element-plus';

// 定义接口响应通用类型
interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

// 解码JWT token获取payload
const decodeToken = (token: string) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
};

// 检查token是否即将过期（默认提前5分钟刷新）
const isTokenExpiringSoon = (token: string, bufferSeconds: number = 300): boolean => {
  const payload = decodeToken(token);
  if (!payload || !payload.exp) {
    return false;
  }
  const currentTime = Math.floor(Date.now() / 1000);
  const expTime = payload.exp;
  return expTime - currentTime < bufferSeconds;
};

// 创建Axios实例
const getBaseURL = () => {
  // 开发环境：使用相对路径（由vite proxy转发，避免localhost硬编码）
  if (import.meta.env.MODE === 'development') {
    return '/'; // 关键：改为相对路径，由vite proxy转发到5001
  }
  // 生产环境：动态拼接当前访问的IP+端口 + /api（核心：解决移动端localhost问题）
  // window.location.origin会自动获取当前访问的地址，如http://192.168.30.64:5183
  return `${window.location.origin}/`;
};

const service = axios.create({
  baseURL: getBaseURL(),
  timeout: 15000, // 移动端网络波动较大，预留足够超时时间
  headers: {
    'Content-Type': 'application/json;charset=utf-8',
  },
});

// 用于存储刷新token的Promise，避免同时发起多个刷新请求
let isRefreshing = false;
let failedQueue: Array<{resolve: (value: any) => void, reject: (value: any) => void}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// 刷新令牌函数
const refreshToken = async (): Promise<string> => {
  const token = localStorage.getItem('oa_token');

  if (!token) {
    throw new Error('验证码错误');
  }

  try {
    // 统一使用service的baseURL，避免重复拼接
    const response = await axios.post(`${getBaseURL()}/auth/refresh`, {}, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    const newToken = response.data.data.token;
    localStorage.setItem('oa_token', newToken);
    return newToken;
  } catch (error) {
    localStorage.removeItem('oa_token');
    window.location.href = '/login';
    throw error;
  }
};

// 定义扩展的AxiosRequestConfig接口
interface ExtendedAxiosRequestConfig extends AxiosRequestConfig {
  _skipAuthRefresh?: boolean;
  _retry?: boolean;
}

// 请求拦截器：添加JWT令牌
service.interceptors.request.use(
  (config: any) => {
    // 跳过认证刷新的请求
    if (config._skipAuthRefresh) {
      return config;
    }

    // 从localStorage获取JWT令牌（登录后存储）
    const token = localStorage.getItem('oa_token');
    if (token) {
      // 检查令牌是否即将过期
      if (isTokenExpiringSoon(token)) {
        refreshToken().catch(err => {
          console.error('Token refresh failed:', err);
        });
      }

      if (config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => {
    ElMessage.error('请求发送失败，请检查网络');
    return Promise.reject(error);
  }
);

// 响应拦截器：统一处理结果和错误
service.interceptors.response.use(
  (response: AxiosResponse<any>) => {
    const res = response.data;
    // 检查是否为success/data格式的响应（后端API）
    if (typeof res === 'object' && 'success' in res) {
      if (res.success) {
        // 成功响应，返回data部分
        return res.data || {};
      } else {
        // 业务错误
        const errorMsg = res.message || res.msg || '操作失败';
        ElMessage({
          message: errorMsg,
          type: 'error',
          duration: 5000,
          showClose: true
        });
        return Promise.reject(new Error(res.message || res.msg || '接口请求错误'));
      }
    }
    // 兼容原来的code/msg/data格式
    else if (typeof res === 'object' && 'code' in res && res.code === 200) {
      return res.data;
    }
    // 其他情况，直接返回data部分
    else {
      const errorMsg = res.code ? `[${res.code}] ${res.msg}` : res.msg || '操作失败';
      ElMessage({
        message: errorMsg,
        type: 'error',
        duration: 5000,
        showClose: true
      });
      return Promise.reject(new Error(res.msg || '接口请求错误'));
    }
  },
  (error: AxiosError) => {
    const originalRequest = error.config as ExtendedAxiosRequestConfig;

    // 跳过认证刷新的请求
    if (originalRequest._skipAuthRefresh) {
      let errorMsg = '网络异常，请重试';
      if (error.response) {
        const status = error.response.status;
        const data = error.response.data as any;
        if (data && typeof data === 'object') {
          // 处理success/data格式的错误响应
          if ('success' in data && !data.success) {
            errorMsg = data.message || data.msg || `[${status}] ${error.response.statusText || '服务器错误'}`;
          }
          // 处理code/msg格式的错误响应
          else if (data.code && data.msg) {
            errorMsg = `[${data.code}] ${data.msg}`;
          } else {
            errorMsg = `[${status}] ${error.response.statusText || '服务器错误'}`;
          }
        } else {
          errorMsg = `[${status}] ${error.response.statusText || '服务器错误'}`;
        }
      } else if (error.request) {
        errorMsg = '网络连接失败，请检查网络';
      } else {
        errorMsg = error.message || '请求配置错误';
      }
      ElMessage({
        message: errorMsg,
        type: 'error',
        duration: 5000,
        showClose: true
      });
      return Promise.reject(error);
    }

    // 如果是401错误且不是重试请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 如果正在刷新，将请求加入队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return service(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      return refreshToken()
        .then(newToken => {
          processQueue(null, newToken);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return service(originalRequest);
        })
        .catch(error => {
          processQueue(error, null);
          return Promise.reject(error);
        })
        .finally(() => {
          isRefreshing = false;
        });
    }

    // 网络错误或服务器错误
    let errorMsg = '网络异常，请重试';
    if (error.response) {
      // 服务器返回了错误状态码
      const status = error.response.status;
      const data = error.response.data as any;
      if (data && typeof data === 'object') {
        // 处理success/data格式的错误响应
        if ('success' in data && !data.success) {
          errorMsg = data.message || data.msg || `服务器错误(${status})，请稍后重试`;
        }
        // 处理code/msg格式的错误响应
        else if (data.code && data.msg) {
          errorMsg = data.msg;
        } else {
          errorMsg = `服务器错误(${status})，请稍后重试`;
        }
      } else {
        errorMsg = `服务器错误(${status})，请稍后重试`;
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应（超时、网络断开等）
      errorMsg = '网络连接超时或信号不稳定，请检查WiFi/移动网络后重试';
    } else {
      // 其他错误
      errorMsg = error.message || '请求异常，请稍后重试';
    }
    // 显示错误信息，延长显示时间
    ElMessage({
      message: errorMsg,
      type: 'error',
      duration: 5000, // 延长显示时间到5秒
      showClose: true  // 显示关闭按钮
    });
    return Promise.reject(error);
  }
);

// 封装请求方法（GET/POST/PUT/DELETE）
const request = {
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await service.get<T>(url, config);
    return response as any as T; // 拦截器已处理，response是解包后的数据
  },
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await service.post<T>(url, data, config);
    return response as any as T; // 拦截器已处理，response是解包后的数据
  },
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await service.put<T>(url, data, config);
    return response as any as T; // 拦截器已处理，response是解包后的数据
  },
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await service.delete<T>(url, config);
    return response as any as T; // 拦截器已处理，response是解包后的数据
  },
};

// 机器管理相关API
export const getMachines = (params?: any) => request.get('/api/machines', { params });
export const getMachine = (model: string) => request.get(`/api/machines/${model}`);
export const createMachine = (data: any) => request.post('/api/machines', data);
export const updateMachine = (model: string, data: any) => request.put(`/api/machines/${model}`, data);
export const deleteMachine = (model: string) => request.delete(`/api/machines/${model}`);
export const importMachines = (data: FormData) => request.post('/api/machines/import', data);
// 直接JSON数据导入导出API
export const importMachinesJson = (data: any) => request.post('/api/machines/import-json', data);
export const exportMachinesJson = () => request.get('/api/machines/export-json');
// 部件管理相关API
export const getParts = (params?: any) => request.get('/api/parts', { params });
export const getPart = (partTypeId: number) => request.get(`/api/parts/${partTypeId}`);
export const createPart = (data: any) => request.post('/api/parts', data);
export const updatePart = (partTypeId: number, data: any) => request.put(`/api/parts/${partTypeId}`, data);
export const deletePart = (partTypeId: number) => request.delete(`/api/parts/${partTypeId}`);
// 部件JSON导入导出API
export const importPartsJson = (data: any) => request.post('/api/parts/import-json', data);
export const exportPartsJson = () => request.get('/api/parts/export-json');

// MachineNew相关API
export const getMachinesNew = (params?: any) => request.get('/api/machines_new', { params });
export const getMachineNew = (id: number) => request.get(`/api/machines_new/${id}`);
export const createMachineNew = (data: any) => request.post('/api/machines_new', data);
export const updateMachineNew = (id: number, data: any) => request.put(`/api/machines_new/${id}`, data);
export const deleteMachineNew = (id: number) => request.delete(`/api/machines_new/${id}`);
export const importMachinesNewJson = (data: any) => request.post('/api/machines_new/import-json', data);
export const exportMachinesNewJson = () => request.get('/api/machines_new/export-json');
// 设备回收站相关API
export const getDeletedMachines = (params?: any) => request.get('/api/machines_new/recycle-bin', { params });
export const restoreMachineFromRecycleBin = (id: number) => request.put(`/api/machines_new/recycle-bin/${id}/restore`);
export const permanentDeleteMachine = (id: number) => request.delete(`/api/machines_new/recycle-bin/${id}/permanent-delete`);
export const batchPermanentDeleteMachines = (ids: number[]) => request.delete('/api/machines_new/recycle-bin/batch-permanent-delete', { data: { ids } });
export const clearRecycleBin = () => request.delete('/api/machines_new/recycle-bin/clear');
// 报价管理相关API
export const getQuotationMachines = (params?: any) => request.get('/api/quotation-machines', { params });
// 临时报价相关API
export const getQuotationTempList = (params?: any) => request.get('/api/quotation-temp-list', { params });
export const getQuotationTemp = (id: number) => request.get(`/api/quotation-temp/${id}`);
export const createQuotationTemp = (data: any) => request.post('/api/quotation-temp', data);
export const updateQuotationTemp = (id: number, data: any) => request.put(`/api/quotation-temp/${id}`, data);
export const deleteQuotationTemp = (id: number) => request.delete(`/api/quotation-temp/${id}`);

// 设备缩略图上传API
export const uploadMachineThumb = (machineId: number, data: FormData) => multipartRequest.post(`/api/machines_new/${machineId}/upload-thumb`, data);
// 通用设备缩略图上传API（用于新增设备时）
export const uploadMachineThumbGeneric = (data: FormData) => multipartRequest.post('/api/machines_new/upload-thumb', data);
// 照片管理相关API - 使用特殊处理FormData的函数
export const multipartRequest = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000, // 增加超时时间，因为文件上传可能需要更长时间
  headers: {
    // 这里不设置默认Content-Type，让浏览器自动设置
  },
});

// 添加请求和响应拦截器到multipartRequest
multipartRequest.interceptors.request.use(
  (config) => {
    // 从localStorage获取JWT令牌
    const token = localStorage.getItem('oa_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    ElMessage.error('请求发送失败，请检查网络');
    return Promise.reject(error);
  }
);

multipartRequest.interceptors.response.use(
  (response) => {
    const res = response.data;
    // 检查是否为success/data格式的响应（后端API）
    if (typeof res === 'object' && 'success' in res) {
      if (res.success) {
        // 成功响应，返回data部分
        return res.data || {};
      } else {
        // 业务错误
        const errorMsg = res.message || res.msg || '操作失败';
        ElMessage({
          message: errorMsg,
          type: 'error',
          duration: 5000,
          showClose: true
        });
        return Promise.reject(new Error(res.message || res.msg || '接口请求错误'));
      }
    }
    // 兼容原来的code/msg/data格式
    else if (typeof res === 'object' && 'code' in res && res.code === 200) {
      return res.data;
    }
    // 其他情况，直接返回data部分
    else {
      const errorMsg = res.code ? `[${res.code}] ${res.msg}` : res.msg || '操作失败';
      ElMessage({
        message: errorMsg,
        type: 'error',
        duration: 5000,
        showClose: true
      });
      return Promise.reject(new Error(res.msg || '接口请求错误'));
    }
  },
  (error) => {
    // 复制错误处理逻辑
    let errorMsg = '网络异常，请重试';
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as any;
      if (data && typeof data === 'object') {
        if ('success' in data && !data.success) {
          errorMsg = data.message || data.msg || `[${status}] ${error.response.statusText || '服务器错误'}`;
        }
        else if (data.code && data.msg) {
          errorMsg = `[${data.code}] ${data.msg}`;
        } else {
          errorMsg = `[${status}] ${error.response.statusText || '服务器错误'}`;
        }
      } else {
        errorMsg = `[${status}] ${error.response.statusText || '服务器错误'}`;
      }
    } else if (error.request) {
      errorMsg = '网络连接失败，请检查网络';
    } else {
      errorMsg = error.message || '请求配置错误';
    }
    ElMessage({
      message: errorMsg,
      type: 'error',
      duration: 5000,
      showClose: true
    });
    return Promise.reject(error);
  }
);

export const createPhoto = (
  data: FormData,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
) => {
  return multipartRequest.post('/api/photos', data, {
    onUploadProgress
  });
};

export const updatePhoto = (photoId: number, data: any) => request.put(`/api/photos/${photoId}`, data);
export const deletePhoto = (photoId: number) => request.delete(`/api/photos/${photoId}`);
export const getPhotos = (params?: any) => request.get('/api/photos', { params });
export const getMachinesForPhotos = () => request.get('/api/photos/machines');

// 照片回收站相关API
/**
 * 获取已删除的照片列表
 * @param params - 可选的查询参数，用于过滤或分页等操作
 * @returns 返回一个Promise，解析为API响应结果
 */
export const getDeletedPhotos = (params?: any) => request.get('/api/photos/recycle-bin', { params });
export const restorePhoto = (photoId: number) => request.put(`/api/photos/recycle-bin/${photoId}/restore`);
export const permanentDeletePhotos = (photoIds: number[]) => request.delete('/api/photos/permanent-delete', { data: { photo_ids: photoIds } });

// 视频管理相关API - 使用特殊处理FormData的函数
export const createVideo = (
  data: FormData,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
) => {
  return multipartRequest.post('/api/videos', data, {
    onUploadProgress
  });
};

export const updateVideo = (videoId: number, data: any) => request.put(`/api/videos/${videoId}`, data);

export const deleteVideo = (videoId: number) => request.delete(`/api/videos/${videoId}`);

export const getMachinesForVideos = () => request.get('/api/videos/machines');

// 回收站相关API
export const getDeletedVideos = (params?: any) => request.get('/api/videos/deleted', { params });

export const physicalDeleteVideos = (videoIds: number[]) =>
  request.delete('/api/videos/physical_delete', { data: { video_ids: videoIds } });

export const restoreVideos = (videoIds: number[]) =>
  request.post('/api/videos/restore', { video_ids: videoIds });

export default request;