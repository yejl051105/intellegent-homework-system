<template>
  <div>
    <div class="page-header">
      <h2>全部作业</h2>
    </div>

    <el-empty v-if="!loading && homeworks.length === 0" description="暂无作业提交" />

    <el-skeleton :loading="loading" animated :count="3" v-else>
      <el-card v-for="hw in homeworks" :key="hw.id" class="hw-card" shadow="hover">
        <div class="card-header-row">
          <h3>{{ hw.title }}</h3>
          <el-tag v-if="hw.is_exemplary" type="success" size="small">优秀</el-tag>
        </div>
        <div class="card-meta">学生：{{ hw.student_name }}</div>
        <div class="card-meta">提交时间：{{ hw.submitted_at?.slice(0, 10) }}</div>
        <div class="card-score">
          <el-tag v-if="hw.score !== null" type="primary">得分：{{ hw.score }}</el-tag>
          <el-tag v-else-if="hw.review_status === 'ai_suggested'" type="info">待教师复核</el-tag>
          <el-tag v-else type="warning">待 AI 评阅</el-tag>
        </div>
        <div v-if="hw.comment" class="card-comment"><strong>评语：</strong>{{ hw.comment }}</div>
        <template #footer>
          <el-button type="primary" size="small" @click="grade(hw.id)">批改</el-button>
          <el-button
            v-if="!hw.is_exemplary"
            size="small"
            @click="setExemplary(hw.id)"
          >设为优秀</el-button>
          <el-button v-else size="small" @click="unsetExemplary(hw.id)">取消优秀</el-button>
          <el-popconfirm title="删除后可在回收站恢复，确定删除吗？" @confirm="deleteHomework(hw.id)">
            <template #reference>
              <el-button type="danger" plain size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-card>
    </el-skeleton>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const homeworks = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/teacher/homeworks')
    homeworks.value = data
  } finally {
    loading.value = false
  }
})

function grade(id) {
  router.push(`/teacher/grade/${id}`)
}

async function setExemplary(id) {
  await api.post(`/teacher/exemplary/${id}`)
  location.reload()
}

async function unsetExemplary(id) {
  await api.post(`/teacher/unexemplary/${id}`)
  location.reload()
}

async function deleteHomework(id) {
  await api.post(`/teacher/homework/${id}/delete`)
  location.reload()
}
</script>
