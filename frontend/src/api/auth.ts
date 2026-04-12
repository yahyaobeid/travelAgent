import client from './client'
import type { User } from '../types'

export async function login(username: string, password: string): Promise<User> {
  const { data } = await client.post<User>('/auth/login/', { username, password })
  return data
}

export async function register(username: string, password1: string, password2: string): Promise<User> {
  const { data } = await client.post<User>('/auth/register/', { username, password1, password2 })
  return data
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout/')
}

export async function getMe(): Promise<User> {
  const { data } = await client.get<User>('/auth/me/')
  return data
}

export async function getCsrf(): Promise<void> {
  await client.get('/csrf/')
}
