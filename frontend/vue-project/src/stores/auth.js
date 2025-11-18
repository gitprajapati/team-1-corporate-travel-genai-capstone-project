import { defineStore } from 'pinia'
import api from '../services/api'

const TOKEN_KEY = 'travel_portal_token'
const USER_KEY = 'travel_portal_user'
const EXP_KEY = 'travel_portal_exp'

function computeExpiry(expiresInSeconds) {
  const defaultSeconds = expiresInSeconds || 3600
  return Math.floor(Date.now() / 1000) + defaultSeconds
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
    expiresAt: Number(localStorage.getItem(EXP_KEY)) || null,
    loading: false,
    error: null,
  }),
  getters: {
    isAuthenticated(state) {
      if (!state.token) return false
      if (!state.expiresAt) return true
      return state.expiresAt * 1000 > Date.now()
    },
    role(state) {
      return state.user?.role || null
    },
    employeeName(state) {
      return state.user?.name || state.user?.employee_id || 'Traveler'
    },
  },
  actions: {
    persistSession(payload) {
      this.token = payload.token
      this.expiresAt = payload.expires_at || computeExpiry(payload.expires_in)
      this.user = {
        employee_id: payload.employee_id,
        role: payload.role,
        name: payload.name,
      }
      localStorage.setItem(TOKEN_KEY, this.token)
      localStorage.setItem(EXP_KEY, String(this.expiresAt))
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
    },
    async login({ identifier, password }) {
      this.loading = true
      this.error = null
      try {
        const payload = new URLSearchParams()
        payload.append('username', identifier)
        payload.append('password', password)

        const { data } = await api.post('/auth/token', payload)
        data.token = data.access_token
        if (!data.expires_at) {
          data.expires_at = computeExpiry(data.expires_in)
        }
        this.persistSession(data)
        await this.fetchProfile()
        return data
      } catch (error) {
        this.error = error?.response?.data?.detail || 'Unable to login. Check credentials.'
        throw error
      } finally {
        this.loading = false
      }
    },
    async register(payload) {
      this.loading = true
      this.error = null
      try {
        const { data } = await api.post('/auth/register', payload)
        data.token = data.access_token
        if (!data.expires_at) {
          data.expires_at = computeExpiry(data.expires_in)
        }
        this.persistSession(data)
        await this.fetchProfile()
        return data
      } catch (error) {
        this.error = error?.response?.data?.detail || 'Registration failed'
        throw error
      } finally {
        this.loading = false
      }
    },
    async fetchProfile() {
      if (!this.token) return
      try {
        const { data } = await api.get('/auth/me')
        this.user = { ...this.user, ...data }
        localStorage.setItem(USER_KEY, JSON.stringify(this.user))
        return data
      } catch (error) {
        console.warn('Unable to fetch profile', error)
        return null
      }
    },
    async logout() {
      try {
        if (this.token) {
          await api.post('/auth/logout')
        }
      } catch (error) {
        console.warn('Logout request failed', error)
      } finally {
        this.forceLogout()
      }
    },
    forceLogout() {
      this.token = ''
      this.user = null
      this.expiresAt = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      localStorage.removeItem(EXP_KEY)
    },
  },
})
