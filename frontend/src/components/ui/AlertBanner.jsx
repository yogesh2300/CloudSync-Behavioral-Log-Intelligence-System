export default function AlertBanner({ message, type = 'info', onDismiss }) {
  if (!message) return null
  const styles = {
    success: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
    error: 'bg-red-500/10 border-red-500/30 text-red-300',
    info: 'bg-neutral-500/10 border-neutral-500/30 text-neutral-300',
    warning: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
  }
  const resolved = message.includes('success') || message.includes('OK') || message.includes('verified')
    ? 'success'
    : message.includes('fail') || message.includes('error')
      ? 'error'
      : type

  return (
    <div className={`mb-4 px-4 py-3 rounded-lg border text-sm flex items-start justify-between gap-3 ${styles[resolved]}`}>
      <span>{typeof message === 'string' ? message : JSON.stringify(message)}</span>
      {onDismiss && (
        <button type="button" onClick={onDismiss} className="opacity-60 hover:opacity-100">×</button>
      )}
    </div>
  )
}
