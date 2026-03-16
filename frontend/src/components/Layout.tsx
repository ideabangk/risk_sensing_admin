import { NavLink, Outlet } from 'react-router-dom'
import { BarChart3, Building2, FileText, RefreshCw } from 'lucide-react'

const navItems = [
  { to: '/', label: '대시보드', icon: BarChart3, end: true },
  { to: '/companies', label: '기업 관리', icon: Building2 },
  { to: '/articles', label: '수집 자료', icon: FileText },
  { to: '/batch', label: '배치 관리', icon: RefreshCw },
]

function TossLogo() {
  return (
    <img src="/Toss_Logo_Primary.png" alt="Toss" className="h-20" />
  )
}

export default function Layout() {
  return (
    <div className="flex h-screen" style={{ background: '#F2F4F6' }}>
      {/* Sidebar */}
      <aside className="w-56 bg-white flex flex-col border-r border-gray-100 shadow-sm">
        <div className="px-5 py-5 border-b border-gray-100">
          <TossLogo />
          <p className="text-xm text-gray-400 mt-1.5 font-medium">Toss Risk Sensing Admin</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'text-white'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
              style={({ isActive }) => isActive ? { background: '#3182F6' } : {}}
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-3 border-t border-gray-100 text-xs text-gray-400">
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
