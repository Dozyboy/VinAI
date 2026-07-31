import * as api from './client'

export function list(params = {}) {
  const q = new URLSearchParams(params).toString()
  return api.get(`/shifts/${q ? '?' + q : ''}`)
}

export function updateStatus(id, body) {
  return api.patch(`/shifts/${id}`, body)
}
