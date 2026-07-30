// 学生端接口：提交作业、查看批改结果、回收站、优秀作业
import http from './http'

// 我的作业列表（后端已过滤未复核的 AI 草稿字段）
export const fetchHomeworks = () => http.get('/student/homeworks')
export const fetchHomework = (id) => http.get(`/student/homework/${id}`)
// 提交作业：formData 含 title 和 image 文件
export const uploadHomework = (formData) => http.post('/student/upload', formData)
// 移入学生侧回收站（软删除）
export const deleteHomework = (id) => http.post(`/student/homework/${id}/delete`)

// 回收站：列表 / 恢复 / 彻底删除
export const fetchRecycleBin = () => http.get('/student/recycle-bin')
export const restoreHomework = (id) => http.post(`/student/homework/${id}/restore`)
export const permanentlyDeleteHomework = (id) => http.delete(`/student/homework/${id}/permanent`)

// 优秀作业展示墙
export const fetchExemplaryList = () => http.get('/student/exemplary')
export const fetchExemplaryDetail = (id) => http.get(`/student/exemplary/${id}`)
