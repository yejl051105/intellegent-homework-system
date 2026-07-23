<template>
  <nav class="app-nav" v-if="user">
    <div class="nav-inner">
      <button
        v-for="item in navItems"
        :key="item.path"
        type="button"
        class="nav-link"
        :class="{ 'nav-link--active': isActive(item) }"
        :aria-current="isActive(item) ? 'page' : undefined"
        @click="navigate(item.path)"
      >
        <el-icon><component :is="item.icon" /></el-icon>{{ item.label }}
      </button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Collection, Delete, Files, Medal, Tickets, TrophyBase, UploadFilled } from '@element-plus/icons-vue'
import { authorizedRoutes } from '../router'

const props = defineProps({ user: { type: Object, required: true } })
const route = useRoute()
const router = useRouter()

const iconMap = { Collection, Delete, Files, Medal, Tickets, TrophyBase, UploadFilled }

const navItems = computed(() => authorizedRoutes.value
  .filter((item) => item.meta?.nav && item.meta.role === props.user.role)
  .sort((a, b) => (a.meta.order || 0) - (b.meta.order || 0))
  .map((item) => ({
    label: item.meta.title,
    path: item.path,
    activePrefixes: item.meta.activePrefixes || [item.path],
    icon: iconMap[item.meta.icon],
  })))

function isActive(item) {
  return item.activePrefixes.some((prefix) => route.path.startsWith(prefix))
}

function navigate(path) {
  if (route.path !== path) router.push(path)
}
</script>
