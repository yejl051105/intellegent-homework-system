<template>
  <div>
    <div class="page-header">
      <h2>优秀作业展示</h2>
    </div>

    <el-empty v-if="!loading && items.length === 0" description="暂无优秀作业展示" />

    <el-skeleton :loading="loading" animated :count="2" v-else>
      <div class="card-grid">
        <el-card
          v-for="e in items"
          :key="e.id"
          class="exemplary-card"
          shadow="hover"
          role="link"
          tabindex="0"
          @click="openDetail(e.id)"
          @keydown.enter.self="openDetail(e.id)"
        >
          <h3>{{ e.title }}</h3>
          <div class="card-meta">学生：{{ e.student_name }}</div>
          <div class="card-score"><el-tag type="success">成绩：{{ e.score ?? '暂无' }}</el-tag></div>
          <el-image
            v-if="e.filename"
            :src="`/uploads/${e.filename}`"
            :alt="e.title"
            class="card-img"
            fit="contain"
          />
          <div class="card-meta">提交时间：{{ e.submitted_at?.slice(0, 10) }}</div>
          <div class="card-action">查看作业详情 <el-icon><arrow-right /></el-icon></div>
        </el-card>
      </div>
    </el-skeleton>
  </div>
</template>

<script setup>
// 学生-优秀作业：浏览老师标记的优秀作业展示墙
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchExemplaryList } from '@/api/student'

const router = useRouter()
const items = ref([])
const loading = ref(true)

function openDetail(id) {
  router.push(`/student/exemplary/${id}`)
}

onMounted(async () => {
  try {
    const { data } = await fetchExemplaryList()
    items.value = data
  } finally {
    loading.value = false
  }
})
</script>
