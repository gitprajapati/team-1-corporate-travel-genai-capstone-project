<template>
  <div class="auth-layout">
    <section class="auth-card">
      <div class="auth-card__header">
        <img src="/logo.png" alt="Company logo" class="auth-card__logo" />
        <h2>Create Account</h2>
        <p>Set up your access in less than a minute.</p>
      </div>
      <div class="auth-card__progress">
        <span class="progress-dot is-active"></span>
        <span class="progress-line"></span>
        <span class="progress-dot"></span>
        <p>Step 1 of 2 · Profile details</p>
      </div>
      <form @submit.prevent="handleRegister">
        <div class="form-grid">
          <label>
            Employee ID
            <input v-model="form.employee_id" type="text" required placeholder="EMP123" />
          </label>
          <label>
            Full Name
            <input v-model="form.name" type="text" required placeholder="Jane Doe" />
          </label>
        </div>

        <div class="form-grid">
          <label>
            Corporate Email
            <input v-model="form.email" type="email" required placeholder="you@company.com" />
          </label>
          <label>
            Grade (optional)
            <input v-model="form.grade" type="text" placeholder="E1-E8, M1+" />
          </label>
        </div>

        <div class="form-grid">
          <label>
            Department
            <input v-model="form.department" type="text" placeholder="Sales" />
          </label>
          <label>
            Designation
            <input v-model="form.designation" type="text" placeholder="Regional Manager" />
          </label>
        </div>

        <div class="form-grid">
          <label>
            Manager Employee ID (optional)
            <input v-model="form.manager_id" type="text" placeholder="EMP100" />
          </label>
          <label>
            City (optional)
            <input v-model="form.city" type="text" placeholder="Bengaluru" />
          </label>
        </div>

        <label>
          Gender (optional)
          <select v-model="form.gender">
            <option value="">Prefer not to say</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </label>

        <div class="form-grid">
          <label>
            Password
            <input v-model="form.password" type="password" required placeholder="Strong password" />
          </label>
          <label>
            Confirm Password
            <input v-model="form.confirm" type="password" required placeholder="Repeat password" />
          </label>
        </div>

        <p class="auth-card__hint">
          Use 8+ characters with a number and symbol. Your password syncs securely with IT.
        </p>

        <p v-if="formError" class="auth-card__error">{{ formError }}</p>

        <button class="primary-btn" type="submit" :disabled="loading">
          {{ loading ? 'Creating account...' : 'Create & Continue' }}
        </button>
      </form>

      <p class="auth-card__footer">
        Already onboarded? <RouterLink to="/login">Sign in</RouterLink>
      </p>
    </section>

    <section class="auth-hero">
      <p class="auth-pill">Register Here!</p>
      <h1>Unlock seamless travel workflows</h1>
      <p>
        A single account connects you to employee self-service, manager approvals, and HR concierge
        handoffs with zero email ping-pong.
      </p>

      <div class="auth-hero__feature-grid">
        <article>
          <h3>Employee hub</h3>
          <p>Track itineraries, raise travel indents, and chat with the AI assistant anytime.</p>
        </article>
        <article>
          <h3>Manager cockpit</h3>
          <p>Review requests with policy context, budget impact, and one-click approval.</p>
        </article>
        <article>
          <h3>HR concierge</h3>
          <p>Automations route complex bookings to HR MCP servers with real-time status.</p>
        </article>
      </div>

      <div class="auth-hero__cta">
        <p>Need elevated access?</p>
        <RouterLink to="/login">Request manager / HR role</RouterLink>
      </div>
    </section>
  </div>
</template>

<script>
import { mapActions, mapState } from 'pinia'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'RegisterView',
  data() {
    return {
      form: {
        employee_id: '',
        name: '',
        email: '',
        password: '',
        confirm: '',
        grade: '',
        role: 'employee',
        department: '',
        designation: '',
        manager_id: '',
        city: '',
        gender: '',
      },
      formError: '',
    }
  },
  computed: {
    ...mapState(useAuthStore, ['loading', 'isAuthenticated', 'role']),
  },
  watch: {
    isAuthenticated(newValue) {
      if (newValue) {
        this.$router.replace(this.destinationRoute())
      }
    },
  },
  methods: {
    ...mapActions(useAuthStore, ['register']),
    async handleRegister() {
      this.formError = ''
      if (this.form.password !== this.form.confirm) {
        this.formError = 'Passwords do not match'
        return
      }

      try {
        const payload = { ...this.form }
        delete payload.confirm
        await this.register(payload)
        this.$router.replace(this.destinationRoute())
      } catch (error) {
        this.formError = error?.response?.data?.detail || 'Unable to register'
      }
    },
    destinationRoute() {
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

.auth-card {
  background: white;
  border-radius: 1.5rem;
  padding: 2.5rem;
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.12);
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

.auth-card__progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
  color: var(--slate-500);
}

.progress-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--slate-200);
}

.progress-dot.is-active {
  background: var(--primary-500);
  border-color: var(--primary-500);
}

.progress-line {
  flex: 1;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-500), rgba(37, 99, 235, 0.15));
}

.auth-hero {
  padding: 2rem;
  border-radius: 1.5rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.02), rgba(99, 102, 241, 0.08));
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

.auth-hero__feature-grid {
  margin-top: 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.auth-hero__feature-grid article {
  padding: 1.25rem;
  border-radius: 1rem;
  background: white;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 15px 40px rgba(15, 23, 42, 0.08);
}

.auth-hero__feature-grid h3 {
  margin: 0 0 0.35rem;
}

.auth-hero__feature-grid p {
  margin: 0;
  color: var(--slate-600);
}

.auth-hero__cta {
  margin-top: 1.5rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-radius: 999px;
  background: rgba(79, 70, 229, 0.1);
  color: var(--primary-700);
  font-weight: 600;
}

.auth-hero__cta a {
  color: inherit;
  text-decoration: underline;
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

input,
select {
  border-radius: 0.9rem;
  border: 1px solid var(--slate-200);
  padding: 0.85rem 1rem;
}

.auth-card__hint {
  margin: 0;
  color: var(--slate-500);
  font-size: 0.9rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.auth-card__error {
  background: var(--danger-100);
  color: var(--danger-500);
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  margin: 0;
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
}

.auth-card__footer {
  margin-top: 1.5rem;
  color: var(--slate-500);
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
