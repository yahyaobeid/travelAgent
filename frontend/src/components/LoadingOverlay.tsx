interface LoadingOverlayProps {
  message?: string
}

export default function LoadingOverlay({ message = 'Generating your itinerary…' }: LoadingOverlayProps) {
  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-card">
        <div className="compass-ring" aria-hidden="true" />
        <p className="loading-message">{message}</p>
      </div>
    </div>
  )
}
