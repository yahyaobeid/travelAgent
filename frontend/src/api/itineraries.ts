import client from './client'
import type { Itinerary, ItineraryPreview, PendingItinerary, Event } from '../types'

export async function listItineraries(): Promise<Itinerary[]> {
  const { data } = await client.get<Itinerary[]>('/itineraries/')
  return data
}

export interface CreateItineraryInput {
  destination: string
  start_date: string
  end_date: string
  interests: string
  activities: string
  food_preferences: string
  preference: string
  action: 'preview' | 'save'
}

export async function createItinerary(input: CreateItineraryInput): Promise<Itinerary | ItineraryPreview> {
  const { data } = await client.post('/itineraries/create/', input)
  return data
}

export async function getPreview(): Promise<PendingItinerary> {
  const { data } = await client.get<PendingItinerary>('/itineraries/preview/')
  return data
}

export async function savePending(): Promise<Itinerary> {
  const { data } = await client.post<Itinerary>('/itineraries/save-pending/')
  return data
}

export async function getItinerary(pk: number): Promise<{ itinerary: Itinerary; events: Event[] }> {
  const { data } = await client.get<{ itinerary: Itinerary; events: Event[] }>(`/itineraries/${pk}/`)
  return data
}

export interface UpdateItineraryInput {
  destination?: string
  start_date?: string
  end_date?: string
  interests?: string
  activities?: string
  food_preferences?: string
  preference?: string
  generated_plan?: string
  regenerate_plan?: boolean
}

export async function updateItinerary(pk: number, input: UpdateItineraryInput): Promise<Itinerary> {
  const { data } = await client.put<Itinerary>(`/itineraries/${pk}/`, input)
  return data
}

export async function deleteItinerary(pk: number): Promise<void> {
  await client.delete(`/itineraries/${pk}/`)
}
