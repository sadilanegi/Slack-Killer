/**
 * API service for communicating with backend
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('Adding token to request:', config.url, 'Token:', token.substring(0, 20) + '...')
  } else {
    console.warn('No token found for request:', config.url)
  }
  return config
})

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      error.message = 'Cannot connect to backend server. Please ensure the backend is running on http://localhost:8000'
    } else if (error.response) {
      // Server responded with error status
      if (error.response.status === 401) {
        error.message = 'Authentication required. Please log in.'
      } else if (error.response.status === 403) {
        error.message = 'You do not have permission to access this resource.'
      } else if (error.response.status === 404) {
        error.message = 'Resource not found.'
      } else {
        error.message = error.response.data?.detail || error.message || 'An error occurred'
      }
    }
    return Promise.reject(error)
  }
)

// API methods
export const apiService = {
  // Authentication
  login: async (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password || 'dev')
    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token)
    }
    return response
  },
  devLogin: async (email) => {
    const response = await api.post('/auth/dev-login', null, {
      params: { email }
    })
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token)
      console.log('Token stored:', response.data.access_token.substring(0, 20) + '...')
    } else {
      console.error('No access_token in response:', response.data)
    }
    return response
  },
  
  // Users
  getCurrentUser: () => api.get('/users/me'),
  getUser: (userId) => api.get(`/users/${userId}`),
  listUsers: (teamId = null) => {
    const params = teamId ? { team_id: teamId } : {}
    return api.get('/users/', { params })
  },

  // Metrics
  getUserMetrics: (userId, weeks = 8) => 
    api.get(`/metrics/users/${userId}`, { params: { weeks } }),
  getUserWeeklyMetrics: (userId, startDate = null, endDate = null) => {
    const params = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return api.get(`/metrics/users/${userId}/weekly`, { params })
  },

  // Reports
  getTeamSummary: (teamId, weekStart = null) => {
    const params = weekStart ? { week_start: weekStart } : {}
    return api.get(`/reports/teams/${teamId}/summary`, { params })
  },
  getWeeklyReport: (weekStart = null) => {
    const params = weekStart ? { week_start: weekStart } : {}
    return api.get('/reports/weekly', { params })
  },
  createOverride: (overrideData) => api.post('/reports/overrides', overrideData),
}

export default api

