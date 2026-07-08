import Button from '../ui/Button'

export function AdminEmpty({ message = 'No data available yet.' }) {
  return (
    <div className="rounded-xl border border-dashed border-zinc-700 px-6 py-12 text-center text-sm text-zinc-500">
      {message}
    </div>
  )
}

export function AdminError({ message, onRetry }) {
  return (
    <div className="rounded-xl border border-red-900/50 bg-red-950/20 px-6 py-8 text-center">
      <p className="text-sm text-red-300">{message || 'Failed to load data.'}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  )
}
