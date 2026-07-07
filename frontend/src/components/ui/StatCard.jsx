import CountUp from 'react-countup'
import { motion } from 'framer-motion'

const ACCENTS = {
  neutral: { ring: 'border-neutral-400/20', icon: 'text-neutral-300', line: '#D4D4D4' },
  red: { ring: 'border-red-400/20', icon: 'text-red-300', line: '#B76E79' },
  amber: { ring: 'border-amber-400/20', icon: 'text-amber-300', line: '#B89B5E' },
  emerald: { ring: 'border-emerald-400/20', icon: 'text-emerald-300', line: '#6EA779' },
  slate: { ring: 'border-slate-400/15', icon: 'text-slate-400', line: '#64748B' },
}

function Sparkline({ color }) {
  return (
    <svg className="h-8 w-24 opacity-80" viewBox="0 0 100 34" fill="none">
      <path d="M2 26 C15 8 24 18 34 15 C45 11 48 3 60 9 C70 14 75 27 98 7" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      <path d="M2 26 C15 8 24 18 34 15 C45 11 48 3 60 9 C70 14 75 27 98 7 V34 H2 Z" fill={color} opacity="0.08" />
    </svg>
  )
}

function displayValue(value) {
  const numeric = Number(value)
  if (Number.isFinite(numeric) && String(value).trim() !== '') {
    return <CountUp end={numeric} duration={1.1} separator="," preserveValue />
  }
  return value ?? '-'
}

export default function StatCard({ label, value, icon: Icon, accent = 'neutral', subtext, trend = '+12.4%' }) {
  const a = ACCENTS[accent] || ACCENTS.neutral
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className={`cyber-card rounded-xl border ${a.ring} p-5 min-h-[132px]`}
    >
      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide muted-text">{label}</p>
          <p className="mt-2 text-3xl font-bold cyber-text tabular-nums truncate">{displayValue(value)}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className="rounded-full bg-neutral-400/10 px-2 py-0.5 text-[10px] font-semibold text-neutral-300">{trend}</span>
            {subtext && <span className="text-xs muted-text truncate">{subtext}</span>}
          </div>
        </div>
        {Icon && (
          <div className={`shrink-0 p-2.5 rounded-xl bg-[var(--panel-strong)] border border-[var(--panel-border)] ${a.icon}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      <div className="relative mt-2 flex justify-end"><Sparkline color={a.line} /></div>
    </motion.div>
  )
}
