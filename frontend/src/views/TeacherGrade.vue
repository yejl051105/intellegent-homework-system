<template>
  <div>
    <div class="page-header">
      <h2>批改作业</h2>
      <router-link to="/teacher/dashboard">
        <el-button><el-icon><arrow-left /></el-icon>返回全部作业</el-button>
      </router-link>
    </div>

    <el-skeleton :loading="loading" animated :count="2">
      <el-card v-if="hw.id" shadow="never" class="form-card teacher-grade-card">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="学生">{{ hw.student_name }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ hw.title }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ hw.submitted_at?.slice(0, 10) }}</el-descriptions-item>
        </el-descriptions>

        <section v-if="hw.filename" class="teacher-image-panel" aria-label="学生提交的作业原图">
          <div class="teacher-image-head">
            <div>
              <p>ORIGINAL SUBMISSION</p>
              <h3>学生作业原图</h3>
            </div>
            <span class="image-preview-badge" title="点击图片可放大查看原图"><el-icon><zoom-in /></el-icon></span>
          </div>
          <el-image
            :src="`/uploads/${hw.filename}`"
            :preview-src-list="[`/uploads/${hw.filename}`]"
            preview-teleported
            class="teacher-homework-image"
            fit="contain"
          >
            <template #error>
              <div class="image-load-error"><el-icon><picture /></el-icon><span>作业图片加载失败</span></div>
            </template>
          </el-image>
        </section>

        <section class="ai-review-panel">
          <div class="ai-review-heading">
            <div>
              <p>AI REVIEW DRAFT</p>
              <h3>模型评分建议</h3>
            </div>
            <el-tag v-if="isFinalized" type="success">已完成复核</el-tag>
            <el-tag v-else-if="hasAiSuggestion" type="info">等待教师确认</el-tag>
            <el-tag v-else type="warning">尚未生成</el-tag>
          </div>

          <el-alert v-if="requestError" type="error" :title="requestError" show-icon :closable="false" />

          <template v-if="!hasAiSuggestion && !isFinalized">
            <p class="ai-review-copy">系统会先识别作业文字，再由模型给出评分和评语草稿。草稿不会直接对学生生效。</p>
            <div class="model-picker">
              <label for="review-model">本次批改使用的评分模型</label>
              <el-select id="review-model" v-model="selectedModelId" placeholder="请选择评分模型" @change="requestError = ''">
                <el-option
                  v-for="model in aiModels"
                  :key="model.id"
                  :label="`${model.label} · ${model.model}${model.available ? '' : '（未配置）'}`"
                  :value="model.id"
                  :disabled="!model.available"
                />
              </el-select>
              <p v-if="!hasAvailableModel" class="model-picker-hint">请在服务端 .env 中配置 DEEPSEEK_API_KEY、OPENAI_API_KEY 或 GEMINI_API_KEY 后重启后端。</p>
            </div>
            <div v-if="availableCriteria.length" class="criterion-picker">
              <label for="review-criterion">本次批改使用的评分标准</label>
              <el-select id="review-criterion" v-model="selectedCriteriaId" placeholder="请选择评分标准" @change="requestError = ''">
                <el-option
                  v-for="criterion in availableCriteria"
                  :key="criterion.id"
                  :label="`${criterion.title}${criterion.source_type === 'file' ? '（附件）' : '（文字）'}`"
                  :value="criterion.id"
                />
              </el-select>
              <p v-if="selectedCriterion?.content" class="selected-criterion-preview">{{ selectedCriterion.content }}</p>
              <p v-else-if="selectedCriterion?.filename" class="selected-criterion-preview">已选择附件评分标准，系统会在生成 AI 建议前提取附件中的文字。</p>
            </div>
            <el-alert v-else type="warning" title="请先在“评分标准”中添加文字或附件标准，才能生成 AI 建议。" :closable="false" show-icon />
            <el-button type="primary" class="generate-review-button" :loading="generating" :disabled="!selectedCriteriaId || !selectedModelId" @click="generateAiReview">
              <el-icon><magic-stick /></el-icon>{{ generating ? '正在生成建议' : '生成 AI 批改建议' }}
            </el-button>
          </template>

          <el-form v-else :model="reviewForm" label-position="top" class="review-form" :disabled="isFinalized" @submit.prevent="confirmReview">
            <div class="ai-model-meta" v-if="hw.ai_model">
              <span>模型：{{ hw.ai_model }}</span>
              <span v-if="hw.ai_criteria_title">评分标准：{{ hw.ai_criteria_title }}</span>
              <span v-if="hw.ai_generated_at">生成于 {{ formatDate(hw.ai_generated_at) }}</span>
            </div>
            <el-form-item label="建议分数（教师可修改）" required>
              <el-input-number v-model="reviewForm.score" :min="0" :max="100" :step="1" :precision="0" />
            </el-form-item>
            <el-form-item label="建议评语（教师可修改）" required>
              <el-input v-model="reviewForm.comment" type="textarea" :rows="5" maxlength="2000" show-word-limit />
            </el-form-item>
            <div v-if="!isFinalized" class="comment-reset-row">
              <el-popconfirm title="将放弃当前手动修改，恢复为 AI 原始评语。" @confirm="resetComment">
                <template #reference>
                  <el-button text class="reset-comment-button"><el-icon><refresh-left /></el-icon>重置为 AI 原评语</el-button>
                </template>
              </el-popconfirm>
            </div>
            <div v-if="hw.ai_rationale" class="ai-rationale"><strong>供复核参考：</strong>{{ hw.ai_rationale }}</div>
            <el-form-item v-if="!isFinalized">
              <el-button type="primary" native-type="submit" class="confirm-review-button" :loading="confirming">
                {{ confirming ? '正在确认' : '确认复核并完成批改' }} <el-icon v-if="!confirming"><circle-check /></el-icon>
              </el-button>
            </el-form-item>
          </el-form>
        </section>
      </el-card>
    </el-skeleton>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const hw = ref({})
