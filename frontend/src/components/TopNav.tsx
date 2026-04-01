export default function TopNav() {
  return (
    <header className="glass-nav sticky top-0 z-50 w-full border-b border-outline_variant/10">
      <div className="mx-auto flex h-14 max-w-[1440px] items-center gap-8 px-6">
        {/* Logo */}
        <span className="text-[0.95rem] font-semibold tracking-tight text-on_surface">
          CreatorConnectAI
        </span>

        {/* Nav links */}
        <nav className="flex items-center gap-6 text-sm font-medium text-on_surface_variant">
          <a href="#" className="hover:text-on_surface transition-colors">Marketplace</a>
          <a href="#" className="text-primary border-b-2 border-primary pb-0.5">Explore</a>
          <a href="#" className="hover:text-on_surface transition-colors">Showcase</a>
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Search */}
        <div className="flex items-center gap-2 rounded-xl bg-surface_container_low px-3 py-2 w-56">
          <span className="material-icons-round text-on_surface_variant" style={{ fontSize: 16 }}>search</span>
          <input
            type="text"
            placeholder="Search creators..."
            className="bg-transparent text-sm text-on_surface placeholder:text-on_surface_variant outline-none w-full"
          />
        </div>

        {/* Icon actions */}
        <div className="flex items-center gap-1">
          <button className="p-2 rounded-lg hover:bg-surface_container transition-colors text-on_surface_variant">
            <span className="material-icons-round" style={{ fontSize: 20 }}>notifications</span>
          </button>
          <button className="p-2 rounded-lg hover:bg-surface_container transition-colors text-on_surface_variant">
            <span className="material-icons-round" style={{ fontSize: 20 }}>bookmark</span>
          </button>
        </div>

        {/* CTA */}
        <button className="gradient-primary text-on_primary text-sm font-semibold px-4 py-2 rounded-md hover:opacity-90 transition-opacity">
          Create AI
        </button>

        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-primary_container flex items-center justify-center overflow-hidden">
          <span className="text-xs font-semibold text-on_primary_container">SW</span>
        </div>
      </div>
    </header>
  )
}
