<template>
  <div class="homework-detail exemplary-detail">
    <div class="page-header">
      <h2>优秀作业详情</h2>
      <el-tooltip content="返回优秀作业" placement="left">
        <el-button circle plain aria-label="返回优秀作业" @click="router.push(backPath)">
          <el-icon><arrow-left /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <el-skeleton :loading="loading" animated :count="2">
      <el-result v-if="error" icon="error" title="无法查看该优秀作业" :sub-title="error">
        <template #extra>
          <el-button type="primary" @click="router.push(backPath)">返回优秀作业</el-button>
        </template>
      </el-result>

      <div v-else-if="homework.id" class="detail-layout">
        <section class="detail-paper">
          <div class="detail-paper-head">
            <div>
              <p>EXEMPLARY SUBMISSION</p>
              <h3>{{ homework.title }}</h3>
            </div>
            <div class="exemplary-detail-badges">
              <el-tag type="success">优秀作业</el-tag>
              <el-tooltip content="点击图片可放大" placement="top">
                <span class="image-preview-badge" aria-label="图片支持放大预览"><el-icon><zoom-in /></el-icon></span>
              </el-tooltip>
            </div>
          </div>

          <div class="detail-meta-row">
            <span><el-icon><user /></el-icon>{{ homework.student_name }}</span>
            <span><el-icon><calendar /></el-icon>提交于 {{ formatDate(homework.submitted_at) }}</span>
            <span v-if="homework.graded_at"><el-icon><checked /></el-icon>批改于 {{ formatDate(homework.graded_at) }}</span>
          </div>

          <el-image
            v-if="homework.filename"
            :src="`/uploads/${homework.filename}`"
            :alt="`${homework.student_name}的优秀作业图片`"
            class="homework-image"
            fit="contain"
            :preview-src-list="[`/uploads/${homework.filename}`]"
            preview-teleported
          >
            <template #error>
              <div class="image-load-error"><el-icon><picture /></el-icon><span>作业图片加载失败</span></div>
            </template>
          </el-image>
        </section>

        <aside class="detail-feedback">
          <el-card class="score-summary" shadow="never">
            <p class="feedback-eyebrow">FINAL SCORE</p>
            <span class="score-label">学生成绩</span>
            <strong v-if="homework.score !== null" class="score-value">{{ homework.score }}<small>/100</small></strong>
            <strong v-else class="score-pending">暂无成绩</strong>
            <span v-if="homework.score !== null" class="grade-ready"><el-icon><circle-check-filled /></el-icon>已完成批改</span>
          </el-card>

          <el-card class="feedback-card" shadow="never">
            <div class="feedback-title"><el-icon><chat-line-round /></el-icon><h3>教师评语</h3></div>
            <p v-if="homework.comment?.trim()" class="feedback-comment">{{ homework.comment }}</p>
            <p v-else class="feedback-empty">教师暂未填写文字评语。</p>
          </el-card>
        </aside>
      </div>
    </el-skeleton>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const homework = ref({})
const loading = ref(true)
const error = ref('')

const role = computed(() => route.meta.role)
const backPath = computed(() => `/${role.value}/exemplary`)

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(async () => {
  try {
    const { data } = await api.get(`/${role.value}/exemplary/${route.params.id}`)
    homework.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || '加载优秀作业详情失败，请稍后重试。'
  } finally {
    loading.value = false
  }
})
</script>
