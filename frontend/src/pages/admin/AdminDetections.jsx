import { useCallback, useEffect, useState } from 'react'
import { getAdminDetections, getAdminDetectionStatus } from '../../api/adminClient'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { AdminCard, AdminMetric } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

export default function AdminDetections() {
  const [items, setItems] = useState([])
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [d, s] = await Promise.all([getAdminDetections(200), getAdminDetectionStatus()])
      setItems(Array.isArray(d) ? d : [])
      setStatus(s)
    } catch (err) {
      setItems([])
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load detections.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading && !items.length) return <LoadingSpinner label="Loading detections..." />
  if (error && !items.length) return <AdminError message={error} onRetry={load} />

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <AdminMetric label="Events in DB" value={status?.events_in_db ?? status?.events_analyzed ?? 0} />
        <AdminMetric label="Total Detections" value={status?.total_detections ?? items.length} />
        <AdminMetric label="ML Anomalies" value={status?.ml_anomalies ?? 0} />
        <AdminMetric label="Engine Ready" value={status?.ready ? 'Yes' : 'No'} />
      </section>

      {!items.length ? (
        <AdminEmpty message="No detections recorded. Run detection from the analyst panel after collecting events." />
      ) : (
        <AdminCard title="Detection Results" subtitle="All stored ML predictions">
          <div className="overflow-x-auto">
            <table className="admin-table w-full text-sm">
              <thead>
                <tr>
                  {['Prediction', 'Confidence', 'Model', 'Risk', 'Timestamp', 'Server', 'User', 'Event'].map((h) => (
                    <th key={h} className="px-3 py-2 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id || item.event_id}>
                    <td className="px-3 py-2 text-white">{item.prediction || item.classification || '—'}</td>
                    <td className="px-3 py-2">{item.confidence != null ? item.confidence.toFixed(3) : (item.anomaly_score != null ? item.anomaly_score.toFixed(3) : '—')}</td>
                    <td className="px-3 py-2">{item.model || item.detection_type || '—'}</td>
                    <td className="px-3 py-2">{item.risk_score}</td>
                    <td className="px-3 py-2 text-xs text-zinc-500">{item.timestamp ? new Date(item.timestamp).toLocaleString() : '—'}</td>
                    <td className="px-3 py-2">{item.server_name || '—'}</td>
                    <td className="px-3 py-2">{item.owner_username || item.username || '—'}</td>
                    <td className="px-3 py-2">{item.event_type || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </AdminCard>
      )}
    </div>
  )
}
