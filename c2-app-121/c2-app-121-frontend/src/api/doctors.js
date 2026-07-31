import * as api from './client'

export function getById(id) {
  return api.get(`/doctors/${id}`)
}

export function getStats(id) {
  return api.get(`/doctors/${id}/stats`)
}
