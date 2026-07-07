const VARIANTS = {
  primary: 'bg-[#111111] text-white hover:bg-[#2A2A2A] border border-[#111111] shadow-sm',
  secondary: 'bg-white text-[#111111] border border-[#DADDD8] hover:bg-[#F2F3F1]',
  danger: 'bg-[#9F5F68] hover:bg-[#884F57] text-white border border-[#9F5F68] shadow-sm',
  ghost: 'bg-transparent text-[#111111] border border-transparent hover:bg-white',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-sm',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled,
  ...props
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:-translate-y-0.5 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-neutral-400/40 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
