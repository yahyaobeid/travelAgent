import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchHotels } from '../api/hotels'
import LoadingOverlay from '../components/LoadingOverlay'
import type { HotelSearchResult } from '../types'

export default function HotelSearchPage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setError('')
    setLoading(true)

    try {
      const results = await searchHotels(query)
      navigate('/hotels/results', { state: { results } })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
      setError(msg ?? 'Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {loading && <LoadingOverlay message="Searching hotels…" />}

      <div className="form-page">
        <div className="form-card">
          <h1 className="form-title">Hotel search</h1>
          <p className="form-subtitle">Describe what you're looking for in plain language.</p>

          {error && <div className="form-error" role="alert">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="query">What are you looking for?</label>
              <textarea
                id="query"
                rows={3}
                placeholder="e.g. Hotel in Paris for 3 nights in June under $200/night"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              Search hotels
            </button>
          </form>
        </div>
      </div>
    </>
  )
}