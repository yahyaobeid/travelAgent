import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { searchCars } from '../api/cars'
import LoadingOverlay from '../components/LoadingOverlay'
import type { CarSearchResult } from '../types'

export default function CarSearchPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState<CarSearchResult | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setError('')
    setLoading(true)
    try {
      const data = await searchCars(query)
      if (isAuthenticated && data.search_id) {
        navigate(`/cars/${data.search_id}`)
      } else {
        setResults(data)
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
      setError(msg ?? 'Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {loading && <LoadingOverlay message="Searching car rentals…" />}

      <div className="form-page">
        <div className="form-card">
          <h1 className="form-title">Car rentals</h1>
          <p className="form-subtitle">Describe what you're looking for in plain language.</p>

          {error && <div className="form-error" role="alert">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="query">What are you looking for?</label>
              <textarea
                id="query"
                rows={3}
                placeholder="e.g. Economy car in Miami for 5 days next month, under $50/day"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              Search car rentals
            </button>
          </form>
        </div>

        {results && (
          <div className="results-section">
            <h2 className="section-title">
              {results.count} result{results.count !== 1 ? 's' : ''} for{' '}
              {results.search_params.location}
            </h2>
            <div className="card-grid">
              {results.results.map((car, i) => (
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
        )}
      </div>
    </>
  )
}
