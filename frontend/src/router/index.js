// 路由模块：只静态注册登录页，业务页面全部在登录后按后端权限动态注册。
//
// 流程：登录成功 → loadAuthorizedRoutes() 调 /api/routes 拿到当前角色的
// 路由表 → 按 component 字段（组件文件名）注册到 router → 跳转角色首页。
// 退出登录 / 会话失效时用 resetAuthorizedRoutes() 移除已注册的动态路由。
import { ref } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { fetchAuthorizedRoutes } from '@/api/auth'

// 视图按角色放在 views/ 的子目录下，组件名（文件名）保持全局唯一，
// 后端权限接口只返回组件名，这里按文件名建立映射。
const viewLoaders = Object.fromEntries(
  Object.entries(import.meta.glob('../views/**/*.vue')).map(([path, loader]) => [
    path.split('/').pop().replace('.vue', ''),
    loader,
  ])
)

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: viewLoaders.Login,
    meta: { guest: true, title: '登录' },
  },
  { path: '/', name: 'Root', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 当前角色的路由表（AppNav 用它渲染导航菜单）
export const authorizedRoutes = ref([])

let homePath = '/login'          // 当前角色的首页路径
let routesLoaded = false         // 动态路由是否已注册
let loadingPromise = null        // 进行中的加载 Promise，避免并发重复请求
const dynamicRouteNames = new Set()  // 已注册的动态路由名，退出时按名移除

function resolveView(componentName) {
  // 按后端返回的组件名找到对应的懒加载器；找不到说明前后端路由配置不同步
  const loader = viewLoaders[componentName]
  if (!loader) {
    throw new Error(`后端返回了未知页面组件：${componentName}`)
  }
  return loader
}

// 拉取并注册当前角色的动态路由，返回角色首页路径（幂等，可重复调用）
export async function loadAuthorizedRoutes() {
  if (routesLoaded) return homePath
  // 多个页面守卫可能同时触发加载，复用同一个 Promise，避免重复 addRoute 报错或闪烁。
  if (loadingPromise) return loadingPromise

  loadingPromise = fetchAuthorizedRoutes().then(({ data }) => {
    const routeRecords = Array.isArray(data.routes) ? data.routes : []

    for (const route of routeRecords) {
      if (!route.path || !route.name || !route.component) {
        throw new Error('后端返回的路由配置不完整')
      }
      // 路由记录来自后端权限配置，真正的组件加载器只从本地 viewLoaders 白名单里取。
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

// 退出登录 / 会话失效时调用：移除全部动态路由并复位状态
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

// 全局守卫：保证进入业务页面前动态路由已注册；会话失效则回登录页
router.beforeEach(async (to) => {
  const hasCachedUser = Boolean(sessionStorage.getItem('user'))

  // 未登录访问登录页：直接放行，不请求后端
  if (to.meta.guest && !hasCachedUser) return true

  try {
    const currentHome = await loadAuthorizedRoutes()

    // 已登录还访问登录页或根路径：跳去角色首页
    if (to.meta.guest || to.path === '/') return currentHome

    // 刷新页面直接访问业务路由时，首次解析发生在动态路由注册之前，
    // 注册完成后需要重新解析一次才能命中
    const resolved = router.resolve(to.fullPath)
    // 如果后端权限里仍没有这条路由，就回角色首页，避免停在空白页。
    if (!resolved.matched.length) return currentHome
    if (!to.matched.length) return to.fullPath

    return true
  } catch {
    // /api/routes 请求失败（多为会话过期）：清理状态回登录页
    resetAuthorizedRoutes()
    sessionStorage.removeItem('user')
    return to.meta.guest ? true : '/login'
  }
})

export default router
