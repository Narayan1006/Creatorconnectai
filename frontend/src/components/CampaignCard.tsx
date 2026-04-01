interface CampaignCardProps {
  icon: string
  status: 'ACTIVE' | 'DRAFTING'
  title: string
  subtitle: string
  progressLabel: string
  progress: number
}

export default function CampaignCard({
  icon,
  status,
  title,
  subtitle,
  progressLabel,
  progress,
}: CampaignCardProps) {
  const isActive = status === 'ACTIVE'

  return (
    <div className="bg-surface_container_lowest rounded-xl p-5 shadow-ambient flex-1 min-w-0">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 rounded-xl bg-primary_container flex items-center justify-center">
          <span className="material-icons-round text-primary" style={{ fontSize: 20 }}>{icon}</span>
        </div>
        <span
          className={`text-label-upper text-xs px-2 py-0.5 rounded-full ${
            isActive
              ? 'bg-green-50 text-green-600'
              : 'bg-surface_container text-on_surface_variant'
          }`}
        >
          {status}
        </span>
      </div>

      <h3 className="text-sm font-semibold text-on_surface mb-0.5">{title}</h3>
      <p className="text-xs text-on_surface_variant mb-4">{subtitle}</p>

      <div>
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-xs text-on_surface_variant">{progressLabel}</span>
          <span className="text-xs font-semibold text-primary">{progress}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-surface_container_high overflow-hidden">
          <div
            className="h-full rounded-full gradient-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  )
}
