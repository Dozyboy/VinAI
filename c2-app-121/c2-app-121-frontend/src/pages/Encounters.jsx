import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as encountersApi from '../api/encounters'
import DashboardLayout from '../components/DashboardLayout'
import './ListPage.css'

const statusLabels = { in_progress: 'Đang khám', completed: 'Hoàn thành', cancelled: 'Đã hủy' }
const statusColors = { in_progress: '#d97706', completed: '#059669', cancelled: '#94a3b8' }

export default function Encounters() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filter, setFilter] = useState('')

  function load() {
    const params = { page, size: 20 }
    if (filter) params.status = filter
    encountersApi.list(params).then(res => {
      setItems(res.items || [])
      setTotal(res.total || 0)
    }).catch(() => {})
  }

  useEffect(() => { load() }, [page, filter])

  const pages = Math.max(1, Math.ceil(total / 20))

  return (
    <DashboardLayout>
      <header className="lp-header">
        <div>
          <h1>Lượt khám</h1>
          <p>{total} lượt</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/patients')}>+ Tạo lượt khám</button>
      </header>

      <div className="lp-tabs">
        {['', 'in_progress', 'completed', 'cancelled'].map(s => (
          <button key={s} className={`lp-tab${filter === s ? ' active' : ''}`} onClick={() => { setFilter(s); setPage(1) }}>
            {s ? statusLabels[s] : 'Tất cả'}
          </button>
        ))}
      </div>

      <div className="lp-table-wrap">
        <table className="lp-table">
          <thead>
            <tr>
              <th>Bệnh nhân</th>
              <th>Bác sĩ</th>
              <th>Ngày khám</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map(e => (
              <tr key={e.id}>
                <td className="td-name">{e.patient_name}</td>
                <td>{e.doctor_name}</td>
                <td>{e.encounter_date}</td>
                <td>
                  <span className="status-badge" style={{ background: statusColors[e.status] + '18', color: statusColors[e.status] }}>
                    {statusLabels[e.status] || e.status}
                  </span>
                </td>
                <td>
                  <button className="btn-ghost-sm" onClick={() => navigate(`/encounters/${e.id}`)}>
                    {e.status === 'in_progress' ? 'Khám' : 'Xem'}
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={5} className="td-empty">Không có lượt khám nào</td></tr>
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
    </DashboardLayout>
  )
}
