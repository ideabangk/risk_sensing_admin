interface Props {
  source: string
}

const CONFIG: Record<string, { label: string; cls: string }> = {
  NEWS:            { label: '뉴스',      cls: 'bg-blue-50 text-blue-700' },
  BLOG:            { label: '블로그',    cls: 'bg-purple-50 text-purple-700' },
  CAFE:            { label: '카페',      cls: 'bg-pink-50 text-pink-700' },
  CONSUMER_AGENCY: { label: '소비자원',  cls: 'bg-amber-50 text-amber-700' },
  DART:            { label: 'DART',      cls: 'bg-emerald-50 text-emerald-700' },
}

export default function SourceBadge({ source }: Props) {
  const cfg = CONFIG[source] || { label: source, cls: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}
