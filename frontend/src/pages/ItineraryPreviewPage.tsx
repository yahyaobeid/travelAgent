import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getPreview, savePending } from '../api/itineraries'
import MarkdownRenderer from '../components/MarkdownRenderer'
import EventsSection from '../components/EventCard'
import LoadingOverlay from '../components/LoadingOverlay'
import type { PendingItinerary } from '../types'

export default function ItineraryPreviewPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [preview, setPreview] = useState<PendingItinerary | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getPreview()
      .then(setPreview)
      .catch(() => navigate('/itineraries/new'))
      .finally(() => setLoading(false))
  }, [navigate])

  const handleSave = async () => {
    setSaving(true)
    try {
      const saved = await savePending()
      navigate(`/itineraries/${saved.id}`)
    } catch {
      setError('Failed to save itinerary. Please try again.')
      setSaving(false)
    }
  }

  if (loading) return <div className="loading-screen"><div className="compass-ring" /></div>
  if (saving) return <LoadingOverlay message="Saving your itinerary…" />
  if (!preview) return null

  return (
    <div className="detail-page">
      <div className="detail-header">
        <div>
          <span className="style-badge">{preview.style_label}</span>
          <h1 className="detail-title">{preview.destination}</h1>
          <p className="detail-dates">{preview.start_date} – {preview.end_date}</p>
        </div>
        <div className="detail-actions">
          {isAuthenticated ? (
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              Save to my trips
            </button>
          ) : (
            <Link
              to={`/login?next=/itineraries/save-redirect`}
              className="btn btn-primary"
            >
              Sign in to save
            </Link>
          )}
          <Link to="/itineraries/new" className="btn btn-secondary">Plan another</Link>
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="detail-body">
        <div className="detail-plan">
          <MarkdownRenderer content={preview.generated_plan} />
        </div>
      </div>

      <EventsSection events={preview.events} />
    </div>
  )
}
