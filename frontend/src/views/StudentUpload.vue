<template>
  <div>
    <div class="page-header">
      <h2>提交作业</h2>
    </div>
    <el-card shadow="never" class="form-card">
      <el-form @submit.prevent="handleSubmit" label-position="top">
        <el-form-item label="作业标题" required>
          <el-input v-model="title" placeholder="例如：第一次作业" />
        </el-form-item>
        <el-form-item label="作业图片" required>
          <el-upload
            ref="uploadRef"
            drag
            accept="image/*"
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将图片拖拽到此处，或<em>点击选择</em></div>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="submitting" style="width:100%">
            {{ submitting ? '提交中...' : '提交作业' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const title = ref('')
const file = ref(null)
const submitting = ref(false)
const uploadRef = ref(null)

function onFileChange(uploadFile) {
  file.value = uploadFile.raw
}

function onFileRemove() {
  file.value = null
}

async function handleSubmit() {
  if (!title.value || !file.value) return
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('title', title.value)
    fd.append('image', file.value)
    await api.post('/student/upload', fd)
    router.push('/student/dashboard')
  } finally {
    submitting.value = false
  }
}
</script>
