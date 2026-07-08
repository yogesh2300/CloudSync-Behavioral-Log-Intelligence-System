import { useCallback, useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getAdminAnalytics } from '../../api/adminClient'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { AdminCard, AdminMetric } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

const TOOLTIP = { contentStyle: { background: '#18181b', border: '1px solid #27272a', borderRadius: 12 } }

export default function AdminAnalytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await getAdminAnalytics())
    } catch (err) {
      setData(null)
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load analytics.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading && !data) return <LoadingSpinner label="Loading analytics..." />
  if (error && !data) return <AdminError message={error} onRetry={load} />
  if (!data) return <AdminEmpty message="No analytics data available." />

  const severityChart = Object.entries(data.events_by_severity || {}).map(([name, value]) => ({ name, value }))
  const typeChart = Object.entries(data.events_by_type || {}).slice(0, 8).map(([name, value]) => ({ name, value }))
  const detectionChart = Object.entries(data.detection_distribution || {}).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <AdminMetric label="Event Types" value={Object.keys(data.events_by_type || {}).length} />
        <AdminMetric label="Alert Titles" value={data.most_frequent_alerts?.length ?? 0} />
        <AdminMetric label="Top Servers" value={data.top_risk_servers?.length ?? 0} />
        <AdminMetric label="Detections" value={Object.values(data.detection_distribution || {}).reduce((a, b) => a + b, 0)} />
      </section>

      <div className="grid gap-4 xl:grid-cols-2">
        <AdminCard title="Events by Day">
          {(data.events_by_day || []).length ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.events_by_day}>
                <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fill: '#71717a', fontSize: 10 }} />
                <YAxis tick={{ fill: '#71717a', fontSize: 10 }} width={32} />
                <Tooltip {...TOOLTIP} />
                <Line type="monotone" dataKey="count" stroke="#a1a1aa" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <AdminEmpty message="No events recorded in the last 30 days." />}
        </AdminCard>

        <AdminCard title="Alerts Trend">
          {(data.alerts_trend || []).length ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.alerts_trend}>
                <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fill: '#71717a', fontSize: 10 }} />
                <YAxis tick={{ fill: '#71717a', fontSize: 10 }} width={32} />
                <Tooltip {...TOOLTIP} />
                <Line type="monotone" dataKey="count" stroke="#d4d4d8" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <AdminEmpty message="No alerts in the last 30 days." />}
        </AdminCard>

        <AdminCard title="Events by Severity">
          {severityChart.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={severityChart}>
                <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: '#71717a', fontSize: 10 }} />
                <YAxis tick={{ fill: '#71717a', fontSize: 10 }} width={32} />
                <Tooltip {...TOOLTIP} />
                <Bar dataKey="value" fill="#52525b" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <AdminEmpty message="No severity breakdown available." />}
        </AdminCard>

        <AdminCard title="Events by Type">
          {typeChart.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={typeChart} layout="vertical">
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#71717a', fontSize: 10 }} />
                <Tooltip {...TOOLTIP} />
                <Bar dataKey="value" fill="#71717a" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <AdminEmpty message="No event types recorded." />}
        </AdminCard>

        <AdminCard title="Detection Distribution">
          {detectionChart.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={detectionChart}>
                <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: '#71717a', fontSize: 10 }} />
                <YAxis tick={{ fill: '#71717a', fontSize: 10 }} width={32} />
                <Tooltip {...TOOLTIP} />
                <Bar dataKey="value" fill="#a1a1aa" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <AdminEmpty message="No detections recorded." />}
        </AdminCard>

        <AdminCard title="Top Risk Servers">
          {(data.top_risk_servers || []).length ? (
            <div className="space-y-2">
              {data.top_risk_servers.map((s) => (
                <div key={s.server} className="flex justify-between rounded-lg border border-zinc-800 px-3 py-2 text-sm">
                  <span className="text-white">{s.server}</span>
                  <span className="text-zinc-500">Risk {s.avg_risk} · {s.events} events</span>
                </div>
              ))}
            </div>
          ) : <AdminEmpty message="No server risk data." />}
        </AdminCard>

        <AdminCard title="Top Risk Users">
          {(data.top_risk_users || []).length ? (
            <div className="space-y-2">
              {data.top_risk_users.map((u) => (
                <div key={u.username} className="flex justify-between rounded-lg border border-zinc-800 px-3 py-2 text-sm">
                  <span className="text-white">{u.username}</span>
                  <span className="text-zinc-500">Risk {u.avg_risk} · {u.events} events</span>
                </div>
              ))}
            </div>
          ) : <AdminEmpty message="No user activity data." />}
        </AdminCard>

        <AdminCard title="Most Frequent Alerts">
          {(data.most_frequent_alerts || []).length ? (
            <div className="space-y-2">
              {data.most_frequent_alerts.map((a) => (
                <div key={a.title} className="flex justify-between rounded-lg border border-zinc-800 px-3 py-2 text-sm">
                  <span className="text-white">{a.title}</span>
                  <span className="text-zinc-500">{a.count}</span>
                </div>
              ))}
            </div>
          ) : <AdminEmpty message="No alerts recorded." />}
        </AdminCard>
      </div>
    </div>
  )
}
