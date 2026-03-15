interface Props {
  sentiment: string
}

const CONFIG: Record<string, { label: string; cls: string }> = {
  POSITIVE: { label: '긍정', cls: 'bg-green-100 text-green-700' },
  NEGATIVE: { label: '부정', cls: 'bg-red-100 text-red-700' },
  NEUTRAL:  { label: '중립', cls: 'bg-gray-100 text-gray-600' },
}

export default function SentimentBadge({ sentiment }: Props) {
  const cfg = CONFIG[sentiment] || CONFIG['NEUTRAL']
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}
