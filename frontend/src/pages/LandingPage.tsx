import { Link } from 'react-router-dom'
import { ArrowRight, Hand, Mic, Video } from 'lucide-react'

export function LandingPage() {
  return (
    <div className="land">
      {/* Ambient glow orbs */}
      <div className="land__orb land__orb--1" aria-hidden="true" />
      <div className="land__orb land__orb--2" aria-hidden="true" />

      {/* Nav */}
      <nav className="land__nav">
        <div className="land__logo">
          <span className="land__logo-mark">SB</span>
          <span className="land__logo-name">SignBridge</span>
        </div>
        <Link to="/login" className="land__nav-cta">Sign in</Link>
      </nav>

      {/* Hero */}
      <main className="land__hero">
        <div className="land__badge">
          <span className="land__badge-dot" />
          Real-time · Sign Language · AI Captions
        </div>

        <h1 className="land__headline">
          Meetings where<br />
          <span className="land__headline-em">every voice counts.</span>
        </h1>

        <p className="land__sub">
          Premium video meetings with built-in sign-language intelligence.<br />
          No plugins. No friction. Just connect.
        </p>

        <div className="land__actions">
          <Link to="/login" className="land__btn-primary">
            Start a meeting
            <ArrowRight size={16} />
          </Link>
          <Link to="/login" className="land__btn-ghost">
            Join with a code
          </Link>
        </div>

        {/* Feature pills */}
        <div className="land__pills">
          <span className="land__pill"><Video size={13} /> HD Video</span>
          <span className="land__pill"><Mic size={13} /> Crystal audio</span>
          <span className="land__pill"><Hand size={13} /> Sign language AI</span>
        </div>
      </main>

      {/* Bottom fade */}
      <div className="land__fade" aria-hidden="true" />
    </div>
  )
}
