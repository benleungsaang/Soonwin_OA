import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
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
  timeout: 5000, // 增加超时时间
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
    throw new Error('No token available for refresh');
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
      // 请求已发出但没有收到响应（网络错误等）
      errorMsg = '网络连接失败，请检查网络';
    } else {
      // 其他错误
      errorMsg = error.message || '请求配置错误';
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

export default request;