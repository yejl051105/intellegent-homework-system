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
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { resetAuthorizedRoutes } from './router'
import api from './api'
import AppHeader from './components/AppHeader.vue'
import AppNav from './components/AppNav.vue'

const router = useRouter()
const user = ref(null)

user.value = JSON.parse(sessionStorage.getItem('user'))

watch(router.currentRoute, async (route) => {
  if (!route.meta.guest) {
    try {
      const { data } = await api.get('/me')
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

async function handleLogout() {
  await api.post('/logout')
  resetAuthorizedRoutes()
  sessionStorage.removeItem('user')
  user.value = null
  router.push('/login')
}
</script>
