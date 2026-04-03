import axios from 'axios'
import Cookies from 'js-cookie'

const client = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// Attach CSRF token to every mutating request
client.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase() ?? ''
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = Cookies.get('csrftoken')
    if (csrf) {
      config.headers['X-CSRFToken'] = csrf
    }
  }
  return config
})

export default client
