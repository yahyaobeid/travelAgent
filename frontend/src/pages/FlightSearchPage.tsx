import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { sendFlightChat, getFlightHistory, clearFlightHistory } from '../api/flights'
import MarkdownRenderer from '../components/MarkdownRenderer'
import type { ChatMessage } from '../types'

const EXAMPLE_CHIPS = [
  { label: 'JFK → LAX, May 10–17', query: 'Nonstop JFK to LAX, May 10 returning May 17, under $500' },
  { label: 'Chicago → London, June', query: 'Cheapest flight Chicago to London in June, any airline under $700' },
  { label: 'NYC → Miami weekend', query: 'Weekend NYC to Miami April 5–7, carry-on only, budget $300' },
  { label: 'BOS → SFO fastest', query: 'Fastest Boston to San Francisco March 28, business class' },
]

export default function FlightSearchPage() {
  const [searchParams] = useSearchParams()
  const continueSession = searchParams.get('continue') !== null

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [scanning, setScanning] = useState(false)
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
        setScanning(true)
        // Keep scanning overlay until next real message arrives
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

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const showWelcome = messages.length === 0

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

      <div className="ct-shell">
        <div className="ct-body" ref={bodyRef}>
          {showWelcome && (
            <div className="ct-welcome">
              <svg className="ct-icon" viewBox="0 0 64 64" aria-hidden="true">
                <circle className="ct-icon-ring" cx="32" cy="32" r="28" strokeDasharray="4 6" />
                <path className="ct-icon-plane" d="M32 14 L40 34 L32 30 L24 34 Z" />
                <path className="ct-icon-plane" opacity="0.5" d="M27 34 L29 40 L32 38 L35 40 L37 34" />
              </svg>
              <h1 className="ct-headline">Where are you<br /><em>flying next?</em></h1>
              <p className="ct-subhead">describe your trip in plain language</p>
              <div className="ct-chips" aria-label="Example searches">
                {EXAMPLE_CHIPS.map((chip) => (
                  <button
                    key={chip.label}
                    className="ct-chip"
                    type="button"
                    onClick={() => setInput(chip.query)}
                  >
                    {chip.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {!showWelcome && (
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

        <div className="ct-inputbar">
          <div className="ct-inputbar-inner">
            <span className="ct-input-prefix" aria-hidden="true">›</span>
            <label htmlFor="ct-input" className="sr-only">Describe your flight</label>
            <input
              type="text"
              id="ct-input"
              className="ct-input"
              placeholder="e.g. Nonstop NYC to Paris, June 3, returning June 10, economy"
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
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
          <p className="ct-hint">Press Enter or click send — no form fields required</p>
        </div>
      </div>
    </>
  )
}
