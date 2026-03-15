import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { articlesApi, companiesApi, ArticleListResponse, Company } from '../api/client'
import RiskBadge from '../components/RiskBadge'
import SentimentBadge from '../components/SentimentBadge'
import SourceBadge from '../components/SourceBadge'
import { Search, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react'

const RISK_LEVELS = ['', 'CRITICAL', 'HIGH', 'MIDDLE', 'LOW', 'NONE']
const SOURCES = ['', 'NEWS', 'BLOG', 'CAFE', 'CONSUMER_AGENCY', 'DART']
const SENTIMENTS = ['', 'POSITIVE', 'NEGATIVE', 'NEUTRAL']
const SOURCE_LABELS: Record<string, string> = {
  NEWS: '뉴스', BLOG: '블로그', CAFE: '카페', CONSUMER_AGENCY: '소비자원', DART: 'DART',
}

export default function Articles() {
  const [data, setData] = useState<ArticleListResponse | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const filters = {
    company_id: searchParams.get('company_id') || '',
    source_type: searchParams.get('source_type') || '',
    sentiment: searchParams.get('sentiment') || '',
    risk_level: searchParams.get('risk_level') || '',
    keyword: searchParams.get('keyword') || '',
    page: parseInt(searchParams.get('page') || '1'),
  }

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: filters.page, size: 20 }
      if (filters.company_id) params.company_id = filters.company_id
      if (filters.source_type) params.source_type = filters.source_type
      if (filters.sentiment) params.sentiment = filters.sentiment
      if (filters.risk_level) params.risk_level = filters.risk_level
      if (filters.keyword) params.keyword = filters.keyword
      const res = await articlesApi.list(params)
      setData(res)
    } finally {
      setLoading(false)
    }
  }, [searchParams])

  useEffect(() => {
    companiesApi.list().then(setCompanies)
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value); else next.delete(key)
    next.delete('page')
    setSearchParams(next)
  }

  const setPage = (p: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('page', String(p))
    setSearchParams(next)
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-gray-900">수집 자료</h1>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-wrap gap-3">
        <div className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 min-w-48">
          <Search className="w-4 h-4 text-gray-400" />
          <input
            className="bg-transparent text-sm outline-none w-full"
            placeholder="키워드 검색..."
            value={filters.keyword}
            onChange={e => setFilter('keyword', e.target.value)}
          />
        </div>

        <select
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
          value={filters.company_id}
          onChange={e => setFilter('company_id', e.target.value)}
        >
          <option value="">전체 기업</option>
          {companies.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <select
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
          value={filters.source_type}
          onChange={e => setFilter('source_type', e.target.value)}
        >
          {SOURCES.map(s => (
            <option key={s} value={s}>{s ? SOURCE_LABELS[s] || s : '전체 소스'}</option>
          ))}
        </select>

        <select
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
          value={filters.risk_level}
          onChange={e => setFilter('risk_level', e.target.value)}
        >
          {RISK_LEVELS.map(r => (
            <option key={r} value={r}>{r || '전체 Risk Level'}</option>
          ))}
        </select>

        <select
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
          value={filters.sentiment}
          onChange={e => setFilter('sentiment', e.target.value)}
        >
          {SENTIMENTS.map(s => (
            <option key={s} value={s}>{s ? (s === 'POSITIVE' ? '긍정' : s === 'NEGATIVE' ? '부정' : '중립') : '전체 감성'}</option>
          ))}
        </select>
      </div>

      {/* Results */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-50 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            총 <span className="font-semibold text-gray-800">{data?.total.toLocaleString() || 0}</span>건
          </p>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-gray-400">로딩 중...</div>
        ) : (
          <div className="divide-y divide-gray-50">
            {data?.items.length === 0 && (
              <p className="text-sm text-gray-400 p-8 text-center">수집된 자료가 없습니다.</p>
            )}
            {data?.items.map(article => (
              <div
                key={article.id}
                className="px-5 py-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/articles/${article.id}`)}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <SourceBadge source={article.source_type} />
                      <RiskBadge level={article.risk_level} size="sm" />
                      <SentimentBadge sentiment={article.sentiment} />
                    </div>
                    <p className="text-sm font-medium text-gray-800 leading-snug line-clamp-2">
                      {article.title}
                    </p>
                    {article.summary && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-1">{article.summary}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {article.company_name} · {article.author || '-'} · {article.published_at?.slice(0, 10) || article.collected_at?.slice(0, 10)}
                    </p>
                    {article.risk_keywords.length > 0 && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {article.risk_keywords.slice(0, 5).map(kw => (
                          <span key={kw} className="text-xs bg-red-50 text-red-600 px-1.5 py-0.5 rounded">
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-400 hover:text-blue-500 shrink-0"
                      onClick={e => e.stopPropagation()}
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="px-5 py-3 border-t border-gray-50 flex items-center justify-between">
            <button
              disabled={filters.page <= 1}
              onClick={() => setPage(filters.page - 1)}
              className="flex items-center gap-1 text-sm text-gray-500 disabled:opacity-40 hover:text-gray-800"
            >
              <ChevronLeft className="w-4 h-4" /> 이전
            </button>
            <span className="text-sm text-gray-500">
              {filters.page} / {data.pages}
            </span>
            <button
              disabled={filters.page >= data.pages}
              onClick={() => setPage(filters.page + 1)}
              className="flex items-center gap-1 text-sm text-gray-500 disabled:opacity-40 hover:text-gray-800"
            >
              다음 <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
