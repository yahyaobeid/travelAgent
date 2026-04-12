import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { sendFlightChat, getFlightHistory, clearFlightHistory } from '../api/flights'
import MarkdownRenderer from '../components/MarkdownRenderer'
import type { ChatMessage } from '../types'

const EXAMPLE_CHIPS = [
  { label: '✈ JFK → LAX, May 10–17', query: 'Nonstop JFK to LAX, May 10 returning May 17, under $500' },
  { label: '✈ Chicago → London, June', query: 'Cheapest flight Chicago to London in June, any airline under $700' },
  { label: '✈ NYC → Miami weekend', query: 'Weekend NYC to Miami April 5–7, carry-on only, budget $300' },
  { label: '✈ Boston → SF fastest', query: 'Fastest Boston to San Francisco March 28, business class' },
]

export default function FlightSearchPage() {
  const [searchParams] = useSearchParams()
  const continueSession = searchParams.get('continue') !== null

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (continueSession) {
      getFlightHistory()
        .then(({ display_history }) => setMessages(display_history))
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

    setInput('')
    setSending(true)
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }])

    try {
      const result = await sendFlightChat(trimmed)
      if (result.is_tool_call) {
        setMessages((prev) => [...prev, { role: 'agent', text: result.text, is_tool_call: true }])
      } else {
        setMessages((prev) => [...prev, { role: 'agent', text: result.text, is_tool_call: false }])
      }
    } catch {
      setMessages((prev) => [...prev, { role: 'agent', text: 'Something went wrong. Please try again.' }])
    } finally {
      setSending(false)
    }
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleChipClick = (query: string) => {
    sendMessage(query)
  }

  const showWelcome = messages.length === 0

  return (
    <div className="ct-shell">
      <div className="ct-body" ref={bodyRef}>
        {showWelcome && (
          <div className="ct-welcome">
            <div className="ct-plane-icon" aria-hidden="true">
              <svg viewBox="0 0 48 48" fill="none">
                <circle cx="24" cy="24" r="23" stroke="currentColor" strokeWidth="1" strokeDasharray="3 5" opacity="0.35" />
                <path d="M24 10 L31 28 L24 24 L17 28 Z" fill="currentColor" />
                <path d="M19 28 L21 34 L24 32 L27 34 L29 28" fill="currentColor" opacity="0.5" />
              </svg>
            </div>

            <h1 className="ct-headline">Where are you<br /><em>flying next?</em></h1>
            <p className="ct-subhead">Tell us your trip in plain English — origin, destination, dates, preferences</p>

            <div className="ct-chips-section">
              <span className="ct-chips-label">Quick searches</span>
              <div className="ct-chips" aria-label="Example searches">
                {EXAMPLE_CHIPS.map((chip) => (
                  <button
                    key={chip.label}
                    className="ct-chip"
                    type="button"
                    onClick={() => handleChipClick(chip.query)}
                    disabled={sending}
                  >
                    {chip.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {!showWelcome && (
          <div className="ct-thread">
            {messages.map((msg, i) =>
              msg.role === 'user' ? (
                <div key={i} className="ct-user-msg">
                  <div className="ct-user-bubble">
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
                        <div className="ct-scanning-inline">
                          <div className="ct-scanning-radar" aria-hidden="true">
                            <span /><span /><span />
                          </div>
                          <span>Scanning routes…</span>
                        </div>
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

      <div className="ct-inputbar">
        <div className="ct-inputbar-inner">
          <span className="ct-input-icon" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" />
            </svg>
          </span>
          <label htmlFor="ct-input" className="sr-only">Describe your flight</label>
          <input
            type="text"
            id="ct-input"
            className="ct-input"
            placeholder="e.g. Nonstop NYC to Paris, June 3–10, economy, under $900"
            autoComplete="off"
            autoFocus
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={sending}
          />
          <button
            type="button"
            className="ct-send-btn"
            aria-label="Search flights"
            onClick={() => sendMessage(input)}
            disabled={sending || !input.trim()}
          >
            {sending ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="ct-send-spinner">
                <circle cx="12" cy="12" r="9" strokeDasharray="28" strokeDashoffset="10" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
        <p className="ct-hint">
          {sending
            ? 'Searching flights…'
            : 'Describe your trip naturally — press Enter or click send'}
        </p>
      </div>
    </div>
  )
}
