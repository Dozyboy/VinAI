import * as api from './client'

export function list(params = {}) {
  const q = new URLSearchParams(params).toString()
  return api.get(`/encounters/${q ? '?' + q : ''}`)
}

export function getById(id) {
  return api.get(`/encounters/${id}`)
}

export function create(body) {
  return api.post('/encounters/', body)
}

export function update(id, body) {
  return api.put(`/encounters/${id}`, body)
}

export function createSoapNote(id, body) {
  return api.post(`/encounters/${id}/soap-notes`, body)
}

export function updateSoapSubjective(encounterId, noteId, body) {
  return api.put(`/encounters/${encounterId}/soap-notes/${noteId}/subjective`, body)
}

export function updateSoapObjective(encounterId, noteId, body) {
  return api.put(`/encounters/${encounterId}/soap-notes/${noteId}/objective`, body)
}

export function updateSoapAssessment(encounterId, noteId, body) {
  return api.put(`/encounters/${encounterId}/soap-notes/${noteId}/assessment`, body)
}

export function updateSoapDiagnosis(encounterId, noteId, body) {
  return api.put(`/encounters/${encounterId}/soap-notes/${noteId}/diagnosis`, body)
}

export function updateSoapPlan(encounterId, noteId, body) {
  return api.put(`/encounters/${encounterId}/soap-notes/${noteId}/plan`, body)
}
