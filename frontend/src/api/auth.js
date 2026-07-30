// 认证接口：登录、登出、会话校验、动态路由权限
import http from './http'

// 登录，成功后服务端把用户写入会话（Cookie 承载）
export const login = (credentials) => http.post('/login', credentials)
// 退出登录，清空服务端会话
export const logout = () => http.post('/logout')
// 获取当前登录用户；401 表示会话已失效
export const fetchCurrentUser = () => http.get('/me')
// 获取当前角色可访问的路由表，router 据此动态注册页面
export const fetchAuthorizedRoutes = () => http.get('/routes')
