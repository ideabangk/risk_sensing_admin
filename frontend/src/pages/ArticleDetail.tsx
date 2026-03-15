import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { articlesApi, Article } from '../api/client'
import RiskBadge from '../components/RiskBadge'
import SentimentBadge from '../components/SentimentBadge'
import SourceBadge from '../components/SourceBadge'
import { ArrowLeft, ExternalLink, Edit2, Check } from 'lucide-react'

const RISK_LEVELS = ['CRITICAL', 'HIGH', 'MIDDLE', 'LOW', 'NONE']
const SENTIMENTS = ['POSITIVE', 'NEGATIVE', 'NEUTRAL']

export default function ArticleDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [article, setArticle] = useState<Article | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editRisk, setEditRisk] = useState('')
  const [editSentiment, setEditSentiment] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!id) return
    articlesApi.get(parseInt(id))
      .then(a => {
        setArticle(a)
        setEditRisk(a.risk_level)
        setEditSentiment(a.sentiment)
      })
      .finally(() => setLoading(false))
  }, [id])

  const handleSave = async () => {
    if (!article) return
    setSaving(true)
    try {
      await articlesApi.updateLabel(article.id, {
        risk_level: editRisk,
        sentiment: editSentiment,
      })
      setArticle({ ...article, risk_level: editRisk as Article['risk_level'], sentiment: editSentiment as Article['sentiment'] })
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-sm text-gray-400">로딩 중...</div>
  }

  if (!article) {
    return <div className="p-8 text-sm text-red-500">자료를 찾을 수 없습니다.</div>
  }

  const riskColor: Record<string, string> = {
    CRITICAL: 'border-l-red-500', HIGH: 'border-l-orange-400',
    MIDDLE: 'border-l-yellow-400', LOW: 'border-l-blue-400', NONE: 'border-l-gray-200',
  }

  return (
    <div className="p-6 max-w-3xl">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 mb-5"
      >
        <ArrowLeft className="w-4 h-4" /> 목록으로
      </button>

      <div className={`bg-white rounded-xl border border-gray-100 shadow-sm border-l-4 ${riskColor[article.risk_level]} p-6`}>
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-2 flex-wrap">
            <SourceBadge source={article.source_type} />
            {editing ? (
              <>
                <select
                  className="text-xs border rounded px-1.5 py-0.5"
                  value={editRisk}
                  onChange={e => setEditRisk(e.target.value)}
                >
                  {RISK_LEVELS.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
                <select
                  className="text-xs border rounded px-1.5 py-0.5"
                  value={editSentiment}
                  onChange={e => setEditSentiment(e.target.value)}
                >
                  {SENTIMENTS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </>
            ) : (
              <>
                <RiskBadge level={article.risk_level} />
                <SentimentBadge sentiment={article.sentiment} />
              </>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {editing ? (
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-1 text-xs bg-blue-600 text-white px-2.5 py-1 rounded-md hover:bg-blue-700"
              >
                <Check className="w-3 h-3" /> 저장
              </button>
            ) : (
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 border border-gray-200 px-2.5 py-1 rounded-md"
              >
                <Edit2 className="w-3 h-3" /> 라벨 수정
              </button>
            )}
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 border border-blue-200 px-2.5 py-1 rounded-md"
              >
                <ExternalLink className="w-3 h-3" /> 원문 보기
              </a>
            )}
          </div>
        </div>

        {/* Title */}
        <h1 className="text-lg font-bold text-gray-900 leading-snug mb-3">{article.title}</h1>

        {/* Meta */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400 mb-4">
          <span>기업: <span className="text-gray-600 font-medium">{article.company_name}</span></span>
          {article.author && <span>작성자: {article.author}</span>}
          {article.published_at && <span>발행: {article.published_at.slice(0, 10)}</span>}
          <span>수집: {article.collected_at.slice(0, 10)}</span>
        </div>

        {/* Risk Keywords */}
        {article.risk_keywords.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1.5">감지된 리스크 키워드</p>
            <div className="flex gap-1.5 flex-wrap">
              {article.risk_keywords.map(kw => (
                <span key={kw} className="text-xs bg-red-50 text-red-600 border border-red-200 px-2 py-0.5 rounded-full">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        {article.summary && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-xs font-medium text-blue-700 mb-1">AI 요약</p>
            <p className="text-sm text-blue-800">{article.summary}</p>
          </div>
        )}

        {/* Content */}
        {article.content && (
          <div>
            <p className="text-xs font-medium text-gray-500 mb-2">본문</p>
            <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap bg-gray-50 rounded-lg p-4 max-h-80 overflow-y-auto">
              {article.content}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
