import client from './client'
import type { ChatMessage } from '../types'

export async function sendFlightChat(query: string): Promise<{ text: string; is_tool_call: boolean }> {
  const { data } = await client.post('/flights/chat/', { query })
  return data
}

export async function getFlightHistory(): Promise<{ display_history: ChatMessage[] }> {
  const { data } = await client.get('/flights/chat/')
  return data
}

export async function clearFlightHistory(): Promise<void> {
  await client.delete('/flights/chat/')
}
