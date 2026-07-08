import { useCallback, useEffect, useMemo, useState } from 'react'
import { getAdminAlerts, getAdminAlertSummary } from '../../api/adminClient'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { SeverityBadge } from '../../components/ui/Badge'
import { AdminCard, AdminMetric } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

export default function AdminAlerts() {
  const [alerts, setAlerts] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [a, s] = await Promise.all([getAdminAlerts({ limit: 500 }), getAdminAlertSummary()])
      setAlerts(Array.isArray(a) ? a : [])
      setSummary(s)
    } catch (err) {
      setAlerts([])
      setSummary(null)
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load alerts.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const grouped = useMemo(() => {
    const order = ['critical', 'high', 'medium', 'low', 'info']
    const map = {}
    order.forEach((s) => { map[s] = [] })
    alerts.forEach((a) => {
      const key = (a.severity || 'info').toLowerCase()
      if (!map[key]) map[key] = []
      map[key].push(a)
    })
    return order.map((severity) => ({ severity, items: map[severity] || [] })).filter((g) => g.items.length)
  }, [alerts])

  if (loading && !alerts.length) return <LoadingSpinner label="Loading alerts..." />
  if (error && !alerts.length) return <AdminError message={error} onRetry={load} />

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <AdminMetric label="Total" value={summary?.total ?? 0} />
        <AdminMetric label="Open" value={summary?.unacknowledged ?? 0} />
        <AdminMetric label="Critical" value={summary?.critical ?? 0} />
        <AdminMetric label="ML Anomaly" value={summary?.ml_anomaly ?? 0} />
        <AdminMetric label="Rule Based" value={summary?.rule_based ?? 0} />
      </section>

      {!grouped.length ? (
        <AdminEmpty message="No alerts in the database yet." />
      ) : (
        grouped.map(({ severity, items }) => (
          <AdminCard key={severity} title={`${severity.toUpperCase()} Alerts`} subtitle={`${items.length} alerts`}>
            <div className="overflow-x-auto">
              <table className="admin-table w-full text-sm">
                <thead>
                  <tr>
                    {['Severity', 'Server', 'User', 'Alert Time', 'Status', 'Risk', 'Description'].map((h) => (
                      <th key={h} className="px-3 py-2 text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((a) => (
                    <tr key={a.id}>
                      <td className="px-3 py-2"><SeverityBadge severity={a.severity} /></td>
                      <td className="px-3 py-2">{a.server_name || '—'}</td>
                      <td className="px-3 py-2">{a.owner_username || '—'}</td>
                      <td className="px-3 py-2 text-xs text-zinc-500">{a.created_at ? new Date(a.created_at).toLocaleString() : '—'}</td>
                      <td className="px-3 py-2 capitalize">{a.status || (a.acknowledged ? 'resolved' : 'open')}</td>
                      <td className="px-3 py-2">{a.risk_score}</td>
                      <td className="max-w-md px-3 py-2">
                        <p className="font-medium text-white">{a.title}</p>
                        <p className="truncate text-xs text-zinc-500">{a.message}</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AdminCard>
        ))
      )}
    </div>
  )
}
