import { AdminCard } from '../../components/admin/AdminLayout'

export default function AdminSettings() {
  return (
    <div className="space-y-6 max-w-2xl">
      <AdminCard title="Platform Settings" subtitle="Admin configuration (read-only overview)">
        <dl className="space-y-4 text-sm">
          {[
            ['Platform', 'DefenSync Security Monitoring'],
            ['Admin Console', 'Enabled'],
            ['Health Check Interval', '30 seconds'],
            ['Default User Role', 'ANALYST'],
            ['Owner Isolation', 'Enabled for analysts'],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between border-b border-zinc-800 pb-3">
              <dt className="text-zinc-500">{label}</dt>
              <dd className="text-white">{value}</dd>
            </div>
          ))}
        </dl>
      </AdminCard>
      <AdminCard title="About">
        <p className="text-sm text-zinc-400">
          The Admin Console provides global visibility across all users, servers, events, alerts, and detections.
          Analyst users continue to access the standard dashboard with owner-scoped data only.
        </p>
      </AdminCard>
    </div>
  )
}
