import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './DashboardLayout.css'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' },
  { path: '/patients', label: 'Bệnh nhân', icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2' },
  { path: '/encounters', label: 'Lượt khám', icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' },
]

export default function DashboardLayout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

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
            <a
              key={item.path}
              className={`nav-item${activePath.startsWith(item.path) ? ' active' : ''}`}
              href={item.path}
              onClick={e => { e.preventDefault(); navigate(item.path) }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d={item.icon} />
              </svg>
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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <path d="M16 17l5-5-5-5" />
              <path d="M21 12H9" />
            </svg>
            Đăng xuất
          </button>
        </div>
      </aside>

      <main className="dash-main">
        {children}
      </main>
    </div>
  )
}
