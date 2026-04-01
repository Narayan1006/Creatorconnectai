interface CollaboratorCardProps {
  matchScore: number
  name: string
  specialty: string
  imageUrl?: string
}

export default function CollaboratorCard({
  matchScore,
  name,
  specialty,
  imageUrl,
}: CollaboratorCardProps) {
  return (
    <div className="bg-surface_container_lowest rounded-xl overflow-hidden shadow-ambient flex-1 min-w-0">
      {/* Image area */}
      <div className="relative h-36 bg-surface_container_high">
        {imageUrl ? (
          <img src={imageUrl} alt={name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-surface_container to-surface_container_highest">
            <span className="material-icons-round text-on_surface_variant" style={{ fontSize: 40 }}>person</span>
          </div>
        )}
        {/* Match badge */}
        <span className="absolute top-2 left-2 text-label-upper text-xs bg-primary text-on_primary px-2 py-0.5 rounded-full">
          {matchScore}% Match
        </span>
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="text-sm font-semibold text-on_surface">{name}</p>
        <p className="text-xs text-on_surface_variant mt-0.5">{specialty}</p>
      </div>
    </div>
  )
}
