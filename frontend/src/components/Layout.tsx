import { NavLink, Outlet } from 'react-router-dom'
import { BarChart3, Building2, FileText, RefreshCw, Shield } from 'lucide-react'

const navItems = [
  { to: '/', label: '대시보드', icon: BarChart3, end: true },
  { to: '/companies', label: '기업 관리', icon: Building2 },
  { to: '/articles', label: '수집 자료', icon: FileText },
  { to: '/batch', label: '배치 관리', icon: RefreshCw },
]

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 text-white flex flex-col">
        <div className="px-4 py-5 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-400" />
            <div>
              <p className="text-sm font-bold leading-tight">Risk Sensing</p>
              <p className="text-xs text-slate-400">외부정보 센싱 어드민</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-500">
          v1.0.0 · Toss Risk Team
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
