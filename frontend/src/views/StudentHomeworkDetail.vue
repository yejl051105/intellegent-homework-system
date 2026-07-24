<template>
  <div class="homework-detail">
    <div class="page-header">
      <h2>作业详情</h2>
      <router-link to="/student/dashboard">
        <el-button><el-icon><arrow-left /></el-icon>返回我的作业</el-button>
      </router-link>
    </div>

    <el-skeleton :loading="loading" animated :count="2">
      <el-result v-if="error" icon="error" title="无法查看该作业" :sub-title="error">
        <template #extra>
          <router-link to="/student/dashboard"><el-button type="primary">返回我的作业</el-button></router-link>
        </template>
      </el-result>

      <div v-else-if="homework.id" class="detail-layout">
        <section class="detail-paper">
          <div class="detail-paper-head">
            <div>
              <p>SUBMISSION</p>
              <h3>{{ homework.title }}</h3>
            </div>
            <el-tag v-if="homework.is_exemplary" type="success">优秀作业</el-tag>
          </div>
          <div class="detail-meta-row">
            <span><el-icon><calendar /></el-icon>提交于 {{ formatDate(homework.submitted_at) }}</span>
            <span v-if="homework.graded_at"><el-icon><checked /></el-icon>批改于 {{ formatDate(homework.graded_at) }}</span>
          </div>
          <el-image
            v-if="homework.filename"
            :src="`/uploads/${homework.filename}`"
            :alt="`${homework.title} 的作业图片`"
            class="homework-image"
            fit="contain"
            :preview-src-list="[`/uploads/${homework.filename}`]"
            preview-teleported
          />
        </section>

        <aside class="detail-feedback">
          <el-card class="score-summary" shadow="never">
            <p class="feedback-eyebrow">REVIEW STATUS</p>
            <template v-if="homework.score !== null">
              <span class="score-label">教师评分</span>
              <strong class="score-value">{{ homework.score }}<small>/100</small></strong>
              <span class="grade-ready"><el-icon><circle-check-filled /></el-icon>已完成批改</span>
            </template>
            <template v-else>
              <span class="score-label">当前状态</span>
              <strong class="score-pending">等待批改</strong>
              <p class="pending-copy">教师完成批改后，评分与评语会显示在这里。</p>
            </template>
          </el-card>

          <el-card class="feedback-card" shadow="never">
            <div class="feedback-title"><el-icon><chat-line-round /></el-icon><h3>教师评语</h3></div>
            <p v-if="homework.comment?.trim()" class="feedback-comment">{{ homework.comment }}</p>
            <p v-else class="feedback-empty">{{ homework.score !== null ? '教师暂未填写文字评语。' : '作业尚未批改，暂时没有评语。' }}</p>
          </el-card>
        </aside>
      </div>
    </el-skeleton>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const homework = ref({})
const loading = ref(true)
const error = ref('')

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
    const { data } = await api.get(`/student/homework/${route.params.id}`)
    homework.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || '加载作业详情失败，请稍后重试。'
  } finally {
    loading.value = false
  }
})
</script>
