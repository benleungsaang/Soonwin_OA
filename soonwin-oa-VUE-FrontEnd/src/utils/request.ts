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
  // 在开发环境中使用相对路径，通过Vite代理转发请求
  if (process.env.NODE_ENV === 'development') {
    return '';
  }
  // 在生产环境中使用当前访问的域名和端口5000
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port = 5000; // 后端服务端口固定为5000
  return `${protocol}//${hostname}:${port}`;
};

const service = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000, // 增加超时时间
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
    const response = await axios.post(`${getBaseURL()}/api/auth/refresh`, {}, {
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
  (config: ExtendedAxiosRequestConfig) => {
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
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data;
    // 成功响应（code=200）
    if (res.code === 200) {
      return res.data;
    }
    // 业务错误（code≠200）
    const errorMsg = res.code ? `[${res.code}] ${res.msg}` : res.msg || '操作失败';
    ElMessage({
      message: errorMsg,
      type: 'error',
      duration: 5000, // 延长显示时间到5秒
      showClose: true  // 显示关闭按钮
    });
    return Promise.reject(new Error(res.msg || '接口请求错误'));
  },
  (error: AxiosError) => {
    const originalRequest = error.config as ExtendedAxiosRequestConfig;
    
    // 跳过认证刷新的请求
    if (originalRequest._skipAuthRefresh) {
      let errorMsg = '网络异常，请重试';
      if (error.response) {
        const status = error.response.status;
        const data = error.response.data as any;
        if (data && typeof data === 'object' && data.code && data.msg) {
          errorMsg = `[${data.code}] ${data.msg}`;
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
      if (data && typeof data === 'object' && data.code && data.msg) {
        // 如果后端返回了标准格式的错误信息，使用后端的错误信息
        errorMsg = `[${data.code}] ${data.msg}`;
      } else {
        // 否则使用HTTP状态码和状态文本
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
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return service.get<T>(url, config);
  },
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return service.post<T>(url, data, config);
  },
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return service.put<T>(url, data, config);
  },
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return service.delete<T>(url, config);
  },
};

export default request;