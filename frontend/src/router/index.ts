import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

/* 路由配置 */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
    meta: { title: '智能对话' },
  },
  {
    path: '/approval',
    name: 'Approval',
    component: () => import('@/views/Approval.vue'),
    meta: { title: '审批管理' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/* 全局路由守卫：设置页面标题 */
router.beforeEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - DataAgent Pro` : 'DataAgent Pro'
})

export default router
