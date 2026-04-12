import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import type { HotelSearchResult, HotelListing } from '../types'

export default function HotelResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [hotels, setHotels] = useState<HotelListing[]>([])
  const [sortByPrice, setSortByPrice] = useState(false)

  useEffect(() => {
    const results = location.state?.results as HotelSearchResult | undefined
    if (!results) {
      navigate('/hotels')
      return
    }
    setHotels(results.results)
  }, [location.state, navigate])

  const renderStarRating = (rating: number) => {
    const stars = []
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} aria-hidden="true">
          {i <= rating ? '★' : '☆'}
        </span>
      )
    }
    return (
      <div className="star-rating" aria-label={`${rating} out of 5 stars`}>
        {stars}
      </div>
    )
  }

  const renderAmenities = (amenities: string | string[]) => {
    const amenityArray = Array.isArray(amenities)
      ? amenities
      : amenities.split(',').map(a => a.trim()).filter(Boolean)

    return (
      <div className="amenities">
        {amenityArray.map((amenity, i) => (
          <span key={i} className="amenity-chip">{amenity}</span>
        ))}
      </div>
    )
  }

  const sortedHotels = sortByPrice
    ? [...hotels].sort((a, b) => {
        const priceA = parseFloat(a.price_display.replace(/[^0-9.]/g, ''))
        const priceB = parseFloat(b.price_display.replace(/[^0-9.]/g, ''))
        return priceA - priceB
      })
    : hotels

  if (hotels.length === 0) {
    return (
      <div className="detail-page">
        <div className="detail-header">
          <h1 className="detail-title">Loading hotels...</h1>
        </div>
      </div>
    )
  }

  return (
    <div className="detail-page">
      <div className="detail-header">
        <div>
          <h1 className="detail-title">Hotel search results</h1>
          <p className="detail-dates">
            {hotels.length} hotel{hotels.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <div className="detail-actions">
          <button
            type="button"
            className={`btn ${sortByPrice ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSortByPrice(!sortByPrice)}
          >
            {sortByPrice ? 'Original order' : 'Sort by price'}
          </button>
          <Link to="/hotels" className="btn btn-secondary">New search</Link>
        </div>
      </div>

      <div className="card-grid">
        {sortedHotels.map((hotel, i) => (
          <article key={i} className="hotel-card">
            <div className="hotel-card-header">
              <h3 className="hotel-card-name">{hotel.name}</h3>
              <span className="hotel-card-price">{hotel.price_display}</span>
            </div>

            <div className="hotel-card-rating">
              {renderStarRating(hotel.star_rating)}
            </div>

            <div className="hotel-card-meta">
              <span className="hotel-meta-chip">{hotel.hotel_type}</span>
              <span className="hotel-meta-chip">{hotel.location}</span>
            </div>

            {(hotel.checkin_time || hotel.checkout_time) && (
              <div className="hotel-card-times">
                {hotel.checkin_time && <span>Check-in: {hotel.checkin_time}</span>}
                {hotel.checkout_time && <span>Check-out: {hotel.checkout_time}</span>}
              </div>
            )}

            {hotel.amenities && renderAmenities(hotel.amenities)}

            {hotel.listing_url && (
              <a
                href={hotel.listing_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-sm"
              >
                Book Now ↗
              </a>
            )}
          </article>
        ))}
      </div>
    </div>
  )
}