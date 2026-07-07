export default function LoadingSpinner({ label = 'Loading...', fullScreen = false }) {
  const content = (
    <div className="w-full max-w-3xl space-y-4">
      {label && <p className="text-sm muted-text">{label}</p>}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="skeleton h-28 rounded-xl border border-[var(--panel-border)]" />
        <div className="skeleton h-28 rounded-xl border border-[var(--panel-border)]" />
        <div className="skeleton h-28 rounded-xl border border-[var(--panel-border)]" />
      </div>
      <div className="skeleton h-64 rounded-xl border border-[var(--panel-border)]" />
    </div>
  )

  if (fullScreen) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 grid-bg">
        {content}
      </div>
    )
  }

  return <div className="py-16 flex justify-center">{content}</div>
}
