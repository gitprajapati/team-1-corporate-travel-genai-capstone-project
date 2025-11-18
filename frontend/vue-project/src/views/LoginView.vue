<template>
  <div class="auth-layout">
    <section class="auth-hero">
      <p class="auth-pill">YASH Corporate Travel Hub</p>
      <h1>Plan, approve, and book travel in one workspace.</h1>
      <p>
        Use your single corporate identity to unlock AI copilots for booking, approvals, and spend
        insights — all secured with policy guardrails.
      </p>

      <ul class="auth-hero__highlights">
        <li>
          <span class="dot"></span>
          Real-time approvals routed to the right manager
        </li>
        <li>
          <span class="dot"></span>
          HR concierge available 24	7 for complex itineraries
        </li>
        <li>
          <span class="dot"></span>
          Built-in policy nudges keep every booking compliant
        </li>
      </ul>

      <div class="auth-hero__stat-grid">
        <article class="stat-card">
          <p class="stat-card__value">98%</p>
          <p class="stat-card__label">Policy compliance</p>
        </article>
        <article class="stat-card">
          <p class="stat-card__value">3 mins</p>
          <p class="stat-card__label">Avg. approval time</p>
        </article>
        <article class="stat-card">
          <p class="stat-card__value">40+</p>
          <p class="stat-card__label">Business units onboarded</p>
        </article>
      </div>
    </section>

    <section class="auth-card">
      <div class="auth-card__header">
        <img src="/logo.png" alt="Company logo" class="auth-card__logo" />
        <div>
          <h2>Sign in</h2>
          <p>Enter your credentials to continue</p>
        </div>
      </div>
      <form @submit.prevent="handleLogin">
        <label>
          Employee ID or Email
          <input v-model="form.identifier" type="text" placeholder="EMP001 or user@company.com" required />
        </label>

        <label>
          Password
          <input v-model="form.password" type="password" placeholder="••••••••" required />
        </label>

        <p v-if="formError" class="auth-card__error">{{ formError }}</p>

        <button class="primary-btn" type="submit" :disabled="loading">
          {{ loading ? 'Signing in...' : 'Access Dashboard' }}
        </button>

        <p class="auth-card__hint">
          Tip: Use the same password you use for your laptop login. Need help? <a href="mailto:travel-support@yash.com">Contact support</a>
        </p>
      </form>

      <div class="auth-card__footer">
        <div>
          Need an account?
          <RouterLink to="/register">Register here</RouterLink>
        </div>
        <div class="auth-card__support">
          <span>📞 +91 80 1234 5678</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'LoginView',
  data() {
    return {
      form: {
        identifier: '',
        password: '',
      },
      formError: '',
    }
  },
  computed: {
    ...mapState(useAuthStore, ['loading', 'error', 'isAuthenticated', 'role']),
  },
  watch: {
    isAuthenticated(newValue) {
      if (newValue) {
        this.$router.replace(this.destinationRoute())
      }
    },
    error(newValue) {
      if (newValue) {
        this.formError = newValue
      }
    },
  },
  methods: {
    ...mapActions(useAuthStore, ['login']),
    async handleLogin() {
      this.formError = ''
      if (!this.form.identifier || !this.form.password) {
        this.formError = 'Please provide both fields.'
        return
      }

      try {
        await this.login({ ...this.form })
        this.$router.replace(this.destinationRoute())
      } catch (error) {
        if (!this.formError) {
          this.formError = error?.response?.data?.detail || 'Login failed'
        }
      }
    },
    destinationRoute() {
      const redirect = this.$route.query.redirect
      if (redirect) {
        return redirect
      }

      switch (this.role) {
        case 'manager':
          return { name: 'dashboard.manager' }
        case 'hr':
          return { name: 'dashboard.hr' }
        default:
          return { name: 'dashboard.employee' }
      }
    },
  },
  mounted() {
    if (this.isAuthenticated) {
      this.$router.replace(this.destinationRoute())
    }
  },
}
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2.5rem;
  padding: 3rem clamp(1rem, 5vw, 5rem);
}

.auth-hero {
  padding: 2rem;
  border-radius: 1.5rem;
  background: radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 55%),
    radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.2), transparent 45%),
    #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.auth-logo {
  width: 120px;
  height: auto;
  margin-bottom: 1rem;
}

.auth-pill {
  display: inline-flex;
  padding: 0.3rem 0.9rem;
  border-radius: 999px;
  background: var(--primary-50);
  color: var(--primary-600);
  font-weight: 600;
}

.auth-hero h1 {
  margin-top: 1rem;
  font-size: clamp(2rem, 4vw, 3rem);
}

.auth-hero p {
  color: var(--slate-600);
  max-width: 520px;
}

.auth-hero__highlights {
  margin-top: 1.25rem;
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  color: var(--slate-600);
}

.auth-hero__highlights .dot {
  width: 0.55rem;
  height: 0.55rem;
  display: inline-flex;
  margin-right: 0.5rem;
  border-radius: 50%;
  background: var(--primary-500);
}

.auth-hero__stat-grid {
  margin-top: 1.75rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.9rem;
}

.stat-card {
  padding: 1rem 1.25rem;
  border-radius: 1rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: white;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4), 0 10px 30px rgba(15, 23, 42, 0.08);
}

.stat-card__value {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.stat-card__label {
  margin: 0.2rem 0 0;
  color: var(--slate-500);
  font-size: 0.9rem;
}

.auth-card {
  background: white;
  border-radius: 1.5rem;
  padding: 2.5rem;
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.12);
}


.auth-card__header {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
}

.auth-card__header h2 {
  margin: 0;
  font-size: 2rem;
}

.auth-card__header p {
  color: var(--slate-500);
  margin-top: 0.25rem;
}

.auth-card__logo {
  width: 80px;
  margin-bottom: 1rem;
}

.auth-card__chip {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--primary-700);
  font-weight: 600;
  font-size: 0.85rem;
}

form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 2rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  color: var(--slate-600);
}

input {
  border-radius: 0.9rem;
  border: 1px solid var(--slate-200);
  padding: 0.85rem 1rem;
  transition: border 0.2s;
}

input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.primary-btn {
  border: none;
  border-radius: 0.9rem;
  padding: 0.9rem 1rem;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.primary-btn:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 15px 30px rgba(79, 70, 229, 0.4);
}

.auth-card__error {
  background: var(--danger-100);
  color: var(--danger-500);
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  margin: 0;
}

.auth-card__hint {
  margin: 0.5rem 0 0;
  color: var(--slate-500);
  font-size: 0.9rem;
}

.auth-card__hint a {
  color: var(--primary-600);
  text-decoration: underline;
}

.auth-card__footer {
  margin-top: 1.5rem;
  color: var(--slate-500);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.auth-card__support {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: var(--slate-600);
}

@media (max-width: 768px) {
  .auth-layout {
    padding: 2rem 1.25rem 3rem;
  }

  .auth-card {
    padding: 2rem 1.5rem;
  }
}
</style>
