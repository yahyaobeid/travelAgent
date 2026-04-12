import client from './client'
import type { Trip } from '../types'

export async function getTrips(): Promise<Trip[]> {
  const { data } = await client.get<Trip[]>('/trips/')
  return data
}

export async function getTrip(id: number): Promise<Trip> {
  const { data } = await client.get<Trip>(`/trips/${id}/`)
  return data
}

export interface UpdateTripInput {
  title?: string
}

export async function updateTrip(id: number, input: UpdateTripInput): Promise<Trip> {
  const { data } = await client.patch<Trip>(`/trips/${id}/`, input)
  return data
}