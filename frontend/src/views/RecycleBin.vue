<template>
  <div>
    <div class="page-header">
      <h2>回收站</h2>
      <el-tooltip :content="`返回${role === 'teacher' ? '全部作业' : '我的作业'}`" placement="left">
        <el-button circle plain aria-label="返回作业列表" @click="router.push(backPath)">
          <el-icon><arrow-left /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <el-alert
      v-if="requestError"
      class="recycle-alert"
      type="error"
      :title="requestError"
      show-icon
      :closable="false"
    />

    <el-empty v-if="!loading && homeworks.length === 0" description="回收站是空的" />

    <el-skeleton :loading="loading" animated :count="3" v-else>
      <el-card v-for="hw in homeworks" :key="hw.id" class="hw-card recycle-card" shadow="hover">
        <div class="card-header-row">
          <h3>{{ hw.title }}</h3>
          <el-tag type="info" size="small">已删除</el-tag>
        </div>
        <div v-if="role === 'teacher'" class="card-meta">学生：{{ hw.student_name }}</div>
        <div class="card-meta">提交时间：{{ hw.submitted_at?.slice(0, 10) }}</div>
        <div class="card-meta">删除时间：{{ deletedAt(hw)?.slice(0, 10) || '刚刚' }}</div>
        <div v-if="hw.score !== null" class="card-score">
          <el-tag type="primary">得分：{{ hw.score }}</el-tag>
        </div>
        <template #footer>
          <el-button type="primary" size="small" :loading="workingId === hw.id" @click="restore(hw.id)">
            恢复作业
          </el-button>
          <el-popconfirm
            title="永久删除后无法恢复，确定继续吗？"
            confirm-button-text="永久删除"
            cancel-button-text="取消"
            @confirm="permanentlyDelete(hw.id)"
          >
            <template #reference>
              <el-button type="danger" plain size="small" :loading="workingId === hw.id">永久删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-card>
    </el-skeleton>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const role = computed(() => route.meta.role)
const basePath = computed(() => `/${role.value}`)
const backPath = computed(() => `${basePath.value}/dashboard`)
const homeworks = ref([])
const loading = ref(true)
const workingId = ref(null)
const requestError = ref('')

function deletedAt(homework) {
  return homework[`${role.value}_deleted_at`] || homework.deleted_at
}

async function loadRecycleBin() {
  const { data } = await api.get(`${basePath.value}/recycle-bin`)
  homeworks.value = data
}

async function runAction(id, action) {
  requestError.value = ''
  workingId.value = id
  try {
    await action()
    await loadRecycleBin()
  } catch (err) {
    requestError.value = err.response?.data?.detail || '操作失败，请稍后重试。'
  } finally {
    workingId.value = null
  }
}

function restore(id) {
  return runAction(id, () => api.post(`${basePath.value}/homework/${id}/restore`))
}

function permanentlyDelete(id) {
  return runAction(id, () => api.delete(`${basePath.value}/homework/${id}/permanent`))
}

onMounted(async () => {
  try {
    await loadRecycleBin()
  } catch (err) {
    requestError.value = err.response?.data?.detail || '加载回收站失败，请稍后重试。'
  } finally {
    loading.value = false
  }
})
</script>
