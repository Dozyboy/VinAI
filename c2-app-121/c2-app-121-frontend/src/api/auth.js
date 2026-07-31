import * as api from './client'

export function login(email, password) {
  return api.post('/auth/login', { email, password })
}

export function register(email, password, fullName) {
  return api.post('/auth/register', { email, password, full_name: fullName })
}

export function refresh(refreshToken) {
  return api.post('/auth/refresh', { refresh_token: refreshToken })
}

export function getMe(token) {
  return api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
}
