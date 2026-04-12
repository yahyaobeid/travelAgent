import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getTrip, updateTrip } from '../api/trips'
import MarkdownRenderer from '../components/MarkdownRenderer'
import type { Trip } from '../types'

interface DaySection {
  dayNumber: number
  title: string
  content: string
}

export default function TripDashboardPage() {
  const { id } = useParams<{ id: string }>()

  const [trip, setTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleValue, setTitleValue] = useState('')
  const [dayStates, setDayStates] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!id) return

    getTrip(Number(id))
      .then((tripData) => {
        setTrip(tripData)
        setTitleValue(tripData.title)
        // Default to first day expanded, rest collapsed
        const days = parseDaySections(tripData.itinerary.generated_plan)
        const initialStates: Record<number, boolean> = {}
        days.forEach((day, index) => {
          initialStates[day.dayNumber] = index === 0 // First day expanded
        })
        setDayStates(initialStates)
      })
      .catch(() => setError('Trip not found'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="compass-ring" />
      </div>
    )
  }

  if (error || !trip) {
    return (
      <div className="form-page">
        <div className="form-card" style={{ textAlign: 'center' }}>
          <h1>Trip not found</h1>
          <p>The trip you're looking for doesn't exist or you don't have access to it.</p>
          <Link to="/trips" className="btn btn-primary">Back to My Trips</Link>
        </div>
      </div>
    )
  }

  const parseDaySections = (generatedPlan: string): DaySection[] => {
    const dayRegex = /^#{1,2}\s*Day\s+(\d+)/gim
    const sections: DaySection[] = []

    const matches = [...generatedPlan.matchAll(dayRegex)]

    for (let i = 0; i < matches.length; i++) {
      const match = matches[i]
      const dayNumber = parseInt(match[1])
      const startIndex = match.index!
      const endIndex = i < matches.length - 1 ? matches[i + 1].index! : generatedPlan.length

      const fullContent = generatedPlan.substring(startIndex, endIndex).trim()
      const lines = fullContent.split('\n')
      const title = lines.length > 1 ? lines[1].trim() : `Day ${dayNumber}`

      sections.push({
        dayNumber,
        title: title.substring(0, 50) + (title.length > 50 ? '...' : ''),
        content: fullContent
      })
    }

    return sections
  }

  const handleTitleSave = async () => {
    if (titleValue.trim() === trip.title) {
      setEditingTitle(false)
      return
    }

    try {
      const updatedTrip = await updateTrip(trip.id, { title: titleValue.trim() })
      setTrip(updatedTrip)
      setEditingTitle(false)
    } catch {
      setError('Failed to update trip title')
      setTitleValue(trip.title) // Reset to original
      setEditingTitle(false)
    }
  }

  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleTitleSave()
    } else if (e.key === 'Escape') {
      setTitleValue(trip.title)
      setEditingTitle(false)
    }
  }

  const toggleDay = (dayNumber: number) => {
    setDayStates(prev => ({
      ...prev,
      [dayNumber]: !prev[dayNumber]
    }))
  }

  const formatDateRange = (startDate: string, endDate: string) => {
    const start = new Date(startDate).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
    const end = new Date(endDate).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
    return `${start} – ${end}`
  }

  const daySections = parseDaySections(trip.itinerary.generated_plan)

  return (
    <div className="detail-page">
      {/* Header */}
      <div className="detail-header">
        <div>
          {editingTitle ? (
            <input
              type="text"
              value={titleValue}
              onChange={(e) => setTitleValue(e.target.value)}
              onBlur={handleTitleSave}
              onKeyDown={handleTitleKeyDown}
              className="trip-title-input"
              autoFocus
            />
          ) : (
            <h1
              className="detail-title trip-title-editable"
              onClick={() => setEditingTitle(true)}
              title="Click to edit"
            >
              {trip.title}
            </h1>
          )}
          <p className="detail-subtitle">{trip.itinerary.destination}</p>
          <p className="detail-dates">
            {formatDateRange(trip.itinerary.start_date, trip.itinerary.end_date)}
          </p>
        </div>
        <div className="detail-actions">
          <Link to="/trips" className="btn btn-secondary">← Back to Trips</Link>
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="detail-body">
        {/* Itinerary Section */}
        {trip.itinerary ? (
          <div className="dashboard-section">
            <h2 className="section-title">Itinerary</h2>
            <div className="day-cards">
              {daySections.map((day) => (
                <div key={day.dayNumber} className="day-card">
                  <button
                    className="day-card-header"
                    onClick={() => toggleDay(day.dayNumber)}
                    aria-expanded={dayStates[day.dayNumber]}
                  >
                    <h3 className="day-card-title">
                      Day {day.dayNumber} — {day.title}
                    </h3>
                    <span className="day-card-chevron">
                      {dayStates[day.dayNumber] ? '▼' : '▶'}
                    </span>
                  </button>
                  {dayStates[day.dayNumber] && (
                    <div className="day-card-content">
                      <MarkdownRenderer content={day.content} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="dashboard-section">
            <h2 className="section-title">Itinerary</h2>
            <div className="empty-section">
              <p>No itinerary yet</p>
              <Link to="/itineraries/new" className="btn btn-primary">Generate Itinerary</Link>
            </div>
          </div>
        )}

        {/* Flights Section */}
        <div className="dashboard-section">
          <h2 className="section-title">Flights</h2>
          {trip.flight_search ? (
            <div className="module-card module-card--attached">
              <div className="module-card-content">
                <div className="module-card-icon">✈️</div>
                <div>
                  <h3 className="module-card-title">Flights attached</h3>
                  <p className="module-card-description">{trip.flight_search.natural_query}</p>
                </div>
              </div>
              <Link to="/flights" className="btn btn-secondary">Search Again</Link>
            </div>
          ) : (
            <div className="module-card module-card--empty">
              <div className="module-card-content">
                <div className="module-card-icon">✈️</div>
                <div>
                  <h3 className="module-card-title">Add flights</h3>
                  <p className="module-card-description">Find and book flights for your trip</p>
                </div>
              </div>
              <Link to="/flights" className="btn btn-primary">Search Flights →</Link>
            </div>
          )}
        </div>

        {/* Hotels Section */}
        <div className="dashboard-section">
          <h2 className="section-title">Hotels</h2>
          {trip.hotel_search ? (
            <div className="module-card module-card--attached">
              <div className="module-card-content">
                <div className="module-card-icon">🏨</div>
                <div>
                  <h3 className="module-card-title">Hotel attached</h3>
                  <p className="module-card-description">
                    {trip.hotel_search.location} — {trip.hotel_search.natural_query}
                  </p>
                </div>
              </div>
              <Link to="/hotels" className="btn btn-secondary">Search Again</Link>
            </div>
          ) : (
            <div className="module-card module-card--empty">
              <div className="module-card-content">
                <div className="module-card-icon">🏨</div>
                <div>
                  <h3 className="module-card-title">Add hotel</h3>
                  <p className="module-card-description">Find and book accommodations</p>
                </div>
              </div>
              <Link to="/hotels" className="btn btn-primary">Search Hotels →</Link>
            </div>
          )}
        </div>

        {/* Cars Section */}
        <div className="dashboard-section">
          <h2 className="section-title">Car Rental</h2>
          {trip.car_rental_search ? (
            <div className="module-card module-card--attached">
              <div className="module-card-content">
                <div className="module-card-icon">🚗</div>
                <div>
                  <h3 className="module-card-title">Car rental attached</h3>
                  <p className="module-card-description">Car rental options selected</p>
                </div>
              </div>
              <Link to="/cars" className="btn btn-secondary">Search Again</Link>
            </div>
          ) : (
            <div className="module-card module-card--empty">
              <div className="module-card-content">
                <div className="module-card-icon">🚗</div>
                <div>
                  <h3 className="module-card-title">Add car</h3>
                  <p className="module-card-description">Find and book rental cars</p>
                </div>
              </div>
              <Link to="/cars" className="btn btn-primary">Search Cars →</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}