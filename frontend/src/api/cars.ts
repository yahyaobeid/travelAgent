import client from './client'
import type { CarSearchResult, CarListing } from '../types'

export async function searchCars(query: string): Promise<CarSearchResult> {
  const { data } = await client.post<CarSearchResult>('/cars/search/', { query })
  return data
}

export interface CarDetailResponse {
  search: {
    id: number
    natural_query: string
    location: string
    car_type: string
    max_price_per_day: string | null
    pickup_date: string | null
    dropoff_date: string | null
  }
  results: CarListing[]
}

export async function getCarSearch(pk: number): Promise<CarDetailResponse> {
  const { data } = await client.get<CarDetailResponse>(`/cars/${pk}/`)
  return data
}
