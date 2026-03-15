import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts'
import { dashboardApi, DashboardStats } from '../api/client'
import RiskBadge from '../components/RiskBadge'
import SourceBadge from '../components/SourceBadge'
import { AlertTriangle, TrendingUp, FileText, Frown } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444', HIGH: '#f97316', MIDDLE: '#eab308', LOW: '#3b82f6', NONE: '#9ca3af',
}
const SOURCE_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']

function StatCard({ icon: Icon, label, value, sub, color }: {
  icon: React.ElementType; label: string; value: number | string; sub?: string; color: string
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{label}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className={`p-2 rounded-lg bg-opacity-10 ${color.replace('text-', 'bg-')}`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    dashboardApi.stats()
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-gray-200 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (!stats) return null

  const riskPieData = [
    { name: 'CRITICAL', value: stats.critical_count },
    { name: 'HIGH', value: stats.high_count },
    { name: 'MIDDLE', value: stats.middle_count },
    { name: 'LOW', value: stats.low_count },
    { name: 'NONE', value: stats.none_count },
  ].filter(d => d.value > 0)

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">대시보드</h1>
        <button
          onClick={() => dashboardApi.stats().then(setStats)}
          className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1"
        >
          <TrendingUp className="w-4 h-4" /> 새로고침
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText} label="전체 수집 자료" value={stats.total_articles.toLocaleString()}
          sub={`오늘 +${stats.articles_today}`} color="text-gray-700" />
        <StatCard icon={AlertTriangle} label="CRITICAL" value={stats.critical_count}
          sub="즉시 검토 필요" color="text-red-600" />
        <StatCard icon={AlertTriangle} label="HIGH" value={stats.high_count}
          sub="주의 필요" color="text-orange-500" />
        <StatCard icon={Frown} label="부정 비율" value={`${stats.negative_ratio}%`}
          sub="전체 수집 자료 기준" color="text-purple-600" />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Daily Trend */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">최근 30일 수집 트렌드</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={stats.daily_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }}
                tickFormatter={v => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total" stroke="#6366f1" name="전체" dot={false} />
              <Line type="monotone" dataKey="high_risk" stroke="#ef4444" name="High Risk" dot={false} />
              <Line type="monotone" dataKey="negative" stroke="#f97316" name="부정" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Pie */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Risk Level 분포</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                dataKey="value" nameKey="name">
                {riskPieData.map((entry) => (
                  <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                ))}
              </Pie>
              <Tooltip formatter={(value, name) => [value, name]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Source distribution */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">소스별 수집 현황</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.source_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="source_type" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" name="건수">
                {stats.source_distribution.map((_, idx) => (
                  <Cell key={idx} fill={SOURCE_COLORS[idx % SOURCE_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top risk companies */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">기업별 High Risk 건수 TOP 10</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.top_risk_companies} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={80} />
              <Tooltip />
              <Bar dataKey="high_risk" fill="#ef4444" name="High Risk" />
              <Bar dataKey="total" fill="#e2e8f0" name="전체" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Critical */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">최근 CRITICAL / HIGH 자료</h2>
        <div className="divide-y divide-gray-50">
          {stats.recent_critical.length === 0 && (
            <p className="text-sm text-gray-400 py-4">수집된 Critical/High 자료가 없습니다.</p>
          )}
          {stats.recent_critical.map((article) => (
            <div
              key={article.id}
              className="py-3 flex items-start gap-3 cursor-pointer hover:bg-gray-50 rounded px-2 -mx-2"
              onClick={() => navigate(`/articles/${article.id}`)}
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{article.title}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {article.company_name} · {article.collected_at?.slice(0, 10)}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <SourceBadge source={article.source_type} />
                <RiskBadge level={article.risk_level} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
