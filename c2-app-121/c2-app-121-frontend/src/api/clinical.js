import { uploadFile } from './client'

export function generateSoapNote(file) {
  const fd = new FormData()
  fd.append('file', file)
  return uploadFile('/clinical/soap-note', fd)
}
