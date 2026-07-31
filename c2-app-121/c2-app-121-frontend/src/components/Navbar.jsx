import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#2563eb" />
            <path d="M16 8v16M8 16h16" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
          <span className="brand-text">Ambient Scribe</span>
        </Link>

        <div className="navbar-links">
          {user ? (
            <>
              <Link to="/dashboard" className="btn btn-ghost">Dashboard</Link>
              <button className="btn btn-primary" onClick={handleLogout}>Đăng xuất</button>
            </>
          ) : (
            <Link to="/login" className="btn btn-primary">Đăng nhập</Link>
          )}
        </div>
      </div>
    </nav>
  )
}
