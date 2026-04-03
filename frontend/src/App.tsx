import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'

import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ItineraryFormPage from './pages/ItineraryFormPage'
import ItineraryPreviewPage from './pages/ItineraryPreviewPage'
import ItineraryDetailPage from './pages/ItineraryDetailPage'
import ItineraryDeletePage from './pages/ItineraryDeletePage'
import SavePendingRedirectPage from './pages/SavePendingRedirectPage'
import FlightSearchPage from './pages/FlightSearchPage'
import CarSearchPage from './pages/CarSearchPage'
import CarResultsPage from './pages/CarResultsPage'

function NotFound() {
  return (
    <div className="form-page">
      <div className="form-card" style={{ textAlign: 'center' }}>
        <h1 className="form-title">404</h1>
        <p>Page not found.</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/flights" element={<FlightSearchPage />} />
            <Route path="/cars" element={<CarSearchPage />} />

            <Route path="/itineraries/new" element={<ItineraryFormPage />} />
            <Route path="/itineraries/preview" element={<ItineraryPreviewPage />} />

            <Route
              path="/itineraries/save-redirect"
              element={
                <ProtectedRoute>
                  <SavePendingRedirectPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/itineraries/:pk"
              element={
                <ProtectedRoute>
                  <ItineraryDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/itineraries/:pk/edit"
              element={
                <ProtectedRoute>
                  <ItineraryFormPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/itineraries/:pk/delete"
              element={
                <ProtectedRoute>
                  <ItineraryDeletePage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/cars/:pk"
              element={
                <ProtectedRoute>
                  <CarResultsPage />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </AuthProvider>
    </BrowserRouter>
  )
}
