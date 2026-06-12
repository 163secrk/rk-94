import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layout/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Projects.vue'),
        meta: { title: '公益项目' },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Home.vue'),
        meta: { title: '个人中心' },
      },
      {
        path: 'verification',
        name: 'Verification',
        component: () => import('@/views/Verification.vue'),
        meta: { title: '实名认证' },
      },
      {
        path: 'projects/create',
        name: 'ProjectCreate',
        component: () => import('@/views/ProjectCreate.vue'),
        meta: { title: '发起项目', roles: ['initiator'] },
      },
      {
        path: 'projects/my',
        name: 'MyProjects',
        component: () => import('@/views/MyProjects.vue'),
        meta: { title: '我的项目', roles: ['initiator'] },
      },
      {
        path: 'projects/audit',
        name: 'ProjectAudit',
        component: () => import('@/views/ProjectAudit.vue'),
        meta: { title: '项目审核', roles: ['auditor'] },
      },
      {
        path: 'verification/audit',
        name: 'VerificationAudit',
        component: () => import('@/views/VerificationAudit.vue'),
        meta: { title: '实名认证审核', roles: ['auditor'] },
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/ProjectDetail.vue'),
        meta: { title: '项目详情' },
      },
      {
        path: 'expenditures',
        name: 'ExpenditureList',
        component: () => import('@/views/ExpenditureList.vue'),
        meta: { title: '支出记录' },
      },
      {
        path: 'expenditures/create',
        name: 'ExpenditureCreate',
        component: () => import('@/views/ExpenditureCreate.vue'),
        meta: { title: '登记支出', roles: ['auditor'] },
      },
      {
        path: 'expenditures/:id',
        name: 'ExpenditureDetail',
        component: () => import('@/views/ExpenditureDetail.vue'),
        meta: { title: '支出详情' },
      },
      {
        path: 'donations/:id/tracking',
        name: 'DonationTracking',
        component: () => import('@/views/DonationTracking.vue'),
        meta: { title: '捐款追踪' },
      },
      {
        path: 'projects/updates/create',
        name: 'ProjectUpdateCreate',
        component: () => import('@/views/ProjectUpdateCreate.vue'),
        meta: { title: '发布项目进展', roles: ['initiator'] },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  document.title = `${to.meta.title || '爱心汇'} - 捐赠管理平台`

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
    next('/')
  } else if (to.meta.roles && Array.isArray(to.meta.roles)) {
    const userRole = userStore.userInfo?.role
    if (!userRole || !(to.meta.roles as string[]).includes(userRole)) {
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
