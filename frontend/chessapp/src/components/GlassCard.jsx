function GlassCard({
  children,
  className = '',
  centered = false,
  style = {},
}) {
  return (
    <div
      className={`
        card
        bg-dark
        bg-opacity-55
        text-white
        border
        border-white
        border-opacity-10
        rounded-4
        p-4
        h-100
        ${centered ? 'text-center' : ''}
        ${className}
      `}
      style={{
        boxShadow:
          '0 20px 80px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255,255,255,0.04)',
        ...style,
      }}
    >
      {children}
    </div>
  )
}

export default GlassCard