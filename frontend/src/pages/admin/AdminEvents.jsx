import { useCallback, useEffect, useState } from 'react'
import { getAdminEvents, getAdminServers, getAdminUsers } from '../../api/adminClient'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { Input, Select } from '../../components/ui/Input'
import { SeverityBadge } from '../../components/ui/Badge'
import { AdminCard } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

export default function AdminEvents() {
  const [events, setEvents] = useState([])
  const [total, setTotal] = useState(0)
  const [servers, setServers] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [severity, setSeverity] = useState('')
  const [eventType, setEventType] = useState('')
  const [serverId, setServerId] = useState('')
  const [ownerId, setOwnerId] = useState('')

  useEffect(() => {
    Promise.all([
      getAdminServers().catch(() => []),
      getAdminUsers().catch(() => ({ items: [] })),
    ]).then(([s, u]) => {
      setServers(Array.isArray(s) ? s : [])
      setUsers(u.items || [])
    })
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { limit: 500 }
      if (search) params.search = search
      if (severity) params.severity = severity
      if (eventType) params.event_type = eventType
      if (serverId) params.server_id = serverId
      if (ownerId) params.owner_id = ownerId
      const data = await getAdminEvents(params)
      setEvents(data.items || [])
      setTotal(data.total ?? (data.items || []).length)
    } catch (err) {
      setEvents([])
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load events.')
    } finally {
      setLoading(false)
    }
  }, [search, severity, eventType, serverId, ownerId])

  useEffect(() => { load() }, [load])

  const exportCsv = () => {
    const header = 'timestamp,event_type,severity,username,hostname,message\n'
    const rows = events.map((e) =>
      [e.timestamp, e.event_type, e.severity, e.username, e.hostname, `"${(e.message || '').replace(/"/g, '""')}"`].join(',')
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'defensync-events.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading && !events.length) return <LoadingSpinner label="Loading events..." />
  if (error && !events.length) return <AdminError message={error} onRetry={load} />

  return (
    <AdminCard title="Event Management" subtitle={`${total.toLocaleString()} total events`}>
      <div className="mb-4 flex flex-wrap gap-3">
        <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs bg-zinc-900 border-zinc-700 text-white" />
        <Select value={severity} onChange={(e) => setSeverity(e.target.value)} className="bg-zinc-900 border-zinc-700 text-white">
          <option value="">All severities</option>
          {['critical', 'high', 'medium', 'low', 'info'].map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Input placeholder="Event type" value={eventType} onChange={(e) => setEventType(e.target.value)} className="max-w-[160px] bg-zinc-900 border-zinc-700 text-white" />
        <Select value={serverId} onChange={(e) => setServerId(e.target.value)} className="bg-zinc-900 border-zinc-700 text-white">
          <option value="">All servers</option>
          {servers.map((s) => <option key={s.id} value={s.id}>{s.server_name}</option>)}
        </Select>
        <Select value={ownerId} onChange={(e) => setOwnerId(e.target.value)} className="bg-zinc-900 border-zinc-700 text-white">
          <option value="">All users</option>
          {users.map((u) => <option key={u.id} value={u.id}>{u.username}</option>)}
        </Select>
        <Button variant="secondary" onClick={load}>Filter</Button>
        <Button variant="secondary" onClick={exportCsv} disabled={!events.length}>Export CSV</Button>
      </div>
      {!events.length ? (
        <AdminEmpty message="No events match the current filters." />
      ) : (
        <div className="max-h-[600px] overflow-y-auto">
          <table className="admin-table w-full text-sm">
            <thead className="sticky top-0 bg-[#111113]">
              <tr>
                {['Time', 'Type', 'Severity', 'User', 'Host', 'Risk', 'Message'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.event_id || e.id}>
                  <td className="px-3 py-2 text-xs text-zinc-500">{e.timestamp ? new Date(e.timestamp).toLocaleString() : '—'}</td>
                  <td className="px-3 py-2">{e.event_type}</td>
                  <td className="px-3 py-2"><SeverityBadge severity={e.severity} /></td>
                  <td className="px-3 py-2">{e.username || '—'}</td>
                  <td className="px-3 py-2">{e.hostname}</td>
                  <td className="px-3 py-2">{e.risk_score}</td>
                  <td className="max-w-md truncate px-3 py-2">{e.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminCard>
  )
}
