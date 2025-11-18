<template>
  <div class="dashboard-shell">
    <aside class="dashboard-sidebar">
      <div class="sidebar-header">
        <div>
          <p class="sidebar-kicker">Travel Portal</p>
          <h3>Control Center</h3>
        </div>
        <p class="user-chip">{{ employeeName }}</p>
      </div>
      <nav>
        <RouterLink
          v-for="link in navigationLinks"
          :key="link.route.name"
          :to="link.route"
          class="sidebar-link"
          :class="{ active: isRouteActive(link.route) }"
        >
          {{ link.label }}
        </RouterLink>
      </nav>
      <button class="outline-btn" @click="handleLogout">Sign out</button>
    </aside>

    <main class="dashboard-main">
      <header class="dashboard-header">
        <div>
          <p class="dashboard-label">{{ roleLabel }}</p>
          <h1>{{ headerTitle }}</h1>
          <p class="dashboard-subtitle">Manage travel requests, approvals, and bookings.</p>
        </div>
        <div class="dashboard-actions">
          <span class="status-pill">Session Active</span>
        </div>
      </header>

      <section class="dashboard-content">
        <RouterView />
      </section>
    </main>
  </div>
</template>

<script>
import { mapActions, mapState } from 'pinia'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'DashboardLayout',
  computed: {
    ...mapState(useAuthStore, ['employeeName', 'role']),
    navigationLinks() {
      const links = [
        { label: 'Employee Hub', route: { name: 'dashboard.employee' }, roles: ['employee'] },
        { label: 'Manager Console', route: { name: 'dashboard.manager' }, roles: ['manager'] },
        { label: 'HR Command Center', route: { name: 'dashboard.hr' }, roles: ['hr'] },
      ]
      return links.filter((link) => !link.roles || link.roles.includes(this.role || 'employee'))
    },
    roleLabel() {
      switch (this.role) {
        case 'manager':
          return 'Manager Console'
        case 'hr':
          return 'HR Command Center'
        default:
          return 'Employee Hub'
      }
    },
    headerTitle() {
      switch (this.role) {
        case 'manager':
          return 'Keep approvals moving'
        case 'hr':
          return 'Oversee every booking'
        default:
          return 'Plan your next trip'
      }
    },
  },
  methods: {
    ...mapActions(useAuthStore, ['logout']),
    async handleLogout() {
      await this.logout()
      this.$router.replace({ name: 'login' })
    },
    isRouteActive(route) {
      return this.$route.name === route.name
    },
  },
}
</script>

<style scoped>
.dashboard-shell {
  display: grid;
  grid-template-columns: minmax(240px, 320px) 1fr;
  min-height: 100vh;
}

.dashboard-sidebar {
  background: white;
  border-right: 1px solid rgba(15, 23, 42, 0.08);
  padding: 2rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sidebar-header h3 {
  margin: 0.25rem 0 0;
}

.sidebar-kicker {
  margin: 0;
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  color: var(--slate-500);
}

.user-chip {
  background: var(--slate-100);
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  display: inline-flex;
  font-weight: 600;
}

.sidebar-link {
  display: block;
  padding: 0.85rem 1rem;
  border-radius: 0.8rem;
  color: var(--slate-600);
  font-weight: 600;
}

.sidebar-link.active {
  background: var(--primary-50);
  color: var(--primary-600);
}

.outline-btn {
  border: 1px solid var(--slate-200);
  border-radius: 0.8rem;
  padding: 0.75rem 1rem;
  background: transparent;
  font-weight: 600;
  cursor: pointer;
}

.dashboard-main {
  padding: 2.5rem clamp(1rem, 4vw, 3rem);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;
}

.dashboard-label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--slate-500);
  margin: 0;
}

.dashboard-header h1 {
  margin: 0.2rem 0;
}

.dashboard-subtitle {
  margin: 0;
  color: var(--slate-500);
}

.status-pill {
  display: inline-flex;
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  background: var(--success-100);
  color: var(--success-500);
  font-weight: 600;
}

.dashboard-content {
  min-height: 70vh;
}

@media (max-width: 992px) {
  .dashboard-shell {
    grid-template-columns: 1fr;
  }

  .dashboard-sidebar {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
  }

  nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .outline-btn {
    width: 100%;
  }
}
</style>
