import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const navRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 721px)')
    const handleResize = () => {
      if (mq.matches) setMenuOpen(false)
    }
    mq.addEventListener('change', handleResize)
    return () => mq.removeEventListener('change', handleResize)
  }, [])

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const closeMenu = () => setMenuOpen(false)

  return (
    <header>
      <div className="navbar">
        <div className="navbar-row">
          <Link className="brand" to="/" onClick={closeMenu}>
            <span className="brand-name">TripHelix</span>
            <span className="brand-tagline">AI Travel Planner</span>
          </Link>
          <button
            className="nav-toggle"
            type="button"
            aria-expanded={menuOpen}
            aria-controls="primary-nav"
            onClick={() => setMenuOpen((o) => !o)}
          >
            <span className="nav-toggle-icon" aria-hidden="true">{menuOpen ? '✕' : '☰'}</span>
            <span className="sr-only">Toggle navigation</span>
          </button>
        </div>
        <nav id="primary-nav" ref={navRef} className={`nav-links${menuOpen ? ' open' : ''}`}>
          <ul>
            <li className="nav-item"><Link to="/flights" onClick={closeMenu}>Flights</Link></li>
            <li className="nav-item"><Link to="/cars" onClick={closeMenu}>Car Rentals</Link></li>
            <li className="nav-item"><Link to="/hotels" onClick={closeMenu}>Hotels</Link></li>
            <li className="nav-divider" aria-hidden="true" />
            {isAuthenticated ? (
              <>
                <li className="nav-item"><Link to="/" onClick={closeMenu}>Dashboard</Link></li>
                <li className="nav-item"><Link to="/trips" onClick={closeMenu}>My Trips</Link></li>
                <li className="nav-item nav-item--cta"><Link to="/itineraries/new" onClick={closeMenu}>Plan a Trip</Link></li>
                <li className="nav-item">
                  <button type="button" id="logout-button" onClick={handleLogout}>Sign out</button>
                </li>
              </>
            ) : (
              <>
                <li className="nav-item"><Link to="/login" onClick={closeMenu}>Sign in</Link></li>
                <li className="nav-item nav-item--cta"><Link to="/register" onClick={closeMenu}>Get started</Link></li>
              </>
            )}
          </ul>
        </nav>
      </div>
    </header>
  )
}
