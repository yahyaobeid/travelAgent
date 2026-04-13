import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { sendFlightChat, getFlightHistory, clearFlightHistory } from '../api/flights'
import MarkdownRenderer from '../components/MarkdownRenderer'
import type { ChatMessage } from '../types'

type TripType = 'round-trip' | 'one-way'
type CabinClass = 'Economy' | 'Premium Economy' | 'Business' | 'First'

interface FlightForm {
  tripType: TripType
  from: string
  to: string
  departDate: string
  returnDate: string
  passengers: number
  cabin: CabinClass
  extra: string
}

const defaultForm: FlightForm = {
  tripType: 'round-trip',
  from: '',
  to: '',
  departDate: '',
  returnDate: '',
  passengers: 1,
  cabin: 'Economy',
  extra: '',
}

const QUICK_SEARCHES: { label: string; form: Partial<FlightForm> }[] = [
  {
    label: 'JFK → LAX, May 10–17',
    form: { from: 'New York (JFK)', to: 'Los Angeles (LAX)', departDate: '2026-05-10', returnDate: '2026-05-17', tripType: 'round-trip', extra: 'Nonstop preferred, under $500' },
  },
  {
    label: 'Chicago → London, June',
    form: { from: 'Chicago (ORD)', to: 'London (LHR)', departDate: '2026-06-01', returnDate: '2026-06-14', tripType: 'round-trip', extra: 'Budget under $700, any airline' },
  },
  {
    label: 'NYC → Miami weekend',
    form: { from: 'New York (JFK)', to: 'Miami (MIA)', departDate: '2026-04-05', returnDate: '2026-04-07', tripType: 'round-trip', extra: 'Carry-on only, budget $300' },
  },
  {
    label: 'BOS → SFO business',
    form: { from: 'Boston (BOS)', to: 'San Francisco (SFO)', departDate: '2026-03-28', tripType: 'one-way', cabin: 'Business', extra: 'Fastest nonstop route' },
  },
]

function buildQuery(form: FlightForm): string {
  const { tripType, from, to, departDate, returnDate, passengers, cabin, extra } = form
  const fromLabel = from.trim() || 'the origin'
  const toLabel = to.trim() || 'the destination'

  const fmtDate = (d: string) =>
    d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : null

  const dept = fmtDate(departDate) ?? 'the soonest available date'
  let q = `${tripType === 'round-trip' ? 'Round trip' : 'One-way'} flight from ${fromLabel} to ${toLabel}, departing ${dept}`

  if (tripType === 'round-trip' && returnDate) {
    const ret = fmtDate(returnDate)
    if (ret) q += `, returning ${ret}`
  }

  q += `, ${passengers} ${passengers === 1 ? 'passenger' : 'passengers'}, ${cabin} class`
  if (extra.trim()) q += `. ${extra.trim()}`

  return q
}

