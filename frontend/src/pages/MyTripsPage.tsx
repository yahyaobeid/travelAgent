import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getTrips } from '../api/trips'
import { STYLE_CHOICES } from '../types'
import type { Trip } from '../types'

export default function MyTripsPage() {
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getTrips()
      .then(setTrips)
      .catch(() => setError('Failed to load trips'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="compass-ring" />
      </div>
    )
  }

  const formatDateRange = (startDate: string, endDate: string) => {
    const start = new Date(startDate).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
    const end = new Date(endDate).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
    return `${start} – ${end}`
  }

  const getStyleLabel = (preference: string) => {
    return STYLE_CHOICES[preference as keyof typeof STYLE_CHOICES] || 'Balanced'
  }

  return (
    <div className="form-page">
      <div className="trips-container">
        <h1 className="page-title">My Trips</h1>

        {error && <div className="form-error">{error}</div>}

        {trips.length === 0 ? (
          <div className="empty-state">
            <p>No trips yet. Start planning!</p>
            <Link to="/itineraries/new" className="btn btn-primary">
              Plan Your First Trip
            </Link>
          </div>
        ) : (
          <div className="trips-grid">
            {trips.map((trip) => (
              <Link
                key={trip.id}
                to={`/trips/${trip.id}`}
                className="trip-card"
              >
                <div className="trip-card-header">
                  <span className="style-badge">
                    {getStyleLabel(trip.itinerary.preference)}
                  </span>
                  <div className="module-badges">
                    {trip.flight_search && <span className="module-badge">✈️</span>}
                    {trip.hotel_search && <span className="module-badge">🏨</span>}
                    {trip.car_rental_search && <span className="module-badge">🚗</span>}
                  </div>
                </div>
                <h2 className="trip-title">
                  {trip.itinerary.destination || trip.title}
                </h2>
                <p className="trip-dates">
                  {formatDateRange(trip.itinerary.start_date, trip.itinerary.end_date)}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}