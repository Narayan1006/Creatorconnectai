interface Creator {
  id: string
  name: string
  avatar_url?: string
  niche: string[]
  followers: number
  engagement_rate: number
}

interface CreatorCardProps {
  creator: Creator
  matchScore?: number
  onSendOffer?: (creatorId: string) => void
  variant: 'showcase' | 'match-result'
}

function formatFollowers(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return String(n)
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export default function CreatorCard({ creator, matchScore, onSendOffer, variant }: CreatorCardProps) {
  return (
    <div className="bg-surface_container_lowest rounded-xl overflow-hidden shadow-ambient flex-1 min-w-0">
      {/* Image / avatar area */}
      <div className="relative h-36 bg-surface_container_high">
        {creator.avatar_url ? (
          <img src={creator.avatar_url} alt={creator.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-surface_container to-surface_container_highest">
            <span className="text-2xl font-bold text-on_surface_variant">{getInitials(creator.name)}</span>
          </div>
        )}
        {variant === 'match-result' && matchScore !== undefined && (
          <span className="absolute top-2 left-2 text-label-upper text-xs bg-primary text-on_primary px-2 py-0.5 rounded-full">
            {Math.round(matchScore * 100)}% Match
          </span>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="text-sm font-semibold text-on_surface">{creator.name}</p>

        {/* Niche tags */}
        <div className="flex flex-wrap gap-1 mt-1.5 mb-2">
          {creator.niche.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="text-xs bg-primary_container text-on_primary_container px-2 py-0.5 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-3 text-xs text-on_surface_variant mb-3">
          <span className="flex items-center gap-1">
            <span className="material-icons-round" style={{ fontSize: 13 }}>people</span>
            {formatFollowers(creator.followers)}
          </span>
          <span className="flex items-center gap-1">
            <span className="material-icons-round" style={{ fontSize: 13 }}>trending_up</span>
            {(creator.engagement_rate * 100).toFixed(1)}%
          </span>
        </div>

        {onSendOffer && (
          <button
            onClick={() => onSendOffer(creator.id)}
            className="w-full gradient-primary text-on_primary text-xs font-semibold py-2 rounded-md hover:opacity-90 transition-opacity"
          >
            Send Offer
          </button>
        )}
      </div>
    </div>
  )
}
