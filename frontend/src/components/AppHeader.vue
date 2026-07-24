<template>
  <header class="app-header">
    <router-link to="/" class="logo" aria-label="阅作作业批改系统首页">
      <span class="logo-mark">阅</span>
      <span class="logo-copy">
        <strong>阅作</strong>
        <small>作业批改系统</small>
      </span>
    </router-link>
    <div class="header-right">
      <div class="user-chip">
        <span class="user-avatar">{{ user.name?.slice(0, 1) }}</span>
        <span class="user-info">
          <small>{{ user.role === 'student' ? '学生空间' : '教师空间' }}</small>
          <strong>{{ user.name }}</strong>
        </span>
      </div>
      <el-button class="logout-button" circle title="退出登录" aria-label="退出登录" @click="$emit('logout')">
        <el-icon><switch-button /></el-icon>
      </el-button>
    </div>
  </header>
</template>

<script setup>
defineProps({ user: { type: Object, required: true } })
defineEmits(['logout'])
</script>
