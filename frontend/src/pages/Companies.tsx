import { useEffect, useState } from 'react'
import { companiesApi, batchApi, Company } from '../api/client'
import { useNavigate } from 'react-router-dom'
import { Plus, Play, BarChart2, Trash2, Check, X, Edit2 } from 'lucide-react'

function KeywordInput({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const [input, setInput] = useState('')
  const add = () => {
    const trimmed = input.trim()
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed])
      setInput('')
    }
  }
  return (
    <div>
      <div className="flex gap-2 mb-2">
        <input
          className="flex-1 text-sm border border-gray-200 rounded-md px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-300"
          placeholder="검색 키워드 추가..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())}
        />
        <button onClick={add} className="text-xs px-2.5 py-1 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100">
          추가
        </button>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {value.map(kw => (
          <span key={kw} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full flex items-center gap-1">
            {kw}
            <button onClick={() => onChange(value.filter(v => v !== kw))} className="text-gray-400 hover:text-red-500">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
    </div>
  )
}

export default function Companies() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState<Set<number>>(new Set())
  const [editId, setEditId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editKeywords, setEditKeywords] = useState<string[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [newKeywords, setNewKeywords] = useState<string[]>([])
  const navigate = useNavigate()

  const load = () => companiesApi.list().then(setCompanies).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleBatch = async (id: number) => {
    setRunning(prev => new Set(prev).add(id))
    try {
      await batchApi.runCompany(id)
    } finally {
      setRunning(prev => { const s = new Set(prev); s.delete(id); return s })
    }
  }

  const startEdit = (c: Company) => {
    setEditId(c.id)
    setEditName(c.name)
    setEditKeywords(c.search_keywords || [])
  }

  const saveEdit = async () => {
    if (!editId) return
    await companiesApi.update(editId, { name: editName, search_keywords: editKeywords, is_active: true })
    setEditId(null)
    load()
  }

  const addCompany = async () => {
    if (!newName.trim()) return
    await companiesApi.create({ name: newName, search_keywords: newKeywords, is_active: true })
    setShowAdd(false)
    setNewName('')
    setNewKeywords([])
    load()
  }

  const deleteCompany = async (id: number) => {
    if (!confirm('삭제하시겠습니까?')) return
    await companiesApi.delete(id)
    load()
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">기업 관리</h1>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-1.5 text-sm bg-blue-600 text-white px-3.5 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" /> 기업 추가
        </button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <div className="bg-white rounded-xl border border-blue-200 shadow-sm p-4 space-y-3">
          <p className="text-sm font-semibold text-gray-700">신규 기업 등록</p>
          <input
            className="w-full text-sm border border-gray-200 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-blue-300"
            placeholder="기업명"
            value={newName}
            onChange={e => setNewName(e.target.value)}
          />
          <KeywordInput value={newKeywords} onChange={setNewKeywords} />
          <div className="flex gap-2">
            <button onClick={addCompany} className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700">
              등록
            </button>
            <button onClick={() => setShowAdd(false)} className="text-sm text-gray-500 px-3 py-1.5 rounded-md hover:bg-gray-50">
              취소
            </button>
          </div>
        </div>
      )}

      {/* Company List */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm divide-y divide-gray-50">
        {loading && <p className="text-sm text-gray-400 p-6">로딩 중...</p>}
        {companies.map(company => (
          <div key={company.id} className="px-5 py-4">
            {editId === company.id ? (
              <div className="space-y-3">
                <input
                  className="w-full text-sm border border-gray-200 rounded-md px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-300"
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                />
                <KeywordInput value={editKeywords} onChange={setEditKeywords} />
                <div className="flex gap-2">
                  <button onClick={saveEdit} className="flex items-center gap-1 text-xs bg-blue-600 text-white px-2.5 py-1 rounded-md">
                    <Check className="w-3 h-3" /> 저장
                  </button>
                  <button onClick={() => setEditId(null)} className="text-xs text-gray-500 px-2.5 py-1 rounded-md hover:bg-gray-50">
                    취소
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800">{company.name}</p>
                  {company.search_keywords?.length > 0 && (
                    <div className="flex gap-1 mt-1 flex-wrap">
                      {company.search_keywords.map(kw => (
                        <span key={kw} className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                          {kw}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => navigate(`/articles?company_id=${company.id}`)}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-blue-600 px-2 py-1 rounded border border-gray-200 hover:border-blue-200"
                  >
                    <BarChart2 className="w-3.5 h-3.5" /> 자료 보기
                  </button>
                  <button
                    onClick={() => handleBatch(company.id)}
                    disabled={running.has(company.id)}
                    className="flex items-center gap-1 text-xs text-green-700 hover:text-green-800 px-2 py-1 rounded border border-green-200 hover:border-green-400 disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5" />
                    {running.has(company.id) ? '수집 중...' : '수집'}
                  </button>
                  <button
                    onClick={() => startEdit(company)}
                    className="p-1 text-gray-400 hover:text-gray-700"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteCompany(company.id)}
                    className="p-1 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
