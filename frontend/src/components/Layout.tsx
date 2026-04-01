import { type ReactNode } from 'react'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { icon: 'dashboard', label: 'Overview' },
  { icon: 'search', label: 'Discovery' },
  { icon: 'handshake', label: 'Deals' },
  { icon: 'verified', label: 'Verification' },
  { icon: 'payments', label: 'Payments' },
  { icon: 'settings', label: 'Settings' },
]

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen flex bg-[#f9f9f9] font-body text-[#1a1c1c]">
      <aside className="w-[220px] shrink-0 flex flex-col bg-white border-r border-[#e8e8e8] min-h-screen px-4 py-6">
        <div className="px-3 mb-8">
          <div className="text-base font-black font-headline tracking-tighter text-black">CreatorConnectAI</div>
          <div className="text-[10px] uppercase tracking-widest text-[#777777] mt-0.5">
            {user?.role === 'business' ? 'Enterprise' : 'Creator'} Portal
          </div>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          {NAV_ITEMS.map((item, i) => (
            <button key={item.label}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors w-full text-left ${
                i === 0 ? 'bg-black text-white' : 'text-[#474747] hover:bg-[#f3f3f4] hover:text-black'
              }`}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="border-t border-[#e8e8e8] pt-4 mt-4">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-xs font-bold shrink-0">
              {user?.email?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-black truncate">{user?.email ?? 'User'}</p>
              <p className="text-[10px] text-[#777777] capitalize">{user?.role ?? 'member'}</p>
            </div>
            <button onClick={logout} className="text-[#777777] hover:text-black transition-colors">
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>logout</span>
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-white border-b border-[#e8e8e8] flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-3 bg-[#f3f3f4] rounded-lg px-3 py-2 w-64">
            <span className="material-symbols-outlined text-[#777777]" style={{ fontSize: 16 }}>search</span>
            <input type="text" placeholder="Search creators, campaigns..."
              className="bg-transparent text-sm text-[#1a1c1c] placeholder:text-[#777777] outline-none w-full" />
          </div>
          <button className="p-2 rounded-lg hover:bg-[#f3f3f4] transition-colors text-[#474747]">
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>notifications</span>
          </button>
        </header>
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
