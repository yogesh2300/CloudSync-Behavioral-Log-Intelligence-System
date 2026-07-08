import { useCallback, useEffect, useState } from 'react'
import { getAdminCollections } from '../../api/adminClient'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { AdminCard } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

export default function AdminCollections() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setRuns(await getAdminCollections(200))
    } catch (err) {
      setRuns([])
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load collections.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading && !runs.length) return <LoadingSpinner label="Loading collections..." />
  if (error && !runs.length) return <AdminError message={error} onRetry={load} />

  return (
    <AdminCard title="Collection Runs" subtitle="Global log collection history">
      {!runs.length ? (
        <AdminEmpty message="No collection runs recorded yet." />
      ) : (
        <div className="overflow-x-auto">
          <table className="admin-table w-full text-sm">
            <thead>
              <tr>
                {['Run Time', 'Owner', 'Server', 'Duration', 'Status', 'Events Collected', 'Errors', 'Message'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td className="px-3 py-3 text-xs">{r.started_at ? new Date(r.started_at).toLocaleString() : '—'}</td>
                  <td className="px-3 py-3">{r.owner_username || '—'}</td>
                  <td className="px-3 py-3 text-white">{r.server_name}</td>
                  <td className="px-3 py-3">{r.duration_ms ? `${r.duration_ms}ms` : '—'}</td>
                  <td className="px-3 py-3">{r.status}</td>
                  <td className="px-3 py-3">{r.events_collected ?? r.inserted ?? 0}</td>
                  <td className="px-3 py-3">{r.errors ?? r.failed ?? 0}</td>
                  <td className="max-w-xs truncate px-3 py-3 text-xs text-zinc-500">{r.error_message || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminCard>
  )
}
