<template>
  <div>
    <div class="page-header">
      <h2>优秀作业</h2>
      <el-tooltip content="返回作业列表" placement="left">
        <el-button circle plain aria-label="返回作业列表" @click="router.push('/teacher/dashboard')">
          <el-icon><arrow-left /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <el-skeleton :loading="loading" animated :count="2">
      <el-empty v-if="homeworks.length === 0" description="暂无被设置为优秀的作业" />
      <el-card
        v-for="hw in homeworks"
        :key="hw.id"
        class="hw-card exemplary-card"
        shadow="hover"
        role="link"
        tabindex="0"
        @click="openDetail(hw.id)"
        @keydown.enter.self="openDetail(hw.id)"
      >
        <h3>{{ hw.title }}</h3>
        <div class="card-meta">学生：{{ hw.student_name }}</div>
        <div class="card-meta">得分：{{ hw.score }}</div>
        <template #footer>
          <el-button size="small" @click.stop="unsetExemplary(hw.id)">取消优秀</el-button>
        </template>
      </el-card>
    </el-skeleton>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const homeworks = ref([])
const loading = ref(true)

async function loadExemplaryHomeworks() {
  const { data } = await api.get('/teacher/exemplary')
  homeworks.value = data.homeworks || []
}

onMounted(async () => {
  try {
    await loadExemplaryHomeworks()
  } finally {
    loading.value = false
  }
})

async function unsetExemplary(id) {
  await api.post(`/teacher/unexemplary/${id}`)
  await loadExemplaryHomeworks()
}

function openDetail(id) {
  router.push(`/teacher/exemplary/${id}`)
}
</script>
