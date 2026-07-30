<template>
  <div>
    <div class="page-header">
      <h2>评分标准</h2>
      <el-tooltip content="返回作业列表" placement="left">
        <el-button circle plain aria-label="返回作业列表" @click="router.push('/teacher/dashboard')">
          <el-icon><arrow-left /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <el-card shadow="never" class="form-card criteria-form-card">
      <div class="criteria-form-head">
        <div>
          <p>RUBRIC LIBRARY</p>
          <h3>添加评分标准</h3>
        </div>
        <el-radio-group v-model="entryMode" class="criteria-mode" @change="clearInputError">
          <el-radio-button label="text"><el-icon><edit-pen /></el-icon>粘贴文字</el-radio-button>
          <el-radio-button label="file"><el-icon><document /></el-icon>上传附件</el-radio-button>
        </el-radio-group>
      </div>

      <el-alert v-if="formError" type="error" :title="formError" :closable="false" show-icon />
      <el-form label-position="top" @submit.prevent="handleAdd">
        <el-form-item label="标题" required>
          <el-input v-model.trim="form.title" placeholder="例如：第一次作文评分标准" maxlength="100" @input="clearInputError" />
        </el-form-item>

        <el-form-item v-if="entryMode === 'text'" label="文字评分标准" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="9"
            maxlength="12000"
            show-word-limit
            placeholder="例如：\n1. 内容完整，主题明确（40 分）\n2. 论证或解题过程正确（40 分）\n3. 表达规范、书写清晰（20 分）"
            @input="clearInputError"
          />
        </el-form-item>

        <el-form-item v-else label="附件（PDF / Word）" required>
          <el-upload
            ref="uploadRef"
            drag
            accept=".pdf,.doc,.docx"
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将文件拖拽到此处，或<em>点击选择</em></div>
            <template #tip><div class="criteria-upload-tip">支持 PDF、DOC、DOCX 格式</div></template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="submitting">
            {{ submitting ? '正在保存' : '保存评分标准' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-empty v-if="!loading && list.length === 0" description="还没有添加评分标准" />

    <el-card v-for="c in list" :key="c.id" class="criteria-card" shadow="hover">
      <div class="criteria-item-head">
        <div>
          <h3>{{ c.title }}</h3>
          <div class="card-meta">创建时间：{{ c.created_at?.slice(0, 10) }}</div>
        </div>
        <el-tag :type="c.source_type === 'file' ? 'info' : 'success'" size="small">{{ c.source_type === 'file' ? '附件标准' : '文字标准' }}</el-tag>
      </div>
      <p v-if="c.content" class="criteria-content">{{ c.content }}</p>
      <div v-if="c.filename" class="criteria-file-link">
        <el-link :href="`/uploads/${c.filename}`" target="_blank" type="primary"><el-icon><document /></el-icon>查看附件</el-link>
      </div>
      <template #footer>
        <el-popconfirm title="确定删除？" @confirm="handleDelete(c.id)">
          <template #reference><el-button type="danger" size="small">删除</el-button></template>
        </el-popconfirm>
      </template>
    </el-card>
  </div>
</template>

<script setup>
// 教师-评分标准：新建（文字粘贴或 PDF/DOC/DOCX 附件二选一）与删除
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as teacherApi from '@/api/teacher'

const router = useRouter()
const list = ref([])
const loading = ref(true)
const submitting = ref(false)
const entryMode = ref('text')
const formError = ref('')
const form = reactive({ title: '', content: '' })
const uploadFile = ref(null)
const uploadRef = ref(null)

async function loadCriteria() {
  const { data } = await teacherApi.fetchCriteria()
  list.value = data
}

loadCriteria().finally(() => { loading.value = false })

function clearInputError() {
  formError.value = ''
}

function onFileChange(uploadFile_) {
  uploadFile.value = uploadFile_.raw
  clearInputError()
}

function onFileRemove() {
  uploadFile.value = null
}

function resetForm() {
  form.title = ''
  form.content = ''
  uploadFile.value = null
  uploadRef.value?.clearFiles()
}

async function handleAdd() {
  formError.value = ''
  if (!form.title) {
    formError.value = '请输入评分标准标题。'
    return
  }
  if (entryMode.value === 'text' && !form.content.trim()) {
    formError.value = '请粘贴文字评分标准。'
    return
  }
  if (entryMode.value === 'file' && !uploadFile.value) {
    formError.value = '请选择评分标准附件。'
    return
  }

  submitting.value = true
  try {
    // 后端根据字段存在与否区分文字/附件模式，FormData 会自动附带正确的 multipart 边界。
    const fd = new FormData()
    fd.append('title', form.title)
    if (entryMode.value === 'text') fd.append('content', form.content)
    else fd.append('file', uploadFile.value)
    await teacherApi.createCriteria(fd)
    resetForm()
    await loadCriteria()
  } catch (err) {
    formError.value = err.response?.data?.detail || '保存评分标准失败，请稍后重试。'
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  await teacherApi.deleteCriteria(id)
  await loadCriteria()
}
</script>
