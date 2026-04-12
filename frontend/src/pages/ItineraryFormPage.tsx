import { useState, useEffect, useRef, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { createItinerary, getItinerary, updateItinerary } from '../api/itineraries'
import LoadingOverlay from '../components/LoadingOverlay'
import { STYLE_CHOICES, type TravelStyle } from '../types'

type Mode = 'create' | 'edit'

const STYLE_META: Record<TravelStyle, { icon: string; description: string }> = {
  general: {
    icon: '🌍',
    description: 'A balanced mix of everything — sightseeing, food, culture, and downtime.',
  },
  culture_history: {
    icon: '🏛️',
    description: 'Museums, landmarks, local traditions, and historical sites.',
  },
  city_shopping: {
    icon: '🛍️',
    description: 'Urban exploration, markets, boutiques, and the best neighbourhoods.',
  },
  adventure: {
    icon: '🏔️',
    description: 'Hikes, outdoor activities, and experiences off the beaten path.',
  },
}

function tripDuration(start: string, end: string): string | null {
  if (!start || !end) return null
  const s = new Date(start)
  const e = new Date(end)
  if (isNaN(s.getTime()) || isNaN(e.getTime()) || e <= s) return null
  const days = Math.round((e.getTime() - s.getTime()) / 86400000)
  return days === 1 ? '1 night' : `${days} nights`
}

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export default function ItineraryFormPage() {
  const { pk } = useParams<{ pk?: string }>()
  const mode: Mode = pk ? 'edit' : 'create'
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const [step, setStep] = useState(1)

  const [destination, setDestination] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [interests, setInterests] = useState('')
  const [activities, setActivities] = useState('')
  const [foodPreferences, setFoodPreferences] = useState('')
  const [preference, setPreference] = useState<TravelStyle>('general')
  const [generatedPlan, setGeneratedPlan] = useState('')
  const [regenerate, setRegenerate] = useState(false)
  const [prefsOpen, setPrefsOpen] = useState(false)

  const [loading, setLoading] = useState(false)
  const [fetchLoading, setFetchLoading] = useState(mode === 'edit')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const destinationRef = useRef<HTMLTextAreaElement>(null)

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
          setPrefsOpen(!!(itinerary.interests || itinerary.activities || itinerary.food_preferences))
        })
        .catch(() => navigate('/'))
        .finally(() => setFetchLoading(false))
    }
  }, [mode, pk, navigate])

  useEffect(() => {
    if (mode === 'create' && step === 1 && destinationRef.current) {
      destinationRef.current.focus()
    }
  }, [mode, step])

  const duration = tripDuration(startDate, endDate)

  const validateStep1 = (): boolean => {
    const e: Record<string, string> = {}
    if (!destination.trim()) e.destination = 'Please enter a destination.'
    if (!startDate) e.start_date = 'Please pick a start date.'
    if (!endDate) e.end_date = 'Please pick an end date.'
    if (startDate && endDate && endDate <= startDate) {
      e.end_date = 'End date must be after start date.'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const goToStep2 = () => {
    if (validateStep1()) setStep(2)
  }

  const goToStep3 = () => setStep(3)

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

  if (fetchLoading) {
    return <div className="loading-screen"><div className="compass-ring" /></div>
  }

  if (mode === 'edit') {
    return (
      <>
        {loading && <LoadingOverlay message={regenerate ? 'Regenerating your itinerary…' : 'Saving changes…'} />}
        <div className="form-page">
          <div className="form-wizard">
            <div className="form-wizard-header">
              <h1 className="form-wizard-title">Edit itinerary</h1>
              <p className="form-wizard-sub">Update your trip details below.</p>
            </div>

            {(errors.__all__ || errors.error) && (
              <div className="form-error" role="alert">
                {errors.__all__ || errors.error}
              </div>
            )}

            <form onSubmit={(e) => handleSubmit(e, 'preview')} noValidate className="form-wizard-body">
              <div className="wiz-section">
                <div className="wiz-section-label">Where &amp; When</div>

                <div className="form-group">
                  <label htmlFor="destination">Destination</label>
                  <small className="help-text">List each city with country, in order. For multi-city trips, note roughly how long you'll spend in each.</small>
                  <textarea
                    id="destination"
                    ref={destinationRef}
                    rows={3}
                    value={destination}
                    placeholder="e.g. Tokyo, Japan (5 days) → Kyoto, Japan (3 days)"
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
                      min={today()}
                      value={startDate}
                      onChange={(e) => {
                        setStartDate(e.target.value)
                        if (endDate && endDate <= e.target.value) setEndDate('')
                      }}
                      required
                    />
                    {errors.start_date && <span className="field-error">{errors.start_date}</span>}
                  </div>
                  <div className="form-group">
                    <label htmlFor="end_date">
                      End date
                      {duration && <span className="duration-badge">{duration}</span>}
                    </label>
                    <input
                      id="end_date"
                      type="date"
                      min={startDate || today()}
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      required
                    />
                    {errors.end_date && <span className="field-error">{errors.end_date}</span>}
                  </div>
                </div>
              </div>

              <div className="wiz-section">
                <div className="wiz-section-label">Travel style</div>
                <div className="style-cards">
                  {(Object.entries(STYLE_CHOICES) as [TravelStyle, string][]).map(([value, label]) => (
                    <label key={value} className={`style-card${preference === value ? ' style-card--selected' : ''}`}>
                      <input
                        type="radio"
                        name="preference"
                        value={value}
                        checked={preference === value}
                        onChange={() => setPreference(value)}
                      />
                      <span className="style-card-icon">{STYLE_META[value].icon}</span>
                      <span className="style-card-name">{label}</span>
                      <span className="style-card-desc">{STYLE_META[value].description}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="wiz-section">
                <div className="wiz-section-label">Preferences <span className="wiz-optional">Optional</span></div>

                <div className="form-group">
                  <label htmlFor="interests">Trip goals &amp; context</label>
                  <small className="help-text">Travel companions, must-see themes, pacing preferences…</small>
                  <textarea
                    id="interests"
                    rows={3}
                    placeholder="e.g. Honeymoon trip, love art and slow mornings, prefer walking over taxis"
                    value={interests}
                    onChange={(e) => setInterests(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="activities">Activities on your wish list</label>
                  <small className="help-text">Specific tours, experiences, or vibes you'd love…</small>
                  <textarea
                    id="activities"
                    rows={3}
                    placeholder="e.g. Tea ceremony, bullet train ride, teamLab digital art museum"
                    value={activities}
                    onChange={(e) => setActivities(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="food_preferences">Food, drink &amp; dietary notes</label>
                  <small className="help-text">Cuisines to try, drinks to explore, restrictions or allergies…</small>
                  <textarea
                    id="food_preferences"
                    rows={3}
                    placeholder="e.g. Love ramen and izakayas, vegetarian, no shellfish"
                    value={foodPreferences}
                    onChange={(e) => setFoodPreferences(e.target.value)}
                  />
                </div>
              </div>

              <div className="wiz-section">
                <div className="wiz-section-label">Current itinerary</div>
                <div className="form-group">
                  <textarea
                    id="generated_plan"
                    rows={14}
                    value={generatedPlan}
                    onChange={(e) => setGeneratedPlan(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={regenerate}
                      onChange={(e) => setRegenerate(e.target.checked)}
                    />
                    Regenerate itinerary with AI
                  </label>
                  <small className="help-text">Check to refresh the itinerary using your updated trip details.</small>
                </div>
              </div>

              <div className="wiz-footer">
                <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
                  {loading ? 'Saving…' : 'Save changes'}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => navigate(-1)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      {loading && <LoadingOverlay message="Generating your itinerary…" />}

      <div className="form-page">
        <div className="form-wizard">

          <div className="form-wizard-header">
            <h1 className="form-wizard-title">Plan your trip</h1>
            <p className="form-wizard-sub">Tell us where you're headed and we'll build a personalised itinerary.</p>
          </div>

          <div className="wiz-steps" aria-label="Form progress">
            {[1, 2, 3].map((s) => (
              <button
                key={s}
                type="button"
                className={`wiz-step${step === s ? ' wiz-step--active' : ''}${step > s ? ' wiz-step--done' : ''}`}
                onClick={() => {
                  if (s < step) { setStep(s); return }
                  if (s === step) return
                  // Forward navigation: validate each step before advancing
                  if (s > step && step === 1 && !validateStep1()) return
                  setStep(s)
                }}
                aria-current={step === s ? 'step' : undefined}
              >
                <span className="wiz-step-num">{step > s ? '✓' : s}</span>
                <span className="wiz-step-label">
                  {s === 1 ? 'Where & When' : s === 2 ? 'Travel Style' : 'Preferences'}
                </span>
              </button>
            ))}
            <div className="wiz-track">
              <div className="wiz-track-fill" style={{ width: `${((step - 1) / 2) * 100}%` }} />
            </div>
          </div>

          {(errors.__all__ || errors.error) && (
            <div className="form-error" role="alert">{errors.__all__ || errors.error}</div>
          )}

          <div className="form-wizard-body">

            {step === 1 && (
              <div className="wiz-panel fade-up" key="step1">
                <div className="form-group">
                  <label htmlFor="destination">Where are you going?</label>
                  <small className="help-text">
                    List each city and country in order. For multi-city trips, include how long you'll spend in each place.
                  </small>
                  <textarea
                    id="destination"
                    ref={destinationRef}
                    rows={3}
                    value={destination}
                    placeholder="e.g. Tokyo, Japan (5 days) → Kyoto, Japan (3 days) → Osaka, Japan (2 days)"
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
                      min={today()}
                      value={startDate}
                      onChange={(e) => {
                        setStartDate(e.target.value)
                        if (endDate && endDate <= e.target.value) setEndDate('')
                      }}
                      required
                    />
                    {errors.start_date && <span className="field-error">{errors.start_date}</span>}
                  </div>
                  <div className="form-group">
                    <label htmlFor="end_date">
                      End date
                      {duration && <span className="duration-badge">{duration}</span>}
                    </label>
                    <input
                      id="end_date"
                      type="date"
                      min={startDate || today()}
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      required
                    />
                    {errors.end_date && <span className="field-error">{errors.end_date}</span>}
                  </div>
                </div>

                <div className="wiz-footer">
                  <button type="button" className="btn btn-primary btn-lg" onClick={goToStep2}>
                    Continue
                    <span className="btn-arrow">→</span>
                  </button>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="wiz-panel fade-up" key="step2">
                <p className="wiz-panel-lead">Choose the vibe for your trip — this shapes how the AI writes your plan.</p>

                <div className="style-cards">
                  {(Object.entries(STYLE_CHOICES) as [TravelStyle, string][]).map(([value, label]) => (
                    <label key={value} className={`style-card${preference === value ? ' style-card--selected' : ''}`}>
                      <input
                        type="radio"
                        name="preference"
                        value={value}
                        checked={preference === value}
                        onChange={() => setPreference(value)}
                      />
                      <span className="style-card-icon">{STYLE_META[value].icon}</span>
                      <span className="style-card-name">{label}</span>
                      <span className="style-card-desc">{STYLE_META[value].description}</span>
                    </label>
                  ))}
                </div>

                <div className="wiz-footer">
                  <button type="button" className="btn btn-primary btn-lg" onClick={goToStep3}>
                    Continue
                    <span className="btn-arrow">→</span>
                  </button>
                  <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}>
                    Back
                  </button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="wiz-panel fade-up" key="step3">
                <div className="trip-summary-pill">
                  <span className="trip-summary-dest">{destination || '—'}</span>
                  <span className="trip-summary-sep">·</span>
                  {duration ? (
                    <span className="trip-summary-dur">{duration}</span>
                  ) : (
                    <span className="trip-summary-dur">{startDate} → {endDate}</span>
                  )}
                  <span className="trip-summary-sep">·</span>
                  <span className="trip-summary-style">{STYLE_CHOICES[preference]}</span>
                </div>

                <button
                  type="button"
                  className={`prefs-toggle${prefsOpen ? ' prefs-toggle--open' : ''}`}
                  onClick={() => setPrefsOpen((v) => !v)}
                  aria-expanded={prefsOpen}
                >
                  <span className="prefs-toggle-icon">{prefsOpen ? '−' : '+'}</span>
                  {prefsOpen ? 'Hide preferences' : 'Add preferences'}
                  <span className="prefs-toggle-sub">Interests, activities, food &amp; dietary notes</span>
                </button>

                {prefsOpen && (
                  <div className="prefs-fields fade-up">
                    <div className="form-group">
                      <label htmlFor="interests">Trip goals &amp; context</label>
                      <small className="help-text">Travel companions, must-see themes, pacing preferences…</small>
                      <textarea
                        id="interests"
                        rows={3}
                        placeholder="e.g. Honeymoon trip, love art and slow mornings, prefer walking over taxis"
                        value={interests}
                        onChange={(e) => setInterests(e.target.value)}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="activities">Activities on your wish list</label>
                      <small className="help-text">Specific tours, experiences, or vibes you'd love…</small>
                      <textarea
                        id="activities"
                        rows={3}
                        placeholder="e.g. Tea ceremony, bullet train ride, TeamLab digital art museum"
                        value={activities}
                        onChange={(e) => setActivities(e.target.value)}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="food_preferences">Food, drink &amp; dietary notes</label>
                      <small className="help-text">Cuisines to try, drinks to explore, restrictions or allergies…</small>
                      <textarea
                        id="food_preferences"
                        rows={3}
                        placeholder="e.g. Love ramen and izakayas, vegetarian, no shellfish"
                        value={foodPreferences}
                        onChange={(e) => setFoodPreferences(e.target.value)}
                      />
                    </div>
                  </div>
                )}

                <div className="wiz-footer wiz-footer--generate">
                  <form onSubmit={(e) => handleSubmit(e, isAuthenticated ? 'save' : 'preview')} noValidate>
                    <button type="submit" className="btn btn-primary btn-lg btn-generate" disabled={loading}>
                      <span className="btn-generate-icon">✦</span>
                      {isAuthenticated ? 'Generate & save itinerary' : 'Generate itinerary'}
                    </button>
                  </form>
                  {!isAuthenticated && (
                    <p className="wiz-guest-note">
                      You'll get a free preview — <a href="/register">create an account</a> to save it.
                    </p>
                  )}
                  <button type="button" className="btn btn-ghost" onClick={() => setStep(2)}>
                    Back
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </>
  )
}
