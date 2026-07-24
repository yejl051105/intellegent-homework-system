import { ref } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import api from '../api'

const viewLoaders = import.meta.glob('../views/*.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: viewLoaders['../views/Login.vue'],
    meta: { guest: true, title: '登录' },
  },
  { path: '/', name: 'Root', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export const authorizedRoutes = ref([])

let homePath = '/login'
let routesLoaded = false
let loadingPromise = null
const dynamicRouteNames = new Set()

function resolveView(componentName) {
  const loader = viewLoaders[`../views/${componentName}.vue`]
  if (!loader) {
    throw new Error(`后端返回了未知页面组件：${componentName}`)
  }
  return loader
}

export async function loadAuthorizedRoutes() {
  if (routesLoaded) return homePath
  if (loadingPromise) return loadingPromise

  loadingPromise = api.get('/routes').then(({ data }) => {
    const routeRecords = Array.isArray(data.routes) ? data.routes : []

    for (const route of routeRecords) {
      if (!route.path || !route.name || !route.component) {
        throw new Error('后端返回的路由配置不完整')
      }
      router.addRoute({
        path: route.path,
        name: route.name,
        component: resolveView(route.component),
        meta: route.meta || {},
      })
      dynamicRouteNames.add(route.name)
    }

    authorizedRoutes.value = routeRecords
    homePath = data.home || '/login'
    routesLoaded = true
    sessionStorage.setItem('user', JSON.stringify(data.user))
    return homePath
  }).finally(() => {
    loadingPromise = null
  })

  return loadingPromise
}

export function resetAuthorizedRoutes() {
  for (const name of dynamicRouteNames) {
    if (router.hasRoute(name)) router.removeRoute(name)
  }
  dynamicRouteNames.clear()
  authorizedRoutes.value = []
  homePath = '/login'
  routesLoaded = false
  loadingPromise = null
}

router.beforeEach(async (to) => {
  const hasCachedUser = Boolean(sessionStorage.getItem('user'))

  if (to.meta.guest && !hasCachedUser) return true

  try {
    const currentHome = await loadAuthorizedRoutes()

    if (to.meta.guest || to.path === '/') return currentHome

    // Direct visits are initially resolved before the permitted routes are registered.
    const resolved = router.resolve(to.fullPath)
    if (!resolved.matched.length) return currentHome
    if (!to.matched.length) return to.fullPath

    return true
  } catch {
    resetAuthorizedRoutes()
    sessionStorage.removeItem('user')
    return to.meta.guest ? true : '/login'
  }
})

export default router