export default function FlightSearchPage() {
  const [searchParams] = useSearchParams()
  const continueSession = searchParams.get('continue') !== null

  const [form, setForm] = useState<FlightForm>(defaultForm)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [followUp, setFollowUp] = useState('')
  const [sending, setSending] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [panelExpanded, setPanelExpanded] = useState(true)

  const bodyRef = useRef<HTMLDivElement>(null)
  const hasResults = messages.length > 0

  useEffect(() => {
    if (continueSession) {
      getFlightHistory()
        .then(({ display_history }) => {
          setMessages(display_history)
          if (display_history.length > 0) setPanelExpanded(false)
        })
        .catch(() => {})
    } else {
      clearFlightHistory().catch(() => {})
    }
  }, [continueSession])

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight
    }
  }, [messages])

  const sendMessage = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || sending) return

    setFollowUp('')
    setSending(true)
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }])
    setPanelExpanded(false)

    try {
      const result = await sendFlightChat(trimmed)
      if (result.is_tool_call) {
        setScanning(true)
        setMessages((prev) => [...prev, { role: 'agent', text: result.text, is_tool_call: true }])
      } else {
        setScanning(false)
        setMessages((prev) => [...prev, { role: 'agent', text: result.text, is_tool_call: false }])
      }
    } catch {
      setScanning(false)
      setMessages((prev) => [...prev, { role: 'agent', text: 'Something went wrong. Please try again.' }])
    } finally {
      setSending(false)
    }
  }

  const handleFormSearch = () => {
    if (!form.from.trim() || !form.to.trim() || sending) return
    sendMessage(buildQuery(form))
  }

  const handleFollowUpKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(followUp)
    }
  }

  const updateForm = (patch: Partial<FlightForm>) => setForm((f) => ({ ...f, ...patch }))

  const swapFromTo = () => setForm((f) => ({ ...f, from: f.to, to: f.from }))

  const applyQuickSearch = (partial: Partial<FlightForm>) =>
    setForm({ ...defaultForm, ...partial })

  const today = new Date().toISOString().split('T')[0]
  const isFormValid = form.from.trim().length > 0 && form.to.trim().length > 0

  return (
    <>
      {scanning && (
        <div className="ct-loading active" aria-live="polite" role="status">
          <div className="ct-loading-box">
            <div className="ct-loading-radar">
              <div className="ct-radar-ring" />
              <div className="ct-radar-ring" />
              <div className="ct-radar-ring" />
              <div className="ct-radar-center" />
            </div>
            <p className="ct-loading-title">Scanning routes</p>
            <p className="ct-loading-sub">Agent is searching&hellip;</p>
          </div>
        </div>
      )}

      <div className="fs-shell">
        {/* ── Search Panel ── */}
        <div className={`fs-panel${hasResults && !panelExpanded ? ' fs-panel--compact' : ''}`}>
          {hasResults && !panelExpanded ? (
            <div className="fs-compact-bar">
              <div className="fs-compact-summary">
                <span className="fs-compact-route">
                  {form.from || '—'}&nbsp;&rarr;&nbsp;{form.to || '—'}
                </span>
                <span className="fs-compact-meta">
                  {form.tripType === 'round-trip' ? 'Round trip' : 'One-way'}&nbsp;&middot;&nbsp;
                  {form.passengers}&nbsp;{form.passengers === 1 ? 'passenger' : 'passengers'}&nbsp;&middot;&nbsp;
                  {form.cabin}
                </span>
              </div>
              <button className="fs-modify-btn" type="button" onClick={() => setPanelExpanded(true)}>
                Modify search
              </button>
            </div>
          ) : (
            <>
              <div className="fs-panel-header">
                <div className="fs-panel-title-row">
                  <h1 className="fs-headline">
                    {hasResults ? 'Modify Search' : <>Where are you <em>flying next?</em></>}
                  </h1>
                  {hasResults && (
                    <button className="fs-collapse-btn" type="button" onClick={() => setPanelExpanded(false)} aria-label="Collapse">
                      ✕
                    </button>
                  )}
                </div>
                <div className="fs-trip-type" role="group" aria-label="Trip type">
                  {(['round-trip', 'one-way'] as TripType[]).map((t) => (
                    <button
                      key={t}
                      type="button"
                      className={`fs-trip-pill${form.tripType === t ? ' active' : ''}`}
                      onClick={() => updateForm({ tripType: t })}
                    >
                      {t === 'round-trip' ? 'Round Trip' : 'One Way'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="fs-fields">
                {/* From / To row */}
                <div className="fs-origin-dest">
                  <div className="fs-field">
                    <label className="fs-field-label">From</label>
                    <input
                      type="text"
                      className="fs-field-input"
                      placeholder="City or airport code"
                      value={form.from}
                      onChange={(e) => updateForm({ from: e.target.value })}
                      autoComplete="off"
                    />
                  </div>

                  <button className="fs-swap-btn" type="button" onClick={swapFromTo} aria-label="Swap origin and destination">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M7 16V4m0 0L3 8m4-4l4 4" />
                      <path d="M17 8v12m0 0l4-4m-4 4l-4-4" />
                    </svg>
                  </button>

                  <div className="fs-field">
                    <label className="fs-field-label">To</label>
                    <input
                      type="text"
                      className="fs-field-input"
                      placeholder="City or airport code"
                      value={form.to}
                      onChange={(e) => updateForm({ to: e.target.value })}
                      autoComplete="off"
                    />
                  </div>
                </div>

                {/* Dates + passengers + cabin */}
                <div className="fs-details-row">
                  <div className="fs-field">
                    <label className="fs-field-label">Depart</label>
                    <input
                      type="date"
                      className="fs-field-input"
                      min={today}
                      value={form.departDate}
                      onChange={(e) => updateForm({ departDate: e.target.value })}
                    />
                  </div>

                  {form.tripType === 'round-trip' && (
                    <div className="fs-field">
                      <label className="fs-field-label">Return</label>
                      <input
                        type="date"
                        className="fs-field-input"
                        min={form.departDate || today}
                        value={form.returnDate}
                        onChange={(e) => updateForm({ returnDate: e.target.value })}
                      />
                    </div>
                  )}

                  <div className="fs-field">
                    <label className="fs-field-label">Passengers</label>
                    <div className="fs-pax-ctrl">
                      <button
                        type="button"
                        className="fs-pax-btn"
                        onClick={() => updateForm({ passengers: Math.max(1, form.passengers - 1) })}
                        aria-label="Remove passenger"
                      >
                        −
                      </button>
                      <span className="fs-pax-num">{form.passengers}</span>
                      <button
                        type="button"
                        className="fs-pax-btn"
                        onClick={() => updateForm({ passengers: Math.min(9, form.passengers + 1) })}
                        aria-label="Add passenger"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  <div className="fs-field">
                    <label className="fs-field-label">Cabin</label>
                    <select
                      className="fs-field-input fs-select"
                      value={form.cabin}
                      onChange={(e) => updateForm({ cabin: e.target.value as CabinClass })}
                    >
                      {(['Economy', 'Premium Economy', 'Business', 'First'] as CabinClass[]).map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Preferences + search button */}
                <div className="fs-extra-row">
                  <div className="fs-field fs-field--full">
                    <label className="fs-field-label">
                      Preferences&nbsp;<span className="fs-optional">(optional — nonstop, budget, airline…)</span>
                    </label>
                    <input
                      type="text"
                      className="fs-field-input"
                      placeholder="e.g. nonstop only, under $600, flexible ±3 days, Alaska Airlines…"
                      value={form.extra}
                      onChange={(e) => updateForm({ extra: e.target.value })}
                      autoComplete="off"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleFormSearch()
                      }}
                    />
                  </div>
                  <button
                    type="button"
                    className="fs-search-btn"
                    onClick={handleFormSearch}
                    disabled={sending || !isFormValid}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <circle cx="11" cy="11" r="8" />
                      <path d="m21 21-4.35-4.35" />
                    </svg>
                    Search Flights
                  </button>
                </div>

                {/* Quick searches */}
                {!hasResults && (
                  <div className="fs-quick">
                    <span className="fs-quick-label">Try:</span>
                    {QUICK_SEARCHES.map((qs) => (
                      <button
                        key={qs.label}
                        type="button"
                        className="fs-quick-chip"
                        onClick={() => applyQuickSearch(qs.form)}
                      >
                        {qs.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* ── Results ── */}
        <div className="fs-body" ref={bodyRef}>
          {!hasResults && (
            <div className="fs-empty">
              <svg className="fs-empty-icon" viewBox="0 0 64 64" aria-hidden="true">
                <circle cx="32" cy="32" r="28" strokeDasharray="4 6" stroke="currentColor" strokeWidth="1" fill="none" />
                <path d="M32 14 L40 34 L32 30 L24 34 Z" fill="currentColor" />
                <path d="M27 34 L29 40 L32 38 L35 40 L37 34" fill="currentColor" opacity="0.5" />
              </svg>
              <p className="fs-empty-text">
                Fill in your route above and hit <strong>Search Flights</strong>
              </p>
            </div>
          )}

          {hasResults && (
            <div className="ct-thread">
              {messages.map((msg, i) =>
                msg.role === 'user' ? (
                  <div key={i} className="ct-user-msg">
                    <div className="ct-user-bubble">
                      <span className="ct-user-label">You</span>
                      <span className="ct-user-text">{msg.text}</span>
                    </div>
                  </div>
                ) : (
                  <div key={i} className="ct-agent-msg">
                    <div className="ct-agent-avatar" aria-hidden="true">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" />
                      </svg>
                    </div>
                    <div className="ct-agent-bubble">
                      <span className="ct-agent-label">TripHelix Agent</span>
                      <div className="ct-agent-content">
                        {msg.is_tool_call ? (
                          <em style={{ color: 'var(--ct-text-dim)' }}>Scanning routes…</em>
                        ) : (
                          <MarkdownRenderer content={msg.text} />
                        )}
                      </div>
                    </div>
                  </div>
                )
              )}

              {sending && (
                <div className="ct-agent-msg">
                  <div className="ct-agent-avatar" aria-hidden="true">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" />
                    </svg>
                  </div>
                  <div className="ct-agent-bubble">
                    <span className="ct-agent-label">TripHelix Agent</span>
                    <div className="ct-typing">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Follow-up bar ── */}
        {hasResults && (
          <div className="fs-followup">
            <div className="fs-followup-inner">
              <label htmlFor="fs-followup-input" className="sr-only">Ask a follow-up</label>
              <input
                id="fs-followup-input"
                type="text"
                className="fs-followup-input"
                placeholder="Refine results — change dates, budget, stop count, airline…"
                value={followUp}
                onChange={(e) => setFollowUp(e.target.value)}
                onKeyDown={handleFollowUpKey}
                disabled={sending}
                autoComplete="off"
              />
              <button
                type="button"
                className="fs-followup-btn"
                onClick={() => sendMessage(followUp)}
                disabled={sending || !followUp.trim()}
                aria-label="Send follow-up"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
