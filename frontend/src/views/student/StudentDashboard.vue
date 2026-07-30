<template>
  <div>
    <div class="page-header">
      <h2>我的作业</h2>
      <router-link to="/student/upload">
        <el-button type="primary">提交新作业</el-button>
      </router-link>
    </div>

    <el-empty v-if="!loading && homeworks.length === 0" description="还没有提交过作业">
      <router-link to="/student/upload">
        <el-button type="primary">立即提交</el-button>
      </router-link>
    </el-empty>

    <el-skeleton :loading="loading" animated :count="3" v-else>
      <div
        v-for="hw in homeworks"
        :key="hw.id"
        class="hw-card-link"
        role="link"
        tabindex="0"
        @click="openDetail(hw.id)"
        @keydown.enter.self="openDetail(hw.id)"
      >
        <el-card class="hw-card" shadow="hover">
          <div class="card-header-row">
            <h3>{{ hw.title }}</h3>
            <el-tag v-if="hw.is_exemplary" type="success" size="small">优秀作业</el-tag>
          </div>
          <div class="card-meta">提交时间：{{ hw.submitted_at?.slice(0, 10) }}</div>
          <div v-if="hw.score !== null" class="card-score">
            <el-tag type="primary">得分：{{ hw.score }}</el-tag>
          </div>
          <div v-else class="card-score">
            <el-tag type="warning">待批改</el-tag>
          </div>
          <div v-if="hw.comment" class="card-comment">
            <strong>评语：</strong>{{ hw.comment }}
          </div>
          <div class="card-action">查看作业详情 <el-icon><arrow-right /></el-icon></div>
          <template #footer>
            <el-popconfirm title="删除后可在回收站恢复，确定删除吗？" @confirm="deleteHomework(hw.id)">
              <template #reference>
                <el-button type="danger" plain size="small" @click.stop>删除作业</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-card>
      </div>
    </el-skeleton>
  </div>
</template>

<script setup>
// 学生-我的作业：本人提交的作业列表（已批改的会显示得分和评语）
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as studentApi from '@/api/student'

const router = useRouter()
const homeworks = ref([])
const loading = ref(true)

function openDetail(id) {
  router.push(`/student/homework/${id}`)
}

async function deleteHomework(id) {
  await studentApi.deleteHomework(id)
  homeworks.value = homeworks.value.filter((item) => item.id !== id)
}

onMounted(async () => {
  try {
    const { data } = await studentApi.fetchHomeworks()
    homeworks.value = data
  } finally {
    loading.value = false
  }
})
</script>
