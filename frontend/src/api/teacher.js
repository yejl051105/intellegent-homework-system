// 教师端接口：作业管理、AI 批改与复核、评分标准、优秀作业、回收站
import http from './http'

// 作业列表与详情（教师可见完整字段，含 AI 草稿）
export const fetchHomeworks = () => http.get('/teacher/homeworks')
export const fetchHomework = (id) => http.get(`/teacher/homework/${id}`)
// 移入教师侧回收站（软删除）
export const deleteHomework = (id) => http.post(`/teacher/homework/${id}/delete`)

// 回收站：列表 / 恢复 / 彻底删除
export const fetchRecycleBin = () => http.get('/teacher/recycle-bin')
export const restoreHomework = (id) => http.post(`/teacher/homework/${id}/restore`)
export const permanentlyDeleteHomework = (id) => http.delete(`/teacher/homework/${id}/permanent`)

// AI 批改三步：可用模型 → 生成建议草稿 → 教师确认（或重置重来）
export const fetchAiModels = () => http.get('/teacher/ai-models')
// payload: { criteria_id, model_id }
export const generateAiReview = (id, payload) => http.post(`/teacher/homework/${id}/ai-review`, payload)
export const resetAiReview = (id) => http.post(`/teacher/homework/${id}/reset-review`)
// payload: { score, comment, error_boxes }，error_boxes 使用原图像素坐标
export const submitGrade = (id, payload) => http.post(`/teacher/grade/${id}`, payload)

// 评分标准：formData 含 title + content（文字）或 file（PDF/DOC/DOCX 附件）
export const fetchCriteria = () => http.get('/teacher/criteria')
export const createCriteria = (formData) => http.post('/teacher/criteria', formData)
export const deleteCriteria = (id) => http.post(`/teacher/criteria/${id}/delete`)

// 优秀作业：设为优秀会复制图片生成独立展示记录
export const fetchExemplaryList = () => http.get('/teacher/exemplary')
export const fetchExemplaryDetail = (id) => http.get(`/teacher/exemplary/${id}`)
export const markExemplary = (id) => http.post(`/teacher/exemplary/${id}`)
export const unmarkExemplary = (id) => http.post(`/teacher/unexemplary/${id}`)
