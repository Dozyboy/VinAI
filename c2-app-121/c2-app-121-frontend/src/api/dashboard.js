import * as api from './client'

export function getSummary() {
  return api.get('/dashboard/summary')
}

export function getDoctorWorkload() {
  return api.get('/dashboard/doctor-workload')
}

export function getTopDiagnoses() {
  return api.get('/dashboard/top-diagnoses')
}

export function getDailyView(date) {
  return api.get(`/dashboard/daily-view?date=${date}`)
}
