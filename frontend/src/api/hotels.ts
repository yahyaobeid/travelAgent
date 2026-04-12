import axios from 'axios'
import Cookies from 'js-cookie'
import type { HotelSearchResult } from '../types'

// Create a separate client for hotels since the endpoint is at /api/hotels/search/
// instead of /api/v1/hotels/search/
const hotelClient = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// Attach CSRF token to every mutating request
hotelClient.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase() ?? ''
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = Cookies.get('csrftoken')
    if (csrf) {
      config.headers['X-CSRFToken'] = csrf
    }
  }
  return config
})

export async function searchHotels(naturalQuery: string): Promise<HotelSearchResult> {
  const { data } = await hotelClient.post<HotelSearchResult>('/hotels/search/', {
    natural_query: naturalQuery
  })
  return data
}