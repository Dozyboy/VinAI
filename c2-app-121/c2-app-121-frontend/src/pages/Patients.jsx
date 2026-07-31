import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import * as patientsApi from '../api/patients'
import DashboardLayout from '../components/DashboardLayout'
import './ListPage.css'

const genders = { male: 'Nam', female: 'Nữ', other: 'Khác' }

export default function Patients() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ full_name: '', gender: 'male', phone: '', email: '', address: '', date_of_birth: '' })
  const [saving, setSaving] = useState(false)

  function load() {
    const params = { page, size: 20 }
    if (search) params.search = search
    patientsApi.list(params).then(res => {
      setItems(res.items || [])
      setTotal(res.total || 0)
    }).catch(() => {})
  }

  useEffect(() => { load() }, [page, search])

  async function handleCreate(e) {
    e.preventDefault()
    if (!form.full_name) return
    setSaving(true)
    try {
      const body = { full_name: form.full_name, gender: form.gender }
      if (form.phone) body.phone = form.phone
      if (form.email) body.email = form.email
      if (form.address) body.address = form.address
      if (form.date_of_birth) body.date_of_birth = form.date_of_birth
      const res = await patientsApi.create(body)
      setShowForm(false)
      setForm({ full_name: '', gender: 'male', phone: '', email: '', address: '', date_of_birth: '' })
      setSearch('')
      setPage(1)
      navigate(`/encounters/new?patient_id=${res.id}&patient_name=${encodeURIComponent(res.full_name)}`)
    } catch (err) { alert(err.message) }
    finally { setSaving(false) }
  }

  const pages = Math.max(1, Math.ceil(total / 20))

  return (
    <DashboardLayout>
      <header className="lp-header">
        <div>
          <h1>Bệnh nhân</h1>
          <p>{total} bệnh nhân</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(true)}>+ Thêm bệnh nhân</button>
      </header>

      <div className="lp-search">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input placeholder="Tìm kiếm bệnh nhân..." value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
      </div>

      <div className="lp-table-wrap">
        <table className="lp-table">
          <thead>
            <tr>
              <th>Họ tên</th>
              <th>Giới tính</th>
              <th>SĐT</th>
              <th>Email</th>
              <th>Số lượt khám</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map(p => (
              <tr key={p.id}>
                <td className="td-name">{p.full_name}</td>
                <td>{genders[p.gender] || p.gender}</td>
                <td>{p.phone || '—'}</td>
                <td>{p.email || '—'}</td>
                <td>{p.encounter_count ?? 0}</td>
                <td>
                  <button className="btn-ghost-sm" onClick={() => navigate(`/encounters/new?patient_id=${p.id}&patient_name=${encodeURIComponent(p.full_name)}`)}>Tạo lượt khám</button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={6} className="td-empty">Không tìm thấy bệnh nhân</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="lp-pages">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Trước</button>
          <span>Trang {page} / {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(p => p + 1)}>Sau</button>
        </div>
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Thêm bệnh nhân mới</h2>
              <button className="modal-close" onClick={() => setShowForm(false)}>&times;</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Họ tên <span className="req">*</span></label>
                  <input value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} required />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Giới tính</label>
                    <select value={form.gender} onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}>
                      <option value="male">Nam</option>
                      <option value="female">Nữ</option>
                      <option value="other">Khác</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Ngày sinh</label>
                    <input type="date" value={form.date_of_birth} onChange={e => setForm(f => ({ ...f, date_of_birth: e.target.value }))} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>SĐT</label>
                    <input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label>Email</label>
                    <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
                  </div>
                </div>
                <div className="form-group">
                  <label>Địa chỉ</label>
                  <input value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Hủy</button>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Đang lưu…' : 'Thêm & tạo lượt khám'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
