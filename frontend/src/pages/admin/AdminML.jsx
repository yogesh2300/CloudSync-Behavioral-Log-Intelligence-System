import { useCallback, useEffect, useState } from 'react'
import { getAdminML } from '../../api/adminClient'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { AdminCard, AdminMetric } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

export default function AdminML() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await getAdminML())
    } catch (err) {
      setData(null)
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load ML stats.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading && !data) return <LoadingSpinner label="Loading ML stats..." />
  if (error && !data) return <AdminError message={error} onRetry={load} />
  if (!data) return <AdminEmpty message="No ML data available." />

  const status = data.detection_status || {}

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <AdminMetric label="Training Dataset" value={data.training_dataset_size ?? 0} />
        <AdminMetric label="Total Predictions" value={data.total_predictions ?? 0} />
        <AdminMetric label="Anomalies" value={data.anomaly_count ?? 0} />
        <AdminMetric label="Avg Risk" value={data.average_risk_score ?? 0} />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <AdminCard title="Isolation Forest" subtitle={`Status: ${data.isolation_forest_status}`}>
          <p className="text-sm text-zinc-400">Unsupervised anomaly detection on normalized event features.</p>
        </AdminCard>
        <AdminCard title="Random Forest" subtitle={`Status: ${data.random_forest_status}`}>
          <p className="text-sm text-zinc-400">Supervised classification for suspicious vs normal behavior.</p>
        </AdminCard>
      </section>

      <AdminCard title="Detection Engine">
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div><dt className="text-zinc-500">Engine</dt><dd className="text-white">{status.engine || '—'}</dd></div>
          <div><dt className="text-zinc-500">Events in DB</dt><dd className="text-white">{status.events_in_db ?? 0}</dd></div>
          <div><dt className="text-zinc-500">Ready</dt><dd className="text-white">{status.ready ? 'Yes' : 'No'}</dd></div>
          <div><dt className="text-zinc-500">Last Activity</dt><dd className="text-white">{data.last_training_time ? new Date(data.last_training_time).toLocaleString() : 'N/A'}</dd></div>
          <div><dt className="text-zinc-500">Models</dt><dd className="text-white">{(status.models || []).join(', ') || '—'}</dd></div>
          <div><dt className="text-zinc-500">Alerts (from detection)</dt><dd className="text-white">{status.alerts?.total ?? 0}</dd></div>
        </dl>
      </AdminCard>
    </div>
  )
}
