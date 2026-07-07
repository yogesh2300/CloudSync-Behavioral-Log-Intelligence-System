import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Database } from 'lucide-react'

export default function DataTable({ columns, rows, emptyMessage = 'No data available.', keyField = 'id', expandable = true }) {
  const [expanded, setExpanded] = useState(null)

  if (!rows?.length) {
    return (
      <div className="py-14 text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border border-[#DADDD8] bg-white text-[#6F746F]">
          <Database className="h-5 w-5" />
        </div>
        <p className="text-sm muted-text">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto -mx-5 px-5">
      <table className="w-full border-separate border-spacing-y-2 text-sm">
        <thead className="sticky top-0 z-10">
          <tr>
            {expandable && <th className="w-8" />}
            {columns.map((col) => (
              <th
                key={col.key}
                className={`bg-white px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[#6F746F] first:rounded-l-2xl last:rounded-r-2xl ${col.className || ''}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <ExpandableRow
              key={row[keyField] ?? idx}
              row={row}
              idx={idx}
              columns={columns}
              expandable={expandable}
              isOpen={expanded === (row[keyField] ?? idx)}
              onToggle={() => setExpanded((current) => (current === (row[keyField] ?? idx) ? null : (row[keyField] ?? idx)))}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ExpandableRow({ row, idx, columns, expandable, isOpen, onToggle }) {
  return (
    <>
      <motion.tr
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: Math.min(idx * 0.015, 0.22) }}
        className="group"
      >
        {expandable && (
          <td className="rounded-l-2xl border-y border-l border-[#DADDD8] bg-white px-2">
            <button type="button" onClick={onToggle} className="rounded-lg p-1 text-[#6F746F] hover:bg-[#F0F1EF]" aria-label="Expand row">
              <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>
          </td>
        )}
        {columns.map((col, colIdx) => (
          <td
            key={col.key}
            className={`border-y border-[#DADDD8] bg-white px-3 py-3 text-[#111111] transition-all group-hover:bg-[#F7F8F6] ${!expandable && colIdx === 0 ? 'rounded-l-2xl border-l' : ''} ${colIdx === columns.length - 1 ? 'rounded-r-2xl border-r' : ''} ${col.className || ''}`}
          >
            {col.render ? col.render(row) : row[col.key]}
          </td>
        ))}
      </motion.tr>
      <AnimatePresence>
        {expandable && isOpen && (
          <motion.tr initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <td colSpan={columns.length + 1} className="px-2 pb-3">
              <pre className="max-h-72 overflow-auto rounded-3xl border border-[#DADDD8] bg-white p-4 text-xs text-[#111111] shadow-inner">
                {JSON.stringify(row, null, 2)}
              </pre>
            </td>
          </motion.tr>
        )}
      </AnimatePresence>
    </>
  )
}
