import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { getCarSearch } from '../api/cars'
import type { CarDetailResponse } from '../api/cars'

export default function CarResultsPage() {
  const { pk } = useParams<{ pk: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<CarDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!pk) return
    getCarSearch(Number(pk))
      .then(setData)
      .catch(() => navigate('/cars'))
      .finally(() => setLoading(false))
  }, [pk, navigate])

  if (loading) return <div className="loading-screen"><div className="compass-ring" /></div>
  if (!data) return null

  const { search, results } = data

  return (
    <div className="detail-page">
      <div className="detail-header">
        <div>
          <h1 className="detail-title">Car rentals in {search.location}</h1>
          <p className="detail-dates">
            {search.pickup_date} – {search.dropoff_date}
            {search.car_type && ` · ${search.car_type}`}
            {search.max_price_per_day && ` · up to $${search.max_price_per_day}/day`}
          </p>
          <p className="text-muted">{search.natural_query}</p>
        </div>
        <div className="detail-actions">
          <Link to="/cars" className="btn btn-secondary">New search</Link>
        </div>
      </div>

      <div className="card-grid">
        {results.map((car, i) => (
          <article key={i} className="car-card">
            <div className="car-card-header">
              <h3 className="car-card-name">{car.car_name}</h3>
              <span className="car-card-price">{car.price_display}<span className="per-day">/day</span></span>
            </div>
            <p className="car-card-company">{car.rental_company}</p>
            <div className="car-card-meta">
              <span className="car-meta-chip">{car.car_type}</span>
              <span className="car-meta-chip">{car.location}</span>
              {car.availability && <span className="car-meta-chip">{car.availability}</span>}
            </div>
            {car.listing_url && (
              <a href={car.listing_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
                View listing ↗
              </a>
            )}
          </article>
        ))}
      </div>
    </div>
  )
}
