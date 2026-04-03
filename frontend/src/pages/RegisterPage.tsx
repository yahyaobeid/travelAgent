import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/'

  const [username, setUsername] = useState('')
  const [password1, setPassword1] = useState('')
  const [password2, setPassword2] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      await register(username, password1, password2)
      navigate(next, { replace: true })
    } catch (err: unknown) {
      const data = (err as { response?: { data?: { errors?: Record<string, string[]> } } })?.response?.data
      setErrors(data?.errors ?? { __all__: ['Registration failed. Please try again.'] })
    } finally {
      setLoading(false)
    }
  }

  const fieldError = (field: string) => errors[field]?.join(' ')

  return (
    <div className="form-page">
      <div className="form-card">
        <h1 className="form-title">Create account</h1>

        {errors.__all__ && <div className="form-error" role="alert">{fieldError('__all__')}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            {fieldError('username') && <span className="field-error">{fieldError('username')}</span>}
          </div>
          <div className="form-group">
            <label htmlFor="password1">Password</label>
            <input
              id="password1"
              type="password"
              autoComplete="new-password"
              value={password1}
              onChange={(e) => setPassword1(e.target.value)}
              required
            />
            {fieldError('password1') && <span className="field-error">{fieldError('password1')}</span>}
          </div>
          <div className="form-group">
            <label htmlFor="password2">Confirm password</label>
            <input
              id="password2"
              type="password"
              autoComplete="new-password"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              required
            />
            {fieldError('password2') && <span className="field-error">{fieldError('password2')}</span>}
          </div>
          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="form-footer">
          Already have an account? <Link to={`/login?next=${encodeURIComponent(next)}`}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
