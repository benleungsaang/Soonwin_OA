import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { ElMessage } from 'element-plus';

// 定义接口响应通用类型
interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

// 创建Axios实例
const getBaseURL = () => {
  // 在开发环境中使用相对路径，通过Vite代理转发请求
  if (import.meta.env.MODE === 'development') {
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
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8',
  },
});

// 请求拦截器：添加JWT令牌
service.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 从localStorage获取JWT令牌（登录后存储）
    const token = localStorage.getItem('oa_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
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
    ElMessage.error(res.msg || '操作失败');
    // 令牌过期（code=401）：清除令牌并跳转登录页
    if (res.code === 401) {
      localStorage.removeItem('oa_token');
      window.location.href = '/login';
    }
    return Promise.reject(new Error(res.msg || '接口请求错误'));
  },
  (error: AxiosError) => {
    // 网络错误或服务器错误
    const errMsg = error.message || '网络异常，请重试';
    ElMessage.error(errMsg);
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