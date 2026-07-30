<template>
  <div class="app-container" :class="{ 'is-authenticated': user }">
    <AppHeader v-if="user" :user="user" @logout="handleLogout" />
      <AppNav v-if="user" :user="user" />
    <main class="app-main" :class="{ 'app-main--guest': !user }">
      <router-view v-slot="{ Component, route }">
        <keep-alive>
          <component :is="Component" v-if="route.meta.keepAlive" :key="route.name" />
        </keep-alive>
        <component :is="Component" v-if="!route.meta.keepAlive" :key="route.name" />
      </router-view>
    </main>
  </div>
</template>

<script setup>
// 应用根组件：维护当前登录用户状态，登录后显示顶栏 + 导航的整体布局
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { resetAuthorizedRoutes } from '@/router'
import { fetchCurrentUser, logout } from '@/api/auth'
import AppHeader from '@/layouts/AppHeader.vue'
import AppNav from '@/layouts/AppNav.vue'

const router = useRouter()
const user = ref(null)

// 先用 sessionStorage 的缓存快速渲染，再由下方 watch 向后端确认会话有效性
user.value = JSON.parse(sessionStorage.getItem('user'))

// 每次进入业务页面都向后端校验会话；失效则清理状态并回登录页
watch(router.currentRoute, async (route) => {
  if (!route.meta.guest) {
    try {
      const { data } = await fetchCurrentUser()
      user.value = data
      sessionStorage.setItem('user', JSON.stringify(data))
    } catch {
      user.value = null
      sessionStorage.removeItem('user')
      if (router.currentRoute.value.path !== '/login') {
        router.replace('/login')
      }
    }
  }
}, { immediate: true })

// 退出登录：清服务端会话 → 移除动态路由 → 清本地缓存 → 回登录页
async function handleLogout() {
  await logout()
  resetAuthorizedRoutes()
  sessionStorage.removeItem('user')
  user.value = null
  router.push('/login')
}
</script>
