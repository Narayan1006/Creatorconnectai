import { useState } from 'react'

interface Deal {
  id: string
  offer_amount: number
  deliverables: string
  deadline: string
  status: string
  ad_idea?: string
  verification_score?: number
}

interface OfferCardProps {
  deal: Deal
  onAccept: (dealId: string) => void
  onReject: (dealId: string) => void
  onCounter: (dealId: string, counterAmount: number) => void
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  accepted: 'Accepted',
  rejected: 'Rejected',
  countered: 'Countered',
  content_submitted: 'Content Submitted',
  verified: 'Verified',
  revision_requested: 'Revision Requested',
  completed: 'Completed',
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-surface_container text-on_surface_variant',
  accepted: 'bg-green-50 text-green-600',
  rejected: 'bg-red-50 text-red-500',
  countered: 'bg-yellow-50 text-yellow-600',
  content_submitted: 'bg-primary_container text-primary',
  verified: 'bg-green-50 text-green-600',
  revision_requested: 'bg-orange-50 text-orange-500',
  completed: 'bg-primary_container text-primary',
}

const TIMELINE_STATUSES = [
  'pending',
  'accepted',
  'content_submitted',
  'verified',
  'completed',
]

export default function OfferCard({ deal, onAccept, onReject, onCounter }: OfferCardProps) {
  const [showCounter, setShowCounter] = useState(false)
  const [counterAmount, setCounterAmount] = useState('')

  const handleCounter = () => {
    const amount = parseFloat(counterAmount)
    if (!isNaN(amount) && amount > 0) {
      onCounter(deal.id, amount)
      setShowCounter(false)
      setCounterAmount('')
    }
  }

  const currentIdx = TIMELINE_STATUSES.indexOf(deal.status)

  return (
    <div className="bg-surface_container_lowest rounded-xl p-5 shadow-ambient">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm font-semibold text-on_surface">${deal.offer_amount.toLocaleString()}</p>
          <p className="text-xs text-on_surface_variant mt-0.5">
            Due {new Date(deal.deadline).toLocaleDateString()}
          </p>
        </div>
        <span className={`text-label-upper text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[deal.status] ?? 'bg-surface_container text-on_surface_variant'}`}>
          {STATUS_LABELS[deal.status] ?? deal.status}
        </span>
      </div>

      {/* Deliverables */}
      <p className="text-xs text-on_surface_variant mb-1 font-medium uppercase tracking-wider">Deliverables</p>
      <p className="text-sm text-on_surface mb-4">{deal.deliverables}</p>

      {/* Ad idea (shown when accepted) */}
      {deal.status === 'accepted' && deal.ad_idea && (
        <div className="bg-primary_container rounded-lg p-3 mb-4">
          <p className="text-xs font-semibold text-on_primary_container uppercase tracking-wider mb-1">AI Ad Idea</p>
          <p className="text-sm text-on_primary_container">{deal.ad_idea}</p>
        </div>
      )}

      {/* Status timeline */}
      <div className="flex items-center gap-1 mb-4">
        {TIMELINE_STATUSES.map((s, i) => (
          <div key={s} className="flex items-center gap-1 flex-1">
            <div
              className={`w-2 h-2 rounded-full shrink-0 ${
                i <= currentIdx ? 'bg-primary' : 'bg-surface_container_high'
              }`}
            />
            {i < TIMELINE_STATUSES.length - 1 && (
              <div className={`h-0.5 flex-1 ${i < currentIdx ? 'bg-primary' : 'bg-surface_container_high'}`} />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-on_surface_variant mb-4">
        {TIMELINE_STATUSES.map((s) => (
          <span key={s} className={s === deal.status ? 'text-primary font-semibold' : ''}>
            {STATUS_LABELS[s]}
          </span>
        ))}
      </div>

      {/* Actions for pending deals */}
      {deal.status === 'pending' && (
        <div className="flex gap-2">
          <button
            onClick={() => onAccept(deal.id)}
            className="flex-1 gradient-primary text-on_primary text-xs font-semibold py-2 rounded-md hover:opacity-90 transition-opacity"
          >
            Accept
          </button>
          <button
            onClick={() => onReject(deal.id)}
            className="flex-1 bg-surface_container text-on_surface_variant text-xs font-semibold py-2 rounded-md hover:bg-surface_container_high transition-colors"
          >
            Reject
          </button>
          <button
            onClick={() => setShowCounter(!showCounter)}
            className="flex-1 bg-surface_container text-on_surface text-xs font-semibold py-2 rounded-md hover:bg-surface_container_high transition-colors"
          >
            Counter
          </button>
        </div>
      )}

      {/* Counter offer input */}
      {showCounter && (
        <div className="mt-3 flex gap-2">
          <input
            type="number"
            value={counterAmount}
            onChange={(e) => setCounterAmount(e.target.value)}
            placeholder="Counter amount ($)"
            className="flex-1 bg-surface_container rounded-lg px-3 py-2 text-sm text-on_surface placeholder:text-on_surface_variant outline-none border border-outline_variant/20 focus:border-primary"
          />
          <button
            onClick={handleCounter}
            className="gradient-primary text-on_primary text-xs font-semibold px-4 py-2 rounded-md hover:opacity-90 transition-opacity"
          >
            Send
          </button>
        </div>
      )}
    </div>
  )
}
