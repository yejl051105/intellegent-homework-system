<template>
  <div class="login-wrapper">
    <section class="login-stage" aria-labelledby="login-title">
      <aside class="login-aside">
        <router-link to="/login" class="login-brand" aria-label="阅作">
          <span class="logo-mark">阅</span>
          <span>阅作</span>
        </router-link>
        <div class="login-intro">
          <p class="login-kicker">HOMEWORK REVIEW</p>
          <h1 id="login-title">把每一次<br>完成，都认真看见。</h1>
          <p>作业提交、教师批改与学习反馈，汇在同一个清晰的工作空间。</p>
        </div>
        <div class="term-stamp">
          <span>2026</span>
          <i></i>
          <small>SPRING TERM</small>
        </div>
      </aside>

      <el-card class="login-card" shadow="never">
        <div class="login-card-head">
          <p>WELCOME BACK</p>
          <h2>登录你的空间</h2>
          <span>输入账号后继续</span>
        </div>
        <el-alert v-if="error" type="error" :title="error" show-icon :closable="false" />
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model.trim="loginForm.username" placeholder="请输入用户名" autocomplete="username" @input="clearRequestError">
              <template #prefix><el-icon><user /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password autocomplete="current-password" @input="clearRequestError">
              <template #prefix><el-icon><lock /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" native-type="submit" class="login-submit" :loading="submitting" :disabled="submitting">
              {{ submitting ? '正在验证' : '进入系统' }} <el-icon v-if="!submitting"><arrow-right /></el-icon>
            </el-button>
          </el-form-item>
        </el-form>
        <div class="login-hint">
          <div><span>学生测试账号</span><b>student1 / 123456</b></div>
          <div><span>教师测试账号</span><b>teacher1 / 123456</b></div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
// 登录页（学生/教师共用）：登录成功后加载动态路由并跳转角色首页
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'
import { loadAuthorizedRoutes, resetAuthorizedRoutes } from '@/router'

const router = useRouter()
const loginFormRef = ref()
const loginForm = reactive({
  username: '',
  password: '',
})
const error = ref('')
const submitting = ref(false)

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度应为 3 至 32 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度应为 6 至 64 个字符', trigger: 'blur' },
  ],
}

function clearRequestError() {
  error.value = ''
}

async function handleLogin() {
  const isValid = await loginFormRef.value.validate().catch(() => false)
  if (!isValid) return

  error.value = ''
  submitting.value = true
  try {
    const { data } = await login(loginForm)
    sessionStorage.setItem('user', JSON.stringify(data))
    const homePath = await loadAuthorizedRoutes()
    await router.replace(homePath)
  } catch (err) {
    resetAuthorizedRoutes()
    sessionStorage.removeItem('user')
    if (!err.response) {
      error.value = '登录成功，但权限路由获取失败，请确认后端已启动'
    } else if (err.response.status === 401) {
      error.value = '用户名或密码错误'
    } else {
      error.value = err.response.data?.detail || '登录服务暂时不可用，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}
</script>
