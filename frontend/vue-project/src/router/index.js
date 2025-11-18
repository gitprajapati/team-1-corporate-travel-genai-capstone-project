import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardLayout from '../views/DashboardLayout.vue'
import EmployeeDashboard from '../views/dashboards/EmployeeDashboard.vue'
import ManagerDashboard from '../views/dashboards/ManagerDashboard.vue'
import HrDashboard from '../views/dashboards/HrDashboard.vue'
import { useAuthStore } from '../stores/auth'

const TOKEN_KEY = 'travel_portal_token'
const USER_KEY = 'travel_portal_user'

function roleToRoute(role) {
  switch (role) {
    case 'manager':
      return { name: 'dashboard.manager' }
    case 'hr':
      return { name: 'dashboard.hr' }
    default:
      return { name: 'dashboard.employee' }
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/dashboard' },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true },
    },
    {
      path: '/dashboard',
      component: DashboardLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: () => '/dashboard/employee',
        },
        {
          path: 'employee',
          name: 'dashboard.employee',
          component: EmployeeDashboard,
          meta: { requiresAuth: true, roles: ['employee'] },
        },
        {
          path: 'manager',
          name: 'dashboard.manager',
          component: ManagerDashboard,
          meta: { requiresAuth: true, roles: ['manager'] },
        },
        {
          path: 'hr',
          name: 'dashboard.hr',
          component: HrDashboard,
          meta: { requiresAuth: true, roles: ['hr'] },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

function resolveAuthSnapshot() {
  let storeReference = null
  try {
    storeReference = useAuthStore()
  } catch (error) {
    storeReference = null
  }

  const localRole = JSON.parse(localStorage.getItem(USER_KEY) || 'null')?.role || null
  const token = storeReference?.token || localStorage.getItem(TOKEN_KEY) || ''
  const isAuthenticated = storeReference?.isAuthenticated || Boolean(token)
  const role = storeReference?.role || localRole

  return { store: storeReference, token, role, isAuthenticated }
}

router.beforeEach((to, from, next) => {
  const snapshot = resolveAuthSnapshot()

  if (to.meta.requiresAuth && !snapshot.isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (to.meta.guestOnly && snapshot.isAuthenticated) {
    return next(roleToRoute(snapshot.role))
  }

  if (to.meta.roles && to.meta.roles.length) {
    if (!snapshot.role || !to.meta.roles.includes(snapshot.role)) {
      if (snapshot.isAuthenticated) {
        return next(roleToRoute(snapshot.role))
      }
      return next({ name: 'login' })
    }
  }

  return next()
})

export default router
