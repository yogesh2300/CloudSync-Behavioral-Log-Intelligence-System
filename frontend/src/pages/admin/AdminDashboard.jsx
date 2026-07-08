import { useCallback, useEffect, useState } from 'react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { getAdminDashboard } from '../../api/adminClient'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { AdminCard, AdminMetric } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

const CHART_COLORS = ['#71717a', '#a1a1aa', '#d4d4d8', '#52525b', '#3f3f46']
const TOOLTIP = {
  contentStyle: { background: '#18181b', border: '1px solid #27272a', borderRadius: 12, fontSize: 12 },
}

export default function AdminDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await getAdminDashboard())
    } catch (err) {
      setData(null)
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || err.message || 'Failed to load admin dashboard.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 30000)
    return () => clearInterval(id)
  }, [load])

  if (loading && !data) return <LoadingSpinner label="Loading admin dashboard..." />
  if (error && !data) return <AdminError message={error} onRetry={load} />

  const s = data?.summary || {}
  const c = data?.charts || {}
  const severityData = Object.entries(c.alert_severity || {}).map(([name, value]) => ({ name, value }))
  const riskData = Object.entries(c.risk_distribution || {}).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        <AdminMetric label="Total Users" value={s.total_users ?? 0} />
        <AdminMetric label="Active Users" value={s.active_users ?? 0} />
        <AdminMetric label="Total Servers" value={s.total_servers ?? 0} />
        <AdminMetric label="Online" value={s.online_servers ?? 0} />
        <AdminMetric label="Offline" value={s.offline_servers ?? 0} />
        <AdminMetric label="Availability" value={`${s.availability_pct ?? 0}%`} />
        <AdminMetric label="Total Events" value={s.total_events ?? 0} />
        <AdminMetric label="Events Today" value={s.events_today ?? 0} />
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        <AdminMetric label="Total Alerts" value={s.total_alerts ?? 0} />
        <AdminMetric label="Open Alerts" value={s.open_alerts ?? 0} />
        <AdminMetric label="Critical Alerts" value={s.critical_alerts ?? 0} />
        <AdminMetric label="Detections" value={s.total_detections ?? 0} />
        <AdminMetric label="ML Anomalies" value={s.ml_anomalies ?? 0} />
        <AdminMetric label="Collection Runs" value={s.collection_runs ?? 0} />
        <AdminMetric label="Success Rate" value={`${s.collection_success_rate ?? 0}%`} />
        <AdminMetric label="Avg Risk Score" value={s.average_risk_score ?? 0} />
      </section>

      {!s.total_events && !s.total_servers ? (
        <AdminEmpty message="No platform activity recorded yet. Data will appear after users register servers and collect logs." />
      ) : (
        <section className="grid gap-4 xl:grid-cols-2">
          <AdminCard title="User Registration Trend" subtitle="Last 30 days">
            {(c.user_registration_trend || []).length ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={c.user_registration_trend}>
                  <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                  <XAxis dataKey="day" tick={{ fill: '#71717a', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#71717a', fontSize: 10 }} width={32} />
                  <Tooltip {...TOOLTIP} />
                  <Area type="monotone" dataKey="count" stroke="#a1a1aa" fill="#27272a" />
                </AreaChart>
              </ResponsiveContainer>
            ) : <AdminEmpty message="No user registrations in the last 30 days." />}
          </AdminCard>

          <AdminCard title="Event Timeline" subtitle="Hourly activity (24h)">
            {(c.event_timeline || []).length ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={c.event_timeline}>
                  <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                  <XAxis dataKey="hour" tick={{ fill: '#71717a', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#71717a', fontSize: 10 }} width={32} />
                  <Tooltip {...TOOLTIP} />
                  <Line type="monotone" dataKey="count" stroke="#d4d4d8" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : <AdminEmpty message="No events in the last 24 hours." />}
          </AdminCard>

          <AdminCard title="Alert Severity">
            {severityData.length ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={severityData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={75}>
                    {severityData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Pie>
                  <Tooltip {...TOOLTIP} />
                </PieChart>
              </ResponsiveContainer>
            ) : <AdminEmpty message="No alerts recorded." />}
          </AdminCard>

          <AdminCard title="Risk Distribution">
            {riskData.length ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={riskData}>
                  <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fill: '#71717a', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#71717a', fontSize: 10 }} width={32} />
                  <Tooltip {...TOOLTIP} />
                  <Bar dataKey="value" fill="#52525b" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <AdminEmpty message="No risk data available." />}
          </AdminCard>

          <AdminCard title="Top Active Users">
            {(c.top_active_users || []).length ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={c.top_active_users} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis dataKey="username" type="category" width={80} tick={{ fill: '#71717a', fontSize: 10 }} />
                  <Tooltip {...TOOLTIP} />
                  <Bar dataKey="count" fill="#71717a" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <AdminEmpty message="No user activity yet." />}
          </AdminCard>

          <AdminCard title="Most Active Servers">
            {(c.most_active_servers || []).length ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={c.most_active_servers} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis dataKey="server" type="category" width={90} tick={{ fill: '#71717a', fontSize: 10 }} />
                  <Tooltip {...TOOLTIP} />
                  <Bar dataKey="events" fill="#52525b" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <AdminEmpty message="No server activity yet." />}
          </AdminCard>
        </section>
      )}
    </div>
  )
}
