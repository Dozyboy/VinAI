import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import * as dashApi from '../api/dashboard'
import * as encountersApi from '../api/encounters'
import './Dashboard.css'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' },
  { path: '/patients', label: 'Bệnh nhân', icon: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2' },
  { path: '/encounters', label: 'Lượt khám', icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' },
]

const shiftStatusLabels = { scheduled: 'Chưa bắt đầu', in_progress: 'Đang diễn ra', completed: 'Hoàn thành', cancelled: 'Đã hủy' }
const shiftStatusColors = { scheduled: '#6366f1', in_progress: '#d97706', completed: '#059669', cancelled: '#94a3b8' }
const encounterStatusLabels = { in_progress: 'Đang khám', completed: 'Hoàn thành', cancelled: 'Đã hủy' }
const encounterStatusColors = { in_progress: '#d97706', completed: '#059669', cancelled: '#94a3b8' }

const MONTHS_VN = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6', 'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12']
const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function formatDateDisplay(d) {
  const parts = d.split('-')
  return `${parts[2]}/${parts[1]}/${parts[0]}`
}

function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfMonth(year, month) {
  const day = new Date(year, month, 1).getDay()
  return day === 0 ? 6 : day - 1
}

function dateToStr(y, m, d) {
  return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

function CalendarPicker({ selected, onSelect, onClose }) {
  const today = new Date()
  const [viewYear, setViewYear] = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth())
  const ref = useRef(null)

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose()
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [onClose])

  const daysInMonth = getDaysInMonth(viewYear, viewMonth)
  const firstDay = getFirstDayOfMonth(viewYear, viewMonth)
  const cells = []
  for (let i = 0; i < firstDay; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)

  function prevMonth() {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1) }
    else setViewMonth(m => m - 1)
  }

  function nextMonth() {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1) }
    else setViewMonth(m => m + 1)
  }

  function goToday() {
    setViewYear(today.getFullYear())
    setViewMonth(today.getMonth())
    onSelect(todayStr())
    onClose()
  }

  return (
    <div className="cal-popup" ref={ref}>
      <div className="cal-header">
        <button className="cal-nav" onClick={prevMonth}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <span className="cal-title">{MONTHS_VN[viewMonth]} {viewYear}</span>
        <button className="cal-nav" onClick={nextMonth}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
      <div className="cal-weekdays">
        {WEEKDAYS.map(w => <div key={w} className="cal-wd">{w}</div>)}
      </div>
      <div className="cal-grid">
        {cells.map((d, i) => {
          if (d === null) return <div key={`e${i}`} className="cal-cell empty" />
          const ds = dateToStr(viewYear, viewMonth, d)
          const isToday = ds === todayStr()
          const isSelected = ds === selected
          return (
            <button
              key={ds}
              className={`cal-cell${isToday ? ' today' : ''}${isSelected ? ' selected' : ''}`}
              onClick={() => { onSelect(ds); onClose() }}
            >
              {d}
            </button>
          )
        })}
      </div>
      <div className="cal-footer">
        <button className="cal-today-btn" onClick={goToday}>Hôm nay</button>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [stats, setStats] = useState(null)
  const [selectedDate, setSelectedDate] = useState(todayStr())
  const [dailyData, setDailyData] = useState(null)
  const [loadingDaily, setLoadingDaily] = useState(false)
  const [showCalendar, setShowCalendar] = useState(false)

  useEffect(() => {
    dashApi.getSummary().then(setStats).catch(() => {})
  }, [])

  const loadDaily = useCallback(() => {
    setLoadingDaily(true)
    dashApi.getDailyView(selectedDate)
      .then(setDailyData)
      .catch(() => setDailyData({ date: selectedDate, shifts: [], unassigned_encounters: [] }))
      .finally(() => setLoadingDaily(false))
  }, [selectedDate])

  useEffect(() => { loadDaily() }, [loadDaily])

  if (!user) return null

  const initials = user.full_name
    ? user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : user.email[0].toUpperCase()

  const activePath = location.pathname

  return (
    <div className="dash-layout">
      <aside className="dash-sidebar">
        <div className="sidebar-brand">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#2563eb" />
            <path d="M16 8v16M8 16h16" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
          <span>Ambient Scribe</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <a key={item.path} className={`nav-item${activePath === item.path ? ' active' : ''}`} href={item.path} onClick={e => { e.preventDefault(); navigate(item.path) }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={item.icon}/></svg>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="user-avatar">{initials}</div>
            <div className="user-info">
              <div className="user-name">{user.full_name}</div>
              <div className="user-role">{user.role === 'doctor' ? 'Bác sĩ' : 'Người dùng'}</div>
            </div>
          </div>
          <button className="btn-logout" onClick={() => { logout(); navigate('/', { replace: true }) }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Đăng xuất
          </button>
        </div>
      </aside>

      <main className="dash-main">
        <header className="dash-header">
          <h1>Xin chào, {user.full_name?.split(' ').pop() || 'Bác sĩ'}</h1>
          <p>Đây là tổng quan hoạt động ghi chú lâm sàng của bạn</p>
        </header>

        <div className="dash-stats">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#dbeafe' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            </div>
            <div className="stat-body">
              <div className="stat-value">{stats?.total_encounters ?? 0}</div>
              <div className="stat-label">Tổng lượt khám</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#fef3c7' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
            </div>
            <div className="stat-body">
              <div className="stat-value">{stats?.today_encounters ?? 0}</div>
              <div className="stat-label">Hôm nay</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#d1fae5' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <div className="stat-body">
              <div className="stat-value">{stats?.completed_encounters ?? 0}</div>
              <div className="stat-label">Đã hoàn thành</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#ede9fe' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            </div>
            <div className="stat-body">
              <div className="stat-value">{stats?.in_progress_encounters ?? 0}</div>
              <div className="stat-label">Đang khám</div>
            </div>
          </div>
        </div>

        <div className="daily-section">
          <div className="daily-header">
            <h2>Lịch làm việc theo ngày</h2>
            <div className="daily-header-right">
              <div className="daily-date-picker">
                <div className="date-display" onClick={() => setShowCalendar(v => !v)}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                  <span className="date-value">{formatDateDisplay(selectedDate)}</span>
                  <span className="date-weekday">{['CN','T2','T3','T4','T5','T6','T7'][new Date(selectedDate+'T00:00:00').getDay()]}</span>
                  {selectedDate === todayStr() && <span className="date-today">Hôm nay</span>}
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
                </div>
                {showCalendar && (
                  <CalendarPicker
                    selected={selectedDate}
                    onSelect={setSelectedDate}
                    onClose={() => setShowCalendar(false)}
                  />
                )}
              </div>
            </div>
          </div>

          {loadingDaily ? (
            <div className="daily-loading">Đang tải dữ liệu...</div>
          ) : (
            <div className="daily-content">
              {dailyData?.shifts?.length === 0 && dailyData?.unassigned_encounters?.length === 0 && (
                <div className="daily-empty">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                  <p>Không có ca làm việc nào trong ngày này</p>
                </div>
              )}

              {dailyData?.shifts?.map(shift => (
                <div key={shift.id} className="shift-card">
                  <div className="shift-header">
                    <div className="shift-info">
                      <div className="shift-time-badge">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        {shift.start_time} - {shift.end_time}
                      </div>
                      <div className="shift-doctor">
                        <div className="shift-doctor-avatar">{shift.doctor_name?.charAt(0) || '?'}</div>
                        <div>
                          <div className="shift-doctor-name">{shift.doctor_name}</div>
                          <div className="shift-doctor-spec">{shift.specialization}</div>
                        </div>
                      </div>
                    </div>
                    <div className="shift-right">
                      <span className="shift-status" style={{ background: (shiftStatusColors[shift.status] || '#94a3b8') + '18', color: shiftStatusColors[shift.status] || '#94a3b8' }}>
                        {shiftStatusLabels[shift.status] || shift.status}
                      </span>
                    </div>
                  </div>

                  {shift.encounters?.length > 0 ? (
                    <div className="shift-patients">
                      {shift.encounters.map(enc => (
                        <div key={enc.id} className="patient-row" onClick={() => navigate(`/encounters/${enc.id}`)}>
                          <div className="patient-row-avatar">{enc.patient_name?.charAt(0) || '?'}</div>
                          <div className="patient-row-info">
                            <div className="patient-row-name">{enc.patient_name}</div>
                            <div className="patient-row-complaint">{enc.chief_complaint || 'Không có lý do khám'}</div>
                          </div>
                          <span className="patient-row-status" style={{ background: (encounterStatusColors[enc.status] || '#94a3b8') + '18', color: encounterStatusColors[enc.status] || '#94a3b8' }}>
                            {encounterStatusLabels[enc.status] || enc.status}
                          </span>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="shift-empty">
                      <p>Chưa có bệnh nhân trong ca này</p>
                    </div>
                  )}
                </div>
              ))}

              {dailyData?.unassigned_encounters?.length > 0 && (
                <div className="shift-card unassigned">
                  <div className="shift-header">
                    <div className="shift-info">
                      <div className="shift-time-badge unassigned">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                        Chưa phân ca
                      </div>
                    </div>
                  </div>
                  <div className="shift-patients">
                    {dailyData.unassigned_encounters.map(enc => (
                      <div key={enc.id} className="patient-row" onClick={() => navigate(`/encounters/${enc.id}`)}>
                        <div className="patient-row-avatar">{enc.patient_name?.charAt(0) || '?'}</div>
                        <div className="patient-row-info">
                          <div className="patient-row-name">{enc.patient_name}</div>
                          <div className="patient-row-complaint">{enc.chief_complaint || 'Không có lý do khám'}</div>
                        </div>
                        <span className="patient-row-status" style={{ background: (encounterStatusColors[enc.status] || '#94a3b8') + '18', color: encounterStatusColors[enc.status] || '#94a3b8' }}>
                          {encounterStatusLabels[enc.status] || enc.status}
                        </span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

      </main>
    </div>
  )
}
