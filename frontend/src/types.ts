export interface User {
  id: number
  username: string
}

export interface Itinerary {
  id: number
  destination: string
  start_date: string
  end_date: string
  interests: string
  activities: string
  food_preferences: string
  preference: string
  style_label: string
  generated_plan: string
  created_at: string
}

export interface Event {
  name: string
  url: string
  start_date?: string
  venue?: string
  image_url?: string
}

export interface ItineraryPreview {
  preview: boolean
  destination: string
  start_date: string
  end_date: string
  generated_plan: string
  events: Event[]
}

export interface PendingItinerary {
  destination: string
  start_date: string
  end_date: string
  interests: string
  activities: string
  food_preferences: string
  preference: string
  style_label: string
  generated_plan: string
  events: Event[]
}

export interface ChatMessage {
  role: 'user' | 'agent'
  text: string
  is_tool_call?: boolean
}

export interface CarSearchParams {
  location: string
  car_type: string
  max_price_per_day: number | null
  pickup_date: string | null
  dropoff_date: string | null
}

export interface CarListing {
  car_name: string
  car_type: string
  price_per_day: number
  price_display: string
  rental_company: string
  location: string
  availability: string
  listing_url: string
  source: string
}

export interface CarSearchResult {
  search_id: number | null
  search_params: CarSearchParams
  results: CarListing[]
  count: number
}

export type TravelStyle = 'general' | 'culture_history' | 'city_shopping' | 'adventure'

export const STYLE_CHOICES: Record<TravelStyle, string> = {
  general: 'No preference / Balanced',
  culture_history: 'Culture & History',
  city_shopping: 'City Life & Shopping',
  adventure: 'Adventure & Outdoors',
}
