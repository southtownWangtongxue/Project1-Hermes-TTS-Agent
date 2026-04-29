import axios from 'axios'
import type { AxiosInstance } from 'axios'

/* 创建 axios 实例 */
const client: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/* 请求拦截器：添加认证 Token（占位） */
client.interceptors.request.use(
  (config) => {
    // TODO: 从本地存储或 Pinia 中获取真实 Token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/* 响应拦截器：统一错误处理 */
client.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('[API Error]', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default client
