import { useEffect, useState, useCallback } from 'react'
import { batchApi, companiesApi, BatchLog, Company } from '../api/client'
import { Play, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react'

const SOURCE_OPTIONS = [
  { value: 'NEWS', label: '뉴스' },
  { value: 'BLOG', label: '블로그' },
  { value: 'CAFE', label: '카페' },
  { value: 'CONSUMER_AGENCY', label: '한국소비자원' },
  { value: 'DART', label: 'DART 공시' },
]

function StatusIcon({ status }: { status: string }) {
  if (status === 'SUCCESS') return <CheckCircle className="w-4 h-4 text-green-500" />
  if (status === 'FAILED') return <XCircle className="w-4 h-4 text-red-500" />
  return <Clock className="w-4 h-4 text-yellow-500 animate-spin" />
}

export default function BatchManager() {
  const [logs, setLogs] = useState<BatchLog[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [batchStatus, setBatchStatus] = useState<{ running_jobs: number; last_run: string | null; total_collected: number } | null>(null)
  const [selectedSources, setSelectedSources] = useState<string[]>(SOURCE_OPTIONS.map(s => s.value))
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    const [logsData, statusData] = await Promise.all([
      batchApi.logs(),
      batchApi.status(),
    ])
    setLogs(logsData)
    setBatchStatus(statusData)
    setLoading(false)
  }, [])

  useEffect(() => {
    companiesApi.list().then(setCompanies)
    load()
  }, [load])

  // Auto-refresh if running
  useEffect(() => {
    if (batchStatus?.running_jobs && batchStatus.running_jobs > 0) {
      const timer = setTimeout(load, 3000)
      return () => clearTimeout(timer)
    }
  }, [batchStatus, load])

  const toggleSource = (src: string) => {
    setSelectedSources(prev =>
      prev.includes(src) ? prev.filter(s => s !== src) : [...prev, src]
    )
  }

  const runAll = async () => {
    setRunning(true)
    try {
      const sources = selectedSources.join(',')
      await batchApi.runAll(sources)
      setTimeout(load, 1000)
    } finally {
      setRunning(false)
    }
  }

  const duration = (log: BatchLog) => {
    if (!log.completed_at || !log.started_at) return '-'
    const ms = new Date(log.completed_at).getTime() - new Date(log.started_at).getTime()
    const s = Math.round(ms / 1000)
    return s >= 60 ? `${Math.floor(s / 60)}분 ${s % 60}초` : `${s}초`
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold text-gray-900">배치 관리</h1>

      {/* Status Cards */}
      {batchStatus && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">실행 중인 작업</p>
            <p className="text-2xl font-bold text-gray-800">{batchStatus.running_jobs}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">마지막 실행</p>
            <p className="text-sm font-semibold text-gray-700">
              {batchStatus.last_run ? batchStatus.last_run.slice(0, 16).replace('T', ' ') : '-'}
            </p>
          </div>
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">누적 수집 건수</p>
            <p className="text-2xl font-bold text-blue-600">{batchStatus.total_collected.toLocaleString()}</p>
          </div>
        </div>
      )}

      {/* Run Controls */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">수집 실행</h2>

        <div>
          <p className="text-xs text-gray-500 mb-2">수집 소스 선택</p>
          <div className="flex gap-2 flex-wrap">
            {SOURCE_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => toggleSource(value)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  selectedSources.includes(value)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={runAll}
            disabled={running || selectedSources.length === 0}
            className="flex items-center gap-2 text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {running ? '시작됨 (백그라운드 실행)' : `전체 기업 수집 시작 (${companies.filter(c => c.is_active).length}개)`}
          </button>
          <button
            onClick={load}
            className="flex items-center gap-2 text-sm text-gray-500 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" /> 새로고침
          </button>
        </div>

        <p className="text-xs text-gray-400">
          배치는 백그라운드에서 실행되며 자동으로 {batchStatus?.running_jobs != null ? '주기적으로' : ''} 실행됩니다.
          설정된 주기: 6시간마다
        </p>
      </div>

      {/* Batch Logs */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-50">
          <h2 className="text-sm font-semibold text-gray-700">실행 이력</h2>
        </div>
        {loading ? (
          <p className="text-sm text-gray-400 p-6">로딩 중...</p>
        ) : (
          <div className="divide-y divide-gray-50">
            {logs.length === 0 && (
              <p className="text-sm text-gray-400 p-6 text-center">실행 이력이 없습니다.</p>
            )}
            {logs.map(log => (
              <div key={log.id} className="px-5 py-3 flex items-center gap-4">
                <StatusIcon status={log.status} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800">
                    {log.company_name || '전체'}
                    {log.source_type && (
                      <span className="text-xs text-gray-400 ml-2">[{log.source_type}]</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-400">
                    {log.started_at?.slice(0, 16).replace('T', ' ')} · 소요 {duration(log)}
                  </p>
                  {log.error_message && (
                    <p className="text-xs text-red-500 mt-0.5 truncate">{log.error_message}</p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-semibold text-gray-700">+{log.articles_collected}</p>
                  <p className="text-xs text-gray-400">수집</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
