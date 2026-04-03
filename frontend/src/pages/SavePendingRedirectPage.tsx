import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { savePending } from '../api/itineraries'

export default function SavePendingRedirectPage() {
  const navigate = useNavigate()

  useEffect(() => {
    savePending()
      .then((saved) => navigate(`/itineraries/${saved.id}`, { replace: true }))
      .catch(() => navigate('/itineraries/preview', { replace: true }))
  }, [navigate])

  return <div className="loading-screen"><div className="compass-ring" /></div>
}
