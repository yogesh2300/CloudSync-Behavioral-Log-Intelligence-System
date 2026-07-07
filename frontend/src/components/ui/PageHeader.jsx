import { motion } from 'framer-motion'

export default function PageHeader({ title, subtitle, actions, badge }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="relative">
        <div className="absolute -left-4 top-1 h-12 w-1 rounded-full bg-[#111111]" />
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight cyber-text">{title}</h1>
          {badge}
        </div>
        {subtitle && <p className="mt-2 max-w-3xl text-sm muted-text">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </motion.div>
  )
}
