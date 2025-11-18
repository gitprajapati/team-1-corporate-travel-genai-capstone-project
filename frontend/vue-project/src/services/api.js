import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 25000,
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('travel_portal_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error?.response?.status === 401) {
      try {
        const { useAuthStore } = await import('../stores/auth')
        const auth = useAuthStore()
        auth.forceLogout?.()
      } catch (storeError) {
        console.error('Failed to clear auth store', storeError)
      }
    }
    return Promise.reject(error)
  },
)

export default api
