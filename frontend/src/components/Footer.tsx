export default function Footer() {
  return (
    <footer className="bg-surface_container_low mt-auto">
      <div className="mx-auto max-w-[1440px] px-6 py-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-on_surface">CreatorConnectAI</p>
          <p className="text-xs text-on_surface_variant mt-0.5">
            © 2024 CreatorConnectAI. Designed for the future of creativity.
          </p>
        </div>
        <nav className="flex items-center gap-5 text-xs font-medium text-on_surface_variant">
          <a href="#" className="hover:text-on_surface transition-colors uppercase tracking-wider">Privacy Policy</a>
          <a href="#" className="hover:text-on_surface transition-colors uppercase tracking-wider">Terms of Service</a>
          <a href="#" className="hover:text-on_surface transition-colors uppercase tracking-wider">AI Ethics</a>
          <a href="#" className="hover:text-on_surface transition-colors uppercase tracking-wider">Contact</a>
        </nav>
      </div>
    </footer>
  )
}
