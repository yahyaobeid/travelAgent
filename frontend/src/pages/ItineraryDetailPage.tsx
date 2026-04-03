import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { getItinerary } from '../api/itineraries'
import MarkdownRenderer from '../components/MarkdownRenderer'
import EventsSection from '../components/EventCard'
import type { Itinerary, Event } from '../types'

export default function ItineraryDetailPage() {
  const { pk } = useParams<{ pk: string }>()
  const navigate = useNavigate()
  const [itinerary, setItinerary] = useState<Itinerary | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!pk) return
    getItinerary(Number(pk))
      .then(({ itinerary, events }) => {
        setItinerary(itinerary)
        setEvents(events)
      })
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [pk, navigate])

  if (loading) return <div className="loading-screen"><div className="compass-ring" /></div>
  if (!itinerary) return null

  return (
    <div className="detail-page">
      <div className="detail-header">
        <div>
          <span className="style-badge">{itinerary.style_label}</span>
          <h1 className="detail-title">{itinerary.destination}</h1>
          <p className="detail-dates">{itinerary.start_date} – {itinerary.end_date}</p>
        </div>
        <div className="detail-actions">
          <Link to={`/itineraries/${itinerary.id}/edit`} className="btn btn-secondary">Edit</Link>
          <Link to={`/itineraries/${itinerary.id}/delete`} className="btn btn-danger">Delete</Link>
          <Link to="/itineraries/new" className="btn btn-ghost">Plan another</Link>
        </div>
      </div>

      <div className="detail-body">
        <div className="detail-plan">
          <MarkdownRenderer content={itinerary.generated_plan} />
        </div>
      </div>

      <EventsSection events={events} />
    </div>
  )
}