const loading = ref(true)
const generating = ref(false)
const confirming = ref(false)
const requestError = ref('')
const reviewForm = reactive({ score: null, comment: '' })

const criteria = ref([])
const aiModels = ref([])
const selectedCriteriaId = ref(null)
const selectedModelId = ref(null)
const hasAiSuggestion = computed(() => hw.value.review_status === 'ai_suggested')
const isFinalized = computed(() => hw.value.review_status === 'confirmed' || hw.value.score !== null)
const availableCriteria = computed(() => criteria.value.filter((item) => item.content?.trim() || item.filename))
const selectedCriterion = computed(() => availableCriteria.value.find((item) => item.id === selectedCriteriaId.value))
const hasAvailableModel = computed(() => aiModels.value.some((item) => item.available))

function syncReviewForm(data) {
  reviewForm.score = data.ai_score ?? data.score
  reviewForm.comment = data.ai_comment || data.comment || ''
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadHomework() {
  const [{ data: homework }, { data: criteriaData }, { data: modelData }] = await Promise.all([
    api.get(`/teacher/homework/${route.params.id}`),
    api.get('/teacher/criteria'),
    api.get('/teacher/ai-models'),
  ])
  hw.value = homework
  criteria.value = criteriaData
  aiModels.value = modelData
  selectedCriteriaId.value = availableCriteria.value.some((item) => item.id === homework.ai_criteria_id)
    ? homework.ai_criteria_id
    : availableCriteria.value[0]?.id ?? null
  selectedModelId.value = modelData.find((item) => item.available)?.id ?? null
  syncReviewForm(homework)
}

async function generateAiReview() {
  requestError.value = ''
  if (!selectedCriteriaId.value) {
    requestError.value = '请先选择一条文字或附件评分标准。'
    return
  }
  if (!selectedModelId.value) {
    requestError.value = '请先选择一个已配置 API Key 的评分模型。'
    return
  }
  generating.value = true
  try {
    const { data } = await api.post(`/teacher/homework/${route.params.id}/ai-review`, {
      criteria_id: selectedCriteriaId.value,
      model_id: selectedModelId.value,
    })
    hw.value = data
    syncReviewForm(data)
  } catch (err) {
    requestError.value = err.response?.data?.detail || '生成 AI 建议失败，请稍后重试。'
  } finally {
    generating.value = false
  }
}

function resetComment() {
  if (!hw.value.ai_comment) {
    requestError.value = '当前没有可恢复的 AI 原始评语。'
    return
  }
  reviewForm.comment = hw.value.ai_comment
  requestError.value = ''
}

async function confirmReview() {
  requestError.value = ''
  if (!Number.isInteger(reviewForm.score) || reviewForm.score < 0 || reviewForm.score > 100) {
    requestError.value = '请填写 0 到 100 的整数分数。'
    return
  }
  if (!reviewForm.comment.trim()) {
    requestError.value = '请确认或修改教师评语后再完成批改。'
    return
  }

  confirming.value = true
  try {
    const { data } = await api.post(`/teacher/grade/${route.params.id}`, reviewForm)
    hw.value = data
    syncReviewForm(data)
  } catch (err) {
    requestError.value = err.response?.data?.detail || '完成复核失败，请稍后重试。'
  } finally {
    confirming.value = false
  }
}

onMounted(async () => {
  try {
    await loadHomework()
  } catch (err) {
    requestError.value = err.response?.data?.detail || '加载作业失败，请返回列表重试。'
  } finally {
    loading.value = false
  }
})
</script>
