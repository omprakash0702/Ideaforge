'use client'

import { useState, useEffect } from 'react'
import { api, type User } from '@/lib/api'

const KEY = 'ideaforge_user'

export function useUser() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const raw = localStorage.getItem(KEY)
    if (raw) {
      try { setUser(JSON.parse(raw)) } catch { localStorage.removeItem(KEY) }
    }
    setLoading(false)
  }, [])

  async function login(name: string, email: string): Promise<User> {
    const created = await api.users.create({ name, email })
    localStorage.setItem(KEY, JSON.stringify(created))
    setUser(created)
    return created
  }

  function logout() {
    localStorage.removeItem(KEY)
    setUser(null)
  }

  return { user, loading, login, logout }
}
