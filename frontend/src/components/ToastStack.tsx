interface ToastItem {
  id: string
  message: string
}

interface ToastStackProps {
  items: ToastItem[]
}

export function ToastStack({ items }: ToastStackProps) {
  if (!items.length) {
    return null
  }

  return (
    <div className="toast-stack" aria-live="polite" aria-atomic="true">
      {items.map((item) => (
        <article key={item.id} className="toast-card">
          {item.message}
        </article>
      ))}
    </div>
  )
}
