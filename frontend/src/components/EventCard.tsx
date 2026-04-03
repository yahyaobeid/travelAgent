import type { Event } from '../types'

interface EventCardProps {
  event: Event
  index: number
}

function EventCard({ event, index }: EventCardProps) {
  return (
    <article className="event-card" aria-labelledby={`event-title-${index}`}>
      <a
        id={`event-title-${index}`}
        className="event-card-name"
        href={event.url}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`${event.name} (opens in new tab)`}
      >
        {event.name}
      </a>

      <div className="event-card-meta">
        {event.start_date && (
          <span className="event-meta-chip date">
            📅 {new Date(event.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </span>
        )}
        {event.venue && (
          <span className="event-meta-chip location">📍 {event.venue}</span>
        )}
      </div>

      <a
        href={event.url}
        target="_blank"
        rel="noopener noreferrer"
        className="event-card-link"
        aria-label={`View ${event.name} on Ticketmaster (opens in new tab)`}
      >
        View on Ticketmaster ↗
      </a>
    </article>
  )
}

interface EventsSectionProps {
  events: Event[]
  heading?: string
}

export default function EventsSection({ events, heading = 'Events happening nearby' }: EventsSectionProps) {
  if (!events.length) return null

  return (
    <section className="events-section" aria-labelledby="events-heading">
      <h2 id="events-heading" className="section-title">{heading}</h2>
      <div className="card-grid">
        {events.map((event, i) => (
          <EventCard key={i} event={event} index={i + 1} />
        ))}
      </div>
    </section>
  )
}
