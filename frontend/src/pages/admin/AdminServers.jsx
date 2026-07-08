import { useCallback, useEffect, useState } from 'react'
import { getAdminServers } from '../../api/adminClient'
import { collectServer, deleteServer, testServerConnection } from '../../api/client'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { HealthBadge } from '../../components/ui/Badge'
import { AdminCard } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

export default function AdminServers() {
  const [servers, setServers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setServers(await getAdminServers())
    } catch (err) {
      setServers([])
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load servers.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const run = async (id, fn) => {
    setBusy(id)
    try { await fn(); await load() } finally { setBusy(null) }
  }

  if (loading && !servers.length) return <LoadingSpinner label="Loading servers..." />
  if (error && !servers.length) return <AdminError message={error} onRetry={load} />

  return (
    <AdminCard title="Server Management" subtitle="All registered servers across the platform">
      {!servers.length ? (
        <AdminEmpty message="No servers registered yet." />
      ) : (
        <div className="overflow-x-auto">
          <table className="admin-table w-full text-sm text-zinc-300">
            <thead>
              <tr>
                {['Hostname', 'Owner', 'OS', 'IP', 'Status', 'Last Seen', 'Collection', 'Events', 'Actions'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {servers.map((s) => (
                <tr key={s.id}>
                  <td className="px-3 py-3 text-white">{s.server_name}</td>
                  <td className="px-3 py-3">{s.owner_username || '—'}</td>
                  <td className="px-3 py-3">{s.operating_system || 'linux'}</td>
                  <td className="px-3 py-3 font-mono text-xs">{s.host}:{s.port}</td>
                  <td className="px-3 py-3"><HealthBadge healthStatus={s.health_status}>{s.connection_state}</HealthBadge></td>
                  <td className="px-3 py-3 text-xs">{s.last_seen ? new Date(s.last_seen).toLocaleString() : 'Never'}</td>
                  <td className="px-3 py-3">{s.last_collection_status || '—'}</td>
                  <td className="px-3 py-3">{s.events_count ?? 0}</td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      <Button size="sm" variant="secondary" disabled={busy === s.id} onClick={() => run(s.id, () => testServerConnection(s.id))}>Test</Button>
                      <Button size="sm" variant="primary" disabled={busy === s.id} onClick={() => run(s.id, () => collectServer(s.id, { tail_lines: 200 }))}>Collect</Button>
                      <Button size="sm" variant="danger" disabled={busy === s.id} onClick={() => run(s.id, () => deleteServer(s.id))}>Delete</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminCard>
  )
}
