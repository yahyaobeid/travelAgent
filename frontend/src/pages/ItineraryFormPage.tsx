import { useState, useEffect, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { createItinerary, getItinerary, updateItinerary } from '../api/itineraries'
import LoadingOverlay from '../components/LoadingOverlay'
import { STYLE_CHOICES, type TravelStyle } from '../types'

type Mode = 'create' | 'edit'

export default function ItineraryFormPage() {
  const { pk } = useParams<{ pk?: string }>()
  const mode: Mode = pk ? 'edit' : 'create'
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const [destination, setDestination] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [interests, setInterests] = useState('')
  const [activities, setActivities] = useState('')
  const [foodPreferences, setFoodPreferences] = useState('')
  const [preference, setPreference] = useState<TravelStyle>('general')
  const [generatedPlan, setGeneratedPlan] = useState('')
  const [regenerate, setRegenerate] = useState(false)
  const [loading, setLoading] = useState(false)
  const [fetchLoading, setFetchLoading] = useState(mode === 'edit')
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (mode === 'edit' && pk) {
      getItinerary(Number(pk))
        .then(({ itinerary }) => {
          setDestination(itinerary.destination)
          setStartDate(itinerary.start_date)
          setEndDate(itinerary.end_date)
          setInterests(itinerary.interests)
          setActivities(itinerary.activities)
          setFoodPreferences(itinerary.food_preferences)
          setPreference(itinerary.preference as TravelStyle)
          setGeneratedPlan(itinerary.generated_plan)
        })
        .catch(() => navigate('/'))
        .finally(() => setFetchLoading(false))
    }
  }, [mode, pk, navigate])

  const handleSubmit = async (e: FormEvent, action: 'preview' | 'save') => {
    e.preventDefault()
    setErrors({})
    setLoading(true)

    try {
      if (mode === 'create') {
        const result = await createItinerary({
          destination,
          start_date: startDate,
          end_date: endDate,
          interests,
          activities,
          food_preferences: foodPreferences,
          preference,
          action: isAuthenticated ? 'save' : action,
        })

        if ('preview' in result && result.preview) {
          navigate('/itineraries/preview')
        } else {
          navigate(`/itineraries/${(result as { id: number }).id}`)
        }
      } else if (mode === 'edit' && pk) {
        const updated = await updateItinerary(Number(pk), {
          destination,
          start_date: startDate,
          end_date: endDate,
          interests,
          activities,
          food_preferences: foodPreferences,
          preference,
          generated_plan: generatedPlan,
          regenerate_plan: regenerate,
        })
        navigate(`/itineraries/${updated.id}`)
      }
    } catch (err: unknown) {
      const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data ?? {}
      const mapped: Record<string, string> = {}
      for (const [k, v] of Object.entries(data)) {
        mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      }
      setErrors(mapped)
    } finally {
      setLoading(false)
    }
  }

  if (fetchLoading) return <div className="loading-screen"><div className="compass-ring" /></div>

  return (
    <>
      {loading && <LoadingOverlay message={mode === 'edit' && regenerate ? 'Regenerating your itinerary…' : 'Generating your itinerary…'} />}

      <div className="form-page">
        <div className="form-card form-card--wide">
          <h1 className="form-title">{mode === 'create' ? 'Plan a trip' : 'Edit itinerary'}</h1>

          {errors.__all__ && <div className="form-error" role="alert">{errors.__all__}</div>}
          {errors.error && <div className="form-error" role="alert">{errors.error}</div>}

          <form onSubmit={(e) => handleSubmit(e, 'preview')} noValidate>
            <div className="form-group">
              <label htmlFor="destination">Where are you staying?</label>
              <small className="help-text">List each city and country in order (include the state code for U.S. stays) and roughly how long you'll be in each.</small>
              <textarea
                id="destination"
                rows={3}
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                required
              />
              {errors.destination && <span className="field-error">{errors.destination}</span>}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="start_date">Start date</label>
                <input
                  id="start_date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  required
                />
                {errors.start_date && <span className="field-error">{errors.start_date}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="end_date">End date</label>
                <input
                  id="end_date"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  required
                />
                {errors.end_date && <span className="field-error">{errors.end_date}</span>}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="interests">Trip goals &amp; context</label>
              <small className="help-text">Share any broader context (travel companions, must-see themes, pacing preferences).</small>
              <textarea
                id="interests"
                rows={4}
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="activities">Activities on your wish list</label>
              <small className="help-text">Tell us about specific tours, experiences, or vibes you'd love to include.</small>
              <textarea
                id="activities"
                rows={4}
                value={activities}
                onChange={(e) => setActivities(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="food_preferences">Food, drink, and dietary notes</label>
              <small className="help-text">Let us know cuisines to prioritise, drinks to try, and dietary restrictions or allergies.</small>
              <textarea
                id="food_preferences"
                rows={4}
                value={foodPreferences}
                onChange={(e) => setFoodPreferences(e.target.value)}
              />
            </div>

            <fieldset className="form-group">
              <legend>Travel style</legend>
              <small className="help-text">Choose the overall vibe you'd like for this itinerary.</small>
              <div className="radio-group">
                {(Object.entries(STYLE_CHOICES) as [TravelStyle, string][]).map(([value, label]) => (
                  <label key={value} className="radio-label">
                    <input
                      type="radio"
                      name="preference"
                      value={value}
                      checked={preference === value}
                      onChange={() => setPreference(value)}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </fieldset>

            {mode === 'edit' && (
              <>
                <div className="form-group">
                  <label htmlFor="generated_plan">Current itinerary</label>
                  <textarea
                    id="generated_plan"
                    rows={14}
                    value={generatedPlan}
                    onChange={(e) => setGeneratedPlan(e.target.value)}
                  />
                </div>
                <div className="form-group form-group--checkbox">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={regenerate}
                      onChange={(e) => setRegenerate(e.target.checked)}
                    />
                    Regenerate itinerary with AI
                  </label>
                  <small className="help-text">Check to refresh the itinerary using the latest trip details.</small>
                </div>
              </>
            )}

            <div className="form-actions">
              {mode === 'create' ? (
                <>
                  {!isAuthenticated && (
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={loading}
                      onClick={(e) => handleSubmit(e as unknown as FormEvent, 'preview')}
                    >
                      Preview itinerary
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={loading}
                    onClick={(e) => handleSubmit(e as unknown as FormEvent, isAuthenticated ? 'save' : 'preview')}
                  >
                    {isAuthenticated ? 'Generate &amp; save' : 'Generate itinerary'}
                  </button>
                </>
              ) : (
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving…' : 'Save changes'}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
