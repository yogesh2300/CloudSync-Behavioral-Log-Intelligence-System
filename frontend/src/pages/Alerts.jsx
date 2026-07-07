import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { AlertOctagon, CheckCircle2, Clock3, Fingerprint, ShieldAlert, UserCheck } from 'lucide-react'
import { acknowledgeAlert, getAlerts } from '../api/client'
import AlertBanner from '../components/ui/AlertBanner'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import PageHeader from '../components/ui/PageHeader'
import { SeverityBadge, StatusBadge } from '../components/ui/Badge'
import { Select } from '../components/ui/Input'

function AlertMetric({ label, value, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-[var(--panel-border)] bg-[var(--panel-strong)] p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-semibold uppercase tracking-wide muted-text">{label}</p>
        <Icon className="h-4 w-4 text-[#A5A5A5]" />
      </div>
      <p className="mt-2 text-2xl font-bold cyber-text">{value}</p>
    </div>
  )
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('open')
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { limit: 100 }
      if (filter === 'open') params.acknowledged = false
      if (filter === 'acked') params.acknowledged = true
      const rows = await getAlerts(params)
      const next = Array.isArray(rows) ? rows : []
      setAlerts(next)
      setSelected((current) => current || next[0]?.id || null)
    } catch (err) {
      setAlerts([])
      setError(err.response?.data?.error || err.response?.data?.detail || err.message || 'Failed to load alerts.')
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => {
    load()
    const id = setInterval(load, 20000)
    return () => clearInterval(id)
  }, [load])

  const selectedAlert = alerts.find((alert) => alert.id === selected) || alerts[0]
  const openCount = alerts.filter((alert) => !alert.acknowledged).length
  const criticalCount = alerts.filter((alert) => alert.severity === 'critical' || alert.severity === 'high').length
  const grouped = useMemo(() => ({
    priority: alerts.filter((alert) => alert.severity === 'critical' || alert.severity === 'high'),
    watch: alerts.filter((alert) => alert.severity !== 'critical' && alert.severity !== 'high'),
  }), [alerts])

  return (
    <div className="page-shell page-fill flex flex-col">
      <PageHeader
        title="Alerts"
        subtitle="Security Monitoring"
        actions={
          <>
            <Select value={filter} onChange={(event) => setFilter(event.target.value)} className="w-44">
              <option value="all">All alerts</option>
              <option value="open">Open only</option>
              <option value="acked">Acknowledged</option>
            </Select>
            <Button variant="secondary" onClick={load}>Refresh</Button>
          </>
        }
      />

      {error && <AlertBanner type="error" message={error} />}

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <AlertMetric label="Total Alerts" value={alerts.length} icon={ShieldAlert} />
        <AlertMetric label="Open" value={openCount} icon={AlertOctagon} />
        <AlertMetric label="Priority" value={criticalCount} icon={Fingerprint} />
        <AlertMetric label="Resolved" value={alerts.length - openCount} icon={CheckCircle2} />
      </section>

      <section className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(300px,1fr)]">
        <Card padding={false} className="flex min-h-[420px] flex-col overflow-hidden lg:max-h-[calc(100vh-13rem)]">
          <div className="shrink-0 border-b border-[var(--panel-border)] p-4">
            <h2 className="text-lg font-semibold cyber-text">Priority Board</h2>
            <p className="text-xs muted-text">Grouped alert cards</p>
          </div>
          {loading ? (
            <LoadingSpinner label="Loading alerts..." />
          ) : (
            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
              {[
                ['Priority', grouped.priority],
                ['Watch List', grouped.watch],
              ].map(([label, items]) => (
                <div key={label}>
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-semibold cyber-text">{label}</p>
                    <span className="rounded-full border border-[var(--panel-border)] px-2 py-0.5 text-[11px] muted-text">{items.length}</span>
                  </div>
                  <div className="space-y-2">
                    {items.map((alert, index) => (
                      <motion.button
                        key={alert.id}
                        type="button"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: Math.min(index * 0.02, 0.2) }}
                        onClick={() => setSelected(alert.id)}
                        className={`w-full rounded-2xl border p-3 text-left transition hover:-translate-y-0.5 ${
                          selectedAlert?.id === alert.id ? 'border-neutral-300 bg-[var(--panel-strong)]' : 'border-[var(--panel-border)] bg-[var(--panel)]'
                        }`}
                      >
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <div className="min-w-0">
                            <div className="mb-1.5 flex flex-wrap items-center gap-2">
                              <SeverityBadge severity={alert.severity} />
                              <StatusBadge status={alert.acknowledged ? 'online' : 'medium'}>{alert.acknowledged ? 'Resolved' : 'Open'}</StatusBadge>
                            </div>
                            <p className="text-sm font-semibold cyber-text">{alert.title}</p>
                            <p className="mt-0.5 line-clamp-2 text-xs muted-text">{alert.message}</p>
                          </div>
                          <span className="shrink-0 font-mono text-[10px] muted-text">{new Date(alert.created_at).toLocaleDateString()}</span>
                        </div>
                      </motion.button>
                    ))}
                    {!items.length && (
                      <div className="rounded-2xl border border-dashed border-[var(--panel-border)] bg-[var(--panel-strong)] p-6 text-center">
                        <ShieldAlert className="mx-auto mb-2 h-6 w-6 muted-text" />
                        <p className="text-sm muted-text">No alerts in this group.</p>
                        <p className="mt-1 text-[11px] muted-text">Alerts appear when detection or risk rules trigger.</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Investigation Panel" subtitle="Selected alert details" className="flex min-h-[420px] flex-col lg:max-h-[calc(100vh-13rem)]">
          {selectedAlert ? (
            <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto">
              <div>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <SeverityBadge severity={selectedAlert.severity} />
                  <StatusBadge status={selectedAlert.acknowledged ? 'online' : 'medium'}>{selectedAlert.acknowledged ? 'Resolved' : 'Open'}</StatusBadge>
                </div>
                <h2 className="text-xl font-semibold cyber-text">{selectedAlert.title}</h2>
                <p className="mt-2 text-sm leading-6 muted-text">{selectedAlert.message}</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-2xl border border-[var(--panel-border)] bg-[var(--panel-strong)] p-3">
                  <p className="text-[11px] muted-text">Risk Score</p>
                  <p className="mt-1 text-xl font-bold text-red-500">{selectedAlert.risk_score}</p>
                </div>
                <div className="rounded-2xl border border-[var(--panel-border)] bg-[var(--panel-strong)] p-3">
                  <p className="text-[11px] muted-text">Created</p>
                  <p className="mt-1 font-mono text-[11px] cyber-text">{new Date(selectedAlert.created_at).toLocaleString()}</p>
                </div>
              </div>
              <div className="space-y-2 border-l border-[var(--panel-border)] pl-3">
                {['Detected', 'Queued for review', selectedAlert.acknowledged ? 'Resolved' : 'Awaiting response'].map((item) => (
                  <div key={item} className="relative">
                    <span className="absolute -left-[17px] top-1.5 h-1.5 w-1.5 rounded-full bg-neutral-400" />
                    <p className="text-sm cyber-text">{item}</p>
                    <p className="text-[11px] muted-text">Security Monitoring</p>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" size="sm"><UserCheck className="h-4 w-4" /> Assign</Button>
                {!selectedAlert.acknowledged && (
                  <Button size="sm" onClick={() => acknowledgeAlert(selectedAlert.id).then(load)}>
                    <CheckCircle2 className="h-4 w-4" /> Resolve
                  </Button>
                )}
              </div>
              <pre className="max-h-48 overflow-auto rounded-2xl border border-[var(--panel-border)] bg-slate-950/80 p-3 text-xs text-slate-200">
                {JSON.stringify(selectedAlert, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center py-8 text-center">
              <Clock3 className="mb-3 h-8 w-8 muted-text" />
              <p className="text-sm font-medium cyber-text">No alert selected</p>
              <p className="mt-1 text-xs muted-text">Select an alert from the board to inspect details.</p>
            </div>
          )}
        </Card>
      </section>
    </div>
  )
}
