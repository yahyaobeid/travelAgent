import React, { createContext, useEffect, useState } from 'react'
import { getCsrf, getMe, login as apiLogin, logout as apiLogout, register as apiRegister } from '../api/auth'
import type { User } from '../types'

export interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password1: string, password2: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    getCsrf()
      .then(() => getMe())
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  const login = async (username: string, password: string) => {
    const u = await apiLogin(username, password)
    setUser(u)
  }

  const register = async (username: string, password1: string, password2: string) => {
    const u = await apiRegister(username, password1, password2)
    setUser(u)
  }

  const logout = async () => {
    await apiLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
