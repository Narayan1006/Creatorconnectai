interface NavItem {
  icon: string
  label: string
  active?: boolean
}

const navItems: NavItem[] = [
  { icon: 'dashboard', label: 'Dashboard', active: true },
  { icon: 'smart_toy', label: 'Models' },
  { icon: 'payments', label: 'Earnings' },
  { icon: 'monitoring', label: 'Analytics' },
  { icon: 'settings', label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="w-[200px] shrink-0 flex flex-col bg-surface_container_low min-h-[calc(100vh-3.5rem)] px-3 py-5 gap-1">
      {/* User profile */}
      <div className="flex items-center gap-3 px-3 pb-5">
        <div className="w-9 h-9 rounded-xl bg-on_surface flex items-center justify-center shrink-0">
          <span className="text-xs font-bold text-surface">SW</span>
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-on_surface truncate">Studio Workspace</p>
          <p className="text-label-upper text-on_surface_variant" style={{ fontSize: '0.6rem' }}>Creator Pro</p>
        </div>
      </div>

      {/* Nav items */}
      {navItems.map((item) => (
        <button
          key={item.label}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors w-full text-left ${
            item.active
              ? 'bg-primary_container text-primary'
              : 'text-on_surface_variant hover:bg-surface_container hover:text-on_surface'
          }`}
        >
          <span className="material-icons-round" style={{ fontSize: 18 }}>{item.icon}</span>
          {item.label}
        </button>
      ))}

      <div className="flex-1" />

      {/* Enterprise upsell */}
      <div className="rounded-xl bg-surface_container_lowest ghost-border p-4 shadow-ambient mb-3">
        <p className="text-sm font-semibold text-primary mb-1">Enterprise Access</p>
        <p className="text-xs text-on_surface_variant leading-relaxed mb-3">
          Scale your agency with custom AI fine-tuning.
        </p>
        <button className="w-full gradient-primary text-on_primary text-xs font-semibold py-2 rounded-md hover:opacity-90 transition-opacity">
          Upgrade to Enterprise
        </button>
      </div>

      {/* Help */}
      <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-on_surface_variant hover:bg-surface_container hover:text-on_surface transition-colors w-full">
        <span className="material-icons-round" style={{ fontSize: 18 }}>help</span>
        Help Center
      </button>
    </aside>
  )
}
