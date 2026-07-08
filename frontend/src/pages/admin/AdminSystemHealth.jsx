import { useCallback, useEffect, useState } from 'react'
import { getAdminSystemHealth } from '../../api/adminClient'
import { getHealth as getPlatformHealth } from '../../api/client'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { AdminCard, AdminMetric } from '../../components/admin/AdminLayout'
import { AdminError } from '../../components/admin/AdminPageState'

export default function AdminSystemHealth() {
  const [health, setHealth] = useState(null)
  const [platform, setPlatform] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [h, p] = await Promise.all([getAdminSystemHealth(), getPlatformHealth()])
      setHealth(h)
      setPlatform(p)
    } catch (err) {
      setHealth(null)
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load system health.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading && !health) return <LoadingSpinner label="Loading system health..." />
  if (error && !health) return <AdminError message={error} onRetry={load} />

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <AdminMetric label="Database" value={platform?.database || health?.database || 'unknown'} />
        <AdminMetric label="API" value={health?.api || health?.backend || 'healthy'} />
        <AdminMetric label="Collection Engine" value={health?.collection_engine || '—'} />
        <AdminMetric label="ML Engine" value={health?.ml_engine || '—'} />
      </section>
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <AdminMetric label="Connected Servers" value={health?.connected_servers ?? 0} />
        <AdminMetric label="Offline Servers" value={health?.offline_servers ?? 0} />
        <AdminMetric label="CPU Avg" value={`${health?.cpu_usage_avg ?? 0}%`} />
        <AdminMetric label="Memory Avg" value={`${health?.memory_usage_avg ?? 0}%`} />
      </section>
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <AdminMetric label="Disk Avg" value={`${health?.disk_usage_avg ?? 0}%`} />
        <AdminMetric label="Network Avg" value={health?.network_activity_avg ?? 0} />
        <AdminMetric label="SSH Latency" value={`${health?.average_ssh_latency_ms ?? 0}ms`} />
        <AdminMetric label="SSH Collector" value={health?.ssh_collector || 'healthy'} />
      </section>
      <AdminCard title="Platform Components">
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            ['Database', platform?.database || health?.database],
            ['Backend API', health?.api || health?.backend],
            ['Collection Engine', health?.collection_engine],
            ['ML Engine', health?.ml_engine],
            ['SSH Collector', health?.ssh_collector],
            ['Frontend', health?.frontend],
          ].map(([name, status]) => (
            <div key={name} className="flex items-center justify-between rounded-lg border border-zinc-800 px-4 py-3">
              <span className="text-white">{name}</span>
              <span className="text-xs uppercase text-emerald-400">{status || 'unknown'}</span>
            </div>
          ))}
        </div>
      </AdminCard>
    </div>
  )
}
