export default function ImpressionsCard() {
  return (
    <div className="gradient-primary rounded-xl p-5 text-on_primary shadow-ambient mt-4">
      <p className="text-label-upper text-xs opacity-80 mb-2">Total Impressions</p>
      <p className="text-3xl font-bold tracking-tight mb-1">1.2M</p>
      <div className="flex items-center gap-1.5 text-sm font-medium opacity-90">
        <span className="material-icons-round" style={{ fontSize: 16 }}>trending_up</span>
        +18.4% this week
      </div>
    </div>
  )
}
