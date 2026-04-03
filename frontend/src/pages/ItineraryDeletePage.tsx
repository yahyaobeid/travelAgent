import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { getItinerary, deleteItinerary } from '../api/itineraries'
import type { Itinerary } from '../types'

export default function ItineraryDeletePage() {
  const { pk } = useParams<{ pk: string }>()
  const navigate = useNavigate()
  const [itinerary, setItinerary] = useState<Itinerary | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!pk) return
    getItinerary(Number(pk))
      .then(({ itinerary }) => setItinerary(itinerary))
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [pk, navigate])

  const handleDelete = async () => {
    if (!pk) return
    setDeleting(true)
    await deleteItinerary(Number(pk))
    navigate('/')
  }

  if (loading) return <div className="loading-screen"><div className="compass-ring" /></div>
  if (!itinerary) return null

  return (
    <div className="form-page">
      <div className="form-card">
        <h1 className="form-title">Delete itinerary</h1>
        <p>Are you sure you want to delete <strong>{itinerary.destination}</strong>?</p>
        <p className="text-muted">This action cannot be undone.</p>
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-danger"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? 'Deleting…' : 'Yes, delete'}
          </button>
          <Link to={`/itineraries/${itinerary.id}`} className="btn btn-secondary">Cancel</Link>
        </div>
      </div>
    </div>
  )
}
