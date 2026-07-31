import * as api from './client'

export function list(params = {}) {
  const q = new URLSearchParams(params).toString()
  return api.get(`/patients/${q ? '?' + q : ''}`)
}

export function getById(id) {
  return api.get(`/patients/${id}`)
}

export function create(body) {
  return api.post('/patients/', body)
}

export function update(id, body) {
  return api.put(`/patients/${id}`, body)
}

export function getEncounters(id, params = {}) {
  const q = new URLSearchParams(params).toString()
  return api.get(`/patients/${id}/encounters${q ? '?' + q : ''}`)
}
