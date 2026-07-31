import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import * as encountersApi from '../api/encounters'
import DashboardLayout from '../components/DashboardLayout'
import './NewEncounter.css'

export default function NewEncounter() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()

  const [patientName] = useState(params.get('patient_name') || '')
  const [patientId] = useState(params.get('patient_id') || '')
  const [encounterDate, setEncounterDate] = useState(new Date().toISOString().slice(0, 16))
  const [chiefComplaint, setChiefComplaint] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!patientId || !encounterDate) return
    setSaving(true)
    try {
      const res = await encountersApi.create({
        doctor_id: user.id,
        patient_id: Number(patientId),
        encounter_date: encounterDate,
        chief_complaint: chiefComplaint || undefined,
      })
      navigate(`/encounters/${res.id}`)
    } catch (err) { alert(err.message) }
    finally { setSaving(false) }
  }

  return (
    <DashboardLayout>
      <div className="ne-wrap">
        <div className="ne-card">
          <h1>Tạo lượt khám mới</h1>

          <div className="ne-patient">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <div>
              <div className="ne-patient-label">Bệnh nhân</div>
              <div className="ne-patient-name">{patientName}</div>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Ngày & giờ khám</label>
              <input type="datetime-local" value={encounterDate} onChange={e => setEncounterDate(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Lý do khám (chief complaint)</label>
              <textarea rows={3} value={chiefComplaint} onChange={e => setChiefComplaint(e.target.value)} placeholder="Ví dụ: Đau đầu, sốt, ho..." />
            </div>
            <div className="ne-actions">
              <button type="button" className="btn-secondary" onClick={() => navigate('/patients')}>Hủy</button>
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? 'Đang tạo…' : 'Bắt đầu lượt khám'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  )
}
