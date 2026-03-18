import axios from 'axios'

const api = axios.create({
  baseURL: (window as any)._env_?.API_URL || 'http://localhost:8000',
  timeout: 30000,
})

export default api

// --- Types ---
export interface Company {
  id: number
  name: string
  search_keywords: string[]
  is_active: boolean
  created_at: string
}

export interface Article {
  id: number
  company_id: number
  company_name: string
  source_type: 'NEWS' | 'BLOG' | 'CAFE' | 'CONSUMER_AGENCY' | 'DART'
  title: string
  content: string | null
  url: string | null
  author: string | null
  published_at: string | null
  collected_at: string
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  risk_level: 'CRITICAL' | 'HIGH' | 'MIDDLE' | 'LOW' | 'NONE'
  risk_keywords: string[]
  summary: string | null
}

export interface ArticleListResponse {
  total: number
  page: number
  size: number
  pages: number
  items: Article[]
}

export interface DashboardStats {
  total_articles: number
  articles_today: number
  critical_count: number
  high_count: number
  middle_count: number
  low_count: number
  none_count: number
  negative_ratio: number
  top_risk_companies: { name: string; total: number; high_risk: number }[]
  recent_critical: Article[]
  source_distribution: { source_type: string; count: number }[]
  daily_trend: { date: string; total: number; high_risk: number; negative: number }[]
}

export interface BatchLog {
  id: number
  company_id: number | null
  company_name: string | null
  source_type: string | null
  started_at: string
  completed_at: string | null
  status: 'RUNNING' | 'SUCCESS' | 'FAILED'
  articles_collected: number
  error_message: string | null
}

// --- API calls ---
export const companiesApi = {
  list: () => api.get<Company[]>('/companies').then(r => r.data),
  create: (data: { name: string; search_keywords: string[]; is_active: boolean }) =>
    api.post<Company>('/companies', data).then(r => r.data),
  update: (id: number, data: { name: string; search_keywords: string[]; is_active: boolean }) =>
    api.patch<Company>(`/companies/${id}`, data).then(r => r.data),
  delete: (id: number) => api.delete(`/companies/${id}`),
  stats: (id: number) => api.get(`/companies/${id}/stats`).then(r => r.data),
}

export const articlesApi = {
  list: (params: Record<string, unknown>) =>
    api.get<ArticleListResponse>('/articles', { params }).then(r => r.data),
  get: (id: number) => api.get<Article>(`/articles/${id}`).then(r => r.data),
  updateLabel: (id: number, data: { risk_level?: string; sentiment?: string }) =>
    api.patch(`/articles/${id}/label`, null, { params: data }).then(r => r.data),
  delete: (id: number) => api.delete(`/articles/${id}`),
}

export const dashboardApi = {
  stats: () => api.get<DashboardStats>('/dashboard/stats').then(r => r.data),
  riskHeatmap: () => api.get('/dashboard/risk-heatmap').then(r => r.data),
}

export const batchApi = {
  runAll: (sources?: string) =>
    api.post('/batch/run/all', null, { params: sources ? { sources } : {} }).then(r => r.data),
  runCompany: (id: number, sources?: string) =>
    api.post(`/batch/run/${id}`, null, { params: sources ? { sources } : {} }).then(r => r.data),
  logs: (companyId?: number) =>
    api.get<BatchLog[]>('/batch/logs', { params: companyId ? { company_id: companyId } : {} }).then(r => r.data),
  status: () => api.get('/batch/status').then(r => r.data),
}
