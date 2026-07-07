const STYLES = {
  critical: 'bg-red-500/10 text-red-400 border-red-500/20',
  high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  low: 'bg-[#F0F1EF] text-[#6F746F] border-[#DADDD8]',
  normal: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  info: 'bg-[#F0F1EF] text-[#6F746F] border-[#DADDD8]',
  online: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  offline: 'bg-red-500/10 text-red-400 border-red-500/20',
  inactive: 'bg-[#F0F1EF] text-[#6F746F] border-[#DADDD8]',
  error: 'bg-red-500/10 text-red-400 border-red-500/20',
  default: 'bg-[#F0F1EF] text-[#6F746F] border-[#DADDD8]',
}

export default function Badge({ children, variant = 'default', className = '' }) {
  const key = (children || variant || 'default').toString().toLowerCase()
  const style = STYLES[key] || STYLES[variant] || STYLES.default
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${style} ${className}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children}
    </span>
  )
}

export function SeverityBadge({ severity }) {
  return <Badge variant={severity}>{severity}</Badge>
}

export function StatusBadge({ status, children }) {
  return <Badge variant={status}>{children || status}</Badge>
}
