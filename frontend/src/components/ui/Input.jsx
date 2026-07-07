export function Input({ label, className = '', ...props }) {
  return (
    <div className="space-y-2">
      {label && <label className="block text-xs font-semibold muted-text">{label}</label>}
      <input
        className={`w-full rounded-full border border-[#DADDD8] bg-white px-4 py-3 text-sm text-[#111111] placeholder-[#9A9F9A] outline-none transition-all duration-200 focus:border-[#111111] focus:ring-4 focus:ring-black/5 ${className}`}
        {...props}
      />
    </div>
  )
}

export function Select({ label, children, className = '', ...props }) {
  return (
    <div className="space-y-2">
      {label && <label className="block text-xs font-semibold muted-text">{label}</label>}
      <select
        className={`w-full rounded-full border border-[#DADDD8] bg-white px-4 py-3 text-sm text-[#111111] outline-none transition-all duration-200 focus:border-[#111111] focus:ring-4 focus:ring-black/5 ${className}`}
        {...props}
      >
        {children}
      </select>
    </div>
  )
}

export function Textarea({ label, className = '', ...props }) {
  return (
    <div className="space-y-2">
      {label && <label className="block text-xs font-semibold muted-text">{label}</label>}
      <textarea
        className={`w-full min-h-[100px] resize-y rounded-[1.5rem] border border-[#DADDD8] bg-white px-4 py-3 font-mono text-xs text-[#111111] placeholder-[#9A9F9A] outline-none transition-all duration-200 focus:border-[#111111] focus:ring-4 focus:ring-black/5 ${className}`}
        {...props}
      />
    </div>
  )
}
