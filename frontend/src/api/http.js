// 全局唯一的 axios 实例：所有接口模块（auth/student/teacher）都基于它。
// baseURL 统一加 /api 前缀；withCredentials 让会话 Cookie 随请求携带。
// 开发环境由 vite 代理转发到后端（见 vite.config.js），生产环境同源直连。
import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

// 统一解包后端 { code, message, data } 响应格式
http.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === 'object' && 'code' in response.data) {
      if (response.data.code === 0) {
        response.data = response.data.data
      }
    }
    return response
  },
  (error) => {
    if (error.response?.data) {
      if (error.response.data.message) {
        error.response.data.detail = error.response.data.message
      }
    }
    return Promise.reject(error)
  },
)

export default http
