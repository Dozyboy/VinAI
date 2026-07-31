const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const BASE = `${API_BASE_URL}/api/v1`

function getToken() {
  try { return localStorage.getItem('access_token') } catch { return null }
}

async function request(path, options = {}) {
  const token = getToken()
  const { headers: extraHeaders, ...fetchOpts } = options
  const headers = { 'Content-Type': 'application/json', ...extraHeaders }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...fetchOpts, headers })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const msg = Array.isArray(data?.detail)
      ? data.detail.map(d => d.msg || d.message).join('; ')
      : data?.detail || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}

export function get(path, extra = {}) {
  return request(path, { method: 'GET', ...extra })
}

export function post(path, body, extra = {}) {
  return request(path, { method: 'POST', body: JSON.stringify(body), ...extra })
}

export function put(path, body, extra = {}) {
  return request(path, { method: 'PUT', body: JSON.stringify(body), ...extra })
}

export function patch(path, body, extra = {}) {
  return request(path, { method: 'PATCH', body: JSON.stringify(body), ...extra })
}

export function uploadFile(path, formData) {
  const token = getToken()
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  return fetch(`${BASE}${path}`, {
    method: 'POST',
    headers,
    body: formData,
  }).then(async res => {
    const data = await res.json().catch(() => null)
    if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`)
    return data
  })
}
