interface Props {
  level: string
  size?: 'sm' | 'md'
}

const CONFIG: Record<string, { label: string; cls: string }> = {
  CRITICAL: { label: 'CRITICAL', cls: 'bg-red-100 text-red-700 border border-red-300' },
  HIGH:     { label: 'HIGH',     cls: 'bg-orange-100 text-orange-700 border border-orange-300' },
  MIDDLE:   { label: 'MIDDLE',   cls: 'bg-yellow-100 text-yellow-700 border border-yellow-300' },
  LOW:      { label: 'LOW',      cls: 'bg-blue-100 text-blue-700 border border-blue-300' },
  NONE:     { label: 'NONE',     cls: 'bg-gray-100 text-gray-500 border border-gray-200' },
}

export default function RiskBadge({ level, size = 'md' }: Props) {
  const cfg = CONFIG[level] || CONFIG['NONE']
  const px = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-0.5 text-xs font-semibold'
  return (
    <span className={`inline-block rounded font-mono ${px} ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}
