import { FormEvent, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useAppContext } from '../contexts/AppContext'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAppContext()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const redirectPath = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!name.trim()) return
    login({ displayName: name.trim(), email: email.trim() || undefined, guest: !email.trim() })
    navigate(redirectPath, { replace: true })
  }

  return (
    <div className="auth">
      <div className="auth__orb" aria-hidden="true" />

      <div className="auth__card">
        <Link to="/" className="auth__logo">
          <span className="auth__logo-mark">SB</span>
          <span className="auth__logo-name">SignBridge</span>
        </Link>

        <h1 className="auth__title">Get started</h1>
        <p className="auth__sub">Enter your name to join or host a meeting. No account required.</p>

        <form className="auth__form" onSubmit={handleSubmit}>
          <div className="auth__field">
            <label className="auth__label" htmlFor="auth-name">Display name</label>
            <input
              id="auth-name"
              className="auth__input"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Your name"
              autoFocus
              required
            />
          </div>

          <div className="auth__field">
            <label className="auth__label" htmlFor="auth-email">
              Email <span className="auth__optional">(optional)</span>
            </label>
            <input
              id="auth-email"
              className="auth__input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>

          <button type="submit" className="auth__submit" disabled={!name.trim()}>
            Continue
            <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  )
}
