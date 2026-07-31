import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import * as authApi from '../api/auth'

const AuthContext = createContext(null)

function getStored() {
  try {
    const a = localStorage.getItem('access_token')
    const r = localStorage.getItem('refresh_token')
    const u = localStorage.getItem('user')
    return { accessToken: a, refreshToken: r, user: u ? JSON.parse(u) : null }
  } catch {
    return { accessToken: null, refreshToken: null, user: null }
  }
}

function store(accessToken, refreshToken, user) {
  if (accessToken) localStorage.setItem('access_token', accessToken)
  if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
  if (user) localStorage.setItem('user', JSON.stringify(user))
}

function clearStore() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStored().user)
  const [accessToken, setAccessToken] = useState(() => getStored().accessToken)
  const [refreshToken, setRefreshToken] = useState(() => getStored().refreshToken)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (accessToken) {
      authApi.getMe(accessToken)
        .then(u => { setUser(u); store(accessToken, refreshToken, u) })
        .catch(() => logout())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password)
    const me = await authApi.getMe(data.access_token)
    setAccessToken(data.access_token)
    setRefreshToken(data.refresh_token)
    setUser(me)
    store(data.access_token, data.refresh_token, me)
    return me
  }, [])

  const logout = useCallback(() => {
    setUser(null)
    setAccessToken(null)
    setRefreshToken(null)
    clearStore()
  }, [])

  return (
    <AuthContext.Provider value={{ user, accessToken, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
