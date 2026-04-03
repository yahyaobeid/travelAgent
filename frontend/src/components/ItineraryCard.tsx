import { Link } from 'react-router-dom'
import type { Itinerary } from '../types'

interface ItineraryCardProps {
  itinerary: Itinerary
}

export default function ItineraryCard({ itinerary }: ItineraryCardProps) {
  const excerpt = itinerary.generated_plan.slice(0, 180).replace(/[#*_`]/g, '').trim()

  return (
    <article className="itinerary-card">
      <div className="itinerary-card-header">
        <h2 className="itinerary-card-title">
          <Link to={`/itineraries/${itinerary.id}`}>{itinerary.destination}</Link>
        </h2>
        <span className="style-badge">{itinerary.style_label}</span>
      </div>
      <p className="itinerary-card-dates">
        {itinerary.start_date} – {itinerary.end_date}
      </p>
      {excerpt && <p className="itinerary-card-excerpt">{excerpt}…</p>}
      <div className="itinerary-card-actions">
        <Link to={`/itineraries/${itinerary.id}`} className="btn btn-ghost btn-sm">View</Link>
        <Link to={`/itineraries/${itinerary.id}/edit`} className="btn btn-ghost btn-sm">Edit</Link>
        <Link to={`/itineraries/${itinerary.id}/delete`} className="btn btn-ghost btn-sm btn-danger">Delete</Link>
      </div>
    </article>
  )
}
