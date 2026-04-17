import type { ReactNode } from 'react'

interface PanelCardProps {
  title: string
  eyebrow?: string
  actions?: ReactNode
  children: ReactNode
}

export function PanelCard({ title, eyebrow, actions, children }: PanelCardProps) {
  return (
    <section className="panel-card">
      <header className="panel-card__header">
        <div>
          {eyebrow ? <p className="panel-card__eyebrow">{eyebrow}</p> : null}
          <h2>{title}</h2>
        </div>
        {actions}
      </header>
      <div className="panel-card__body">{children}</div>
    </section>
  )
}

