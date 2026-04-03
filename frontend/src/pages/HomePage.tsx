import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { listItineraries } from '../api/itineraries'
import ItineraryCard from '../components/ItineraryCard'
import type { Itinerary } from '../types'

export default function HomePage() {
  const { isAuthenticated, user } = useAuth()
  const [itineraries, setItineraries] = useState<Itinerary[]>([])

  useEffect(() => {
    if (isAuthenticated) {
      listItineraries().then(setItineraries).catch(() => {})
    }
  }, [isAuthenticated])

  return (
    <>
      <section className="hero fade-up">
        <div className="hero-main">
          <span className="hero-eyebrow">AI Travel Planning</span>
          <h2>
            {isAuthenticated && user ? `Welcome back, ${user.username}.` : <>Your next adventure,<br />perfectly planned.</>}
          </h2>
          <p>Tell us where you're headed. We'll craft a day-by-day itinerary with curated activities, dining, and local events — powered by AI.</p>
          <Link to="/itineraries/new" className="cta-button">Start planning</Link>
        </div>
        <div className="hero-aside">
          <p className="hero-aside-title">Explore styles</p>
          <ul>
            <li>Weekend city escapes</li>
            <li>Bucket-list tours</li>
            <li>Family adventures</li>
            <li>Work-from-anywhere</li>
            <li>Cultural deep dives</li>
          </ul>
        </div>
      </section>

      {isAuthenticated ? (
        <section>
          <div className="section-header">
            <h3 className="section-title">Your itineraries</h3>
            <div className="section-rule" />
            <Link to="/itineraries/new" className="btn-secondary">+ New trip</Link>
          </div>

          {itineraries.length > 0 ? (
            <div className="card-grid stagger">
              {itineraries.map((it) => (
                <ItineraryCard key={it.id} itinerary={it} />
              ))}
            </div>
          ) : (
            <div className="empty-state fade-up">
              <h3>No trips yet</h3>
              <p>Kick off your first journey — just enter a destination, your dates, and what you're into.</p>
              <Link className="cta-button" to="/itineraries/new">Create your first itinerary</Link>
            </div>
          )}
        </section>
      ) : (
        <section className="empty-state fade-up">
          <h3>Save &amp; manage your trips</h3>
          <p>Preview any itinerary without signing in. Create a free account to save, edit, and revisit your plans from anywhere.</p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link className="cta-button" to="/register">Create account</Link>
            <Link className="btn-secondary" to="/login">Sign in</Link>
          </div>
        </section>
      )}
    </>
  )
}
