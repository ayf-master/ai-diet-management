import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/LandingView.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('../views/ForgotPasswordView.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/meal',
    name: 'MealTrack',
    component: () => import('../views/MealTrackView.vue'),
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('../views/StatsView.vue'),
  },
  {
    path: '/ai-plan',
    name: 'AiPlan',
    component: () => import('../views/AiPlanView.vue'),
  },
  {
    path: '/assistant',
    name: 'Assistant',
    component: () => import('../views/AssistantView.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
  },
  {
    path: '/my-foods',
    name: 'UserFoods',
    component: () => import('../views/UserFoodsView.vue'),
  },
  {
    path: '/my-recipes',
    name: 'UserRecipes',
    component: () => import('../views/UserRecipesView.vue'),
  },
  {
    path: '/me',
    name: 'MobileMe',
    component: () => import('../views/MobileMeView.vue'),
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/admin/AdminLoginView.vue'),
  },
  {
    path: '/admin/foods',
    name: 'AdminFoods',
    component: () => import('../views/admin/AdminFoodsView.vue'),
  },
  {
    path: '/admin/recipes',
    name: 'AdminRecipes',
    component: () => import('../views/admin/AdminRecipesView.vue'),
  },
  {
    path: '/admin',
    redirect: '/admin/foods',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const user = sessionStorage.getItem('user')
  const admin = sessionStorage.getItem('admin')
  const token = sessionStorage.getItem('token')
  const publicPages = ['Landing', 'Login', 'AdminLogin', 'ForgotPassword']
  // 没有 token 的旧会话一律回登录页，避免带着过期登录态一直报 401
  if (!publicPages.includes(to.name) && (!token || (!user && !admin))) {
    next('/login')
  } else {
    next()
  }
})

export default router
