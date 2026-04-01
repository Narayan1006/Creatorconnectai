import { useState, useEffect } from 'react'
import axios from 'axios'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Creator {
  _id?: string; id?: string; name: string; avatar_url?: string
  niche: string[]; followers: number; engagement_rate: number
}
interface MatchResult { creator: Creator; match_score: number }
interface Deal {
  id?: string
  _id?: string
  business_id: string
  creator_id: string
  offer_amount: number
  deliverables: string
  deadline: string
  status: string
  counter_message?: string
  counter_amount?: number
  counter_deliverables?: string
  counter_history?: Array<{
    author: string
    message?: string
    proposed_amount?: number
    proposed_deliverables?: string
    timestamp: string
  }>
}
interface DealResult { id: string; status: string }

function fmt(n: number) {
  if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n/1_000).toFixed(0)}K`
  return String(n)
}

export default function BusinessDashboard() {
  const { token, user } = useAuth()
  const [product, setProduct] = useState('')
  const [audience, setAudience] = useState('')
  const [budget, setBudget] = useState('')
  const [results, setResults] = useState<MatchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState('')
  const [selectedCreator, setSelectedCreator] = useState<string | null>(null)
  const [offerAmount, setOfferAmount] = useState('')
  const [deliverables, setDeliverables] = useState('')
  const [deadline, setDeadline] = useState('')
  const [offerLoading, setOfferLoading] = useState(false)
  const [dealResult, setDealResult] = useState<DealResult | null>(null)
  const [offerError, setOfferError] = useState('')
  const [deals, setDeals] = useState<Deal[]>([])
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null)
  const [dealActionLoading, setDealActionLoading] = useState(false)
  const [dealActionError, setDealActionError] = useState('')
  const [showBusinessCounterForm, setShowBusinessCounterForm] = useState(false)
  const [businessCounterMessage, setBusinessCounterMessage] = useState('')
  const [businessCounterAmount, setBusinessCounterAmount] = useState('')
  const [businessCounterDeliverables, setBusinessCounterDeliverables] = useState('')
  const [showAcceptConfirmation, setShowAcceptConfirmation] = useState(false)

  const handleMatch = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(''); setResults([]); setLoading(true); setSearched(true)
    try {
      const res = await axios.post<{ results: MatchResult[] }>(
        `${API_BASE}/api/match`,
        { product_description: product, target_audience: audience, budget: parseFloat(budget) },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setResults(res.data.results ?? res.data as any)
    } catch { setError('Discovery failed. Please try again.') }
    finally { setLoading(false) }
  }

  const fetchDeals = async () => {
    try {
      const res = await axios.get<Deal[]>(`${API_BASE}/api/deals`, { headers: { Authorization: `Bearer ${token}` } })
      setDeals(res.data)
    } catch {
      // Silently fail - deals section is optional
    }
  }

  const handleAcceptCounter = async (dealId: string) => {
    setDealActionLoading(true); setDealActionError('')
    try {
      await axios.put(`${API_BASE}/api/deals/${dealId}/accept-counter`, {}, { headers: { Authorization: `Bearer ${token}` } })
      await fetchDeals()
      setSelectedDeal(null)
      setShowAcceptConfirmation(false)
    } catch (err: any) {
      setDealActionError(err?.response?.data?.detail ?? 'Failed to accept counter')
    } finally {
      setDealActionLoading(false)
    }
  }

  const hasTermsChanged = (deal: Deal) => {
    return (deal.counter_amount && deal.counter_amount !== deal.offer_amount) ||
           (deal.counter_deliverables && deal.counter_deliverables !== deal.deliverables)
  }

  const handleRejectCounter = async (dealId: string) => {
    setDealActionLoading(true); setDealActionError('')
    try {
      await axios.put(`${API_BASE}/api/deals/${dealId}/reject-counter`, {}, { headers: { Authorization: `Bearer ${token}` } })
      await fetchDeals()
      setSelectedDeal(null)
    } catch (err: any) {
      setDealActionError(err?.response?.data?.detail ?? 'Failed to reject counter')
    } finally {
      setDealActionLoading(false)
    }
  }

  const handleBusinessCounter = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDeal) return
    const dealId = selectedDeal.id ?? selectedDeal._id ?? ''
    setDealActionLoading(true); setDealActionError('')
    try {
      const payload: any = {}
      if (businessCounterMessage.trim()) payload.message = businessCounterMessage.trim()
      if (businessCounterAmount) payload.counter_amount = parseFloat(businessCounterAmount)
      if (businessCounterDeliverables.trim()) payload.counter_deliverables = businessCounterDeliverables.trim()
      
      await axios.put(`${API_BASE}/api/deals/${dealId}/business-counter`, payload, { headers: { Authorization: `Bearer ${token}` } })
      await fetchDeals()
      setSelectedDeal(null)
      setShowBusinessCounterForm(false)
      setBusinessCounterMessage('')
      setBusinessCounterAmount('')
      setBusinessCounterDeliverables('')
    } catch (err: any) {
      setDealActionError(err?.response?.data?.detail ?? 'Failed to send counter')
    } finally {
      setDealActionLoading(false)
    }
  }

  const handleOffer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCreator) return
    setOfferLoading(true); setOfferError('')
    try {
      const res = await axios.post<DealResult>(
        `${API_BASE}/api/deals`,
        {
          business_id: user?.id ?? 'unknown',
          creator_id: selectedCreator,
          offer_amount: parseFloat(offerAmount),
          deliverables,
          deadline: new Date(deadline).toISOString(),
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setDealResult(res.data)
      await fetchDeals()
    } catch (err: any) {
      setOfferError(err?.response?.data?.detail ?? 'Failed to create deal. Please try again.')
    } finally { setOfferLoading(false) }
  }

  useEffect(() => {
    fetchDeals()
  }, [])

  return (
    <Layout>
      <div className="px-8 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-10">
          <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-[#777777] mb-2">Campaign Discovery</p>
          <h1 className="text-3xl font-headline font-extrabold tracking-tighter text-black">Find Your Creators</h1>
          <p className="text-[#474747] mt-1 text-sm">Deploy AI to architect perfect creator alignments for your brand.</p>
        </div>

        {/* Countered Deals Section */}
        {deals.filter(d => d.status === 'countered').length > 0 && (
          <div className="mb-10">
            <h2 className="text-xl font-bold mb-4">Countered Offers ({deals.filter(d => d.status === 'countered').length})</h2>
            <div className="grid gap-4">
              {deals.filter(d => d.status === 'countered').map(deal => (
                <div key={deal.id ?? deal._id} className="bg-yellow-50 border-2 border-yellow-300 rounded-xl p-5">
                  <p className="text-xs font-bold text-yellow-900 mb-2">COUNTERED BY CREATOR</p>
                  <p className="font-bold">Original Offer: ${deal.offer_amount}</p>
                  {deal.counter_amount && <p className="font-bold text-yellow-900">Counter Amount: ${deal.counter_amount}</p>}
                  <p className="text-sm mt-1">{deal.deliverables}</p>
                  {deal.counter_message && (
                    <div className="mt-3 p-3 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-bold mb-1">Creator Message:</p>
                      <p className="text-sm">{deal.counter_message}</p>
                    </div>
                  )}
                  {deal.counter_deliverables && (
                    <div className="mt-2 p-3 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-bold mb-1">Counter Deliverables:</p>
                      <p className="text-sm">{deal.counter_deliverables}</p>
                    </div>
                  )}
                  {deal.counter_history && deal.counter_history.length > 0 && (
                    <div className="mt-3 p-3 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-bold mb-2">Negotiation History:</p>
                      <div className="space-y-2">
                        {deal.counter_history.map((entry, idx) => (
                          <div key={idx} className="text-xs border-l-2 border-gray-300 pl-2">
                            <p className="font-bold">{entry.author === 'business' ? 'You' : 'Creator'} - {new Date(entry.timestamp).toLocaleDateString()}</p>
                            {entry.message && <p className="text-gray-700">{entry.message}</p>}
                            {entry.proposed_amount && <p>Amount: ${entry.proposed_amount}</p>}
                            {entry.proposed_deliverables && <p>Deliverables: {entry.proposed_deliverables}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <button onClick={() => { setSelectedDeal(deal); setDealActionError('') }} 
                    className="mt-3 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700">
                    Respond to Counter
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Match form */}
        <form onSubmit={handleMatch} className="bg-white border border-[#e8e8e8] rounded-xl p-8 mb-10 shadow-[0_10px_40px_rgba(0,0,0,0.03)]">
          <h2 className="text-sm font-bold uppercase tracking-widest text-[#777777] mb-6">Campaign Brief</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-3">
              <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Product Description</label>
              <textarea value={product} onChange={e => setProduct(e.target.value)} rows={3} required minLength={10}
                placeholder="Describe your product or service in detail..."
                className="w-full border border-[#e2e2e2] rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors resize-none" />
            </div>
            <div className="md:col-span-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Target Audience</label>
              <input type="text" value={audience} onChange={e => setAudience(e.target.value)} required minLength={5}
                placeholder="e.g. Tech-savvy professionals aged 25–40"
                className="w-full border border-[#e2e2e2] rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors" />
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Budget (USD)</label>
              <input type="number" value={budget} onChange={e => setBudget(e.target.value)} required min={1}
                placeholder="5000"
                className="w-full border border-[#e2e2e2] rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors" />
            </div>
          </div>
          {error && <p className="text-xs text-red-600 mt-4">{error}</p>}
          <button type="submit" disabled={loading}
            className="mt-6 bg-black text-white px-8 py-3 text-sm font-bold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2">
            {loading ? 'Analyzing...' : <><span className="material-symbols-outlined" style={{fontSize:16}}>search</span> Run Discovery</>}
          </button>
        </form>

        {/* No results state */}
        {!loading && searched && results.length === 0 && !error && (
          <div className="bg-white border border-[#e8e8e8] rounded-xl overflow-hidden max-w-2xl">
            <div className="p-12 text-center border-b border-[#f3f3f4]">
              <div className="w-16 h-16 bg-[#f3f3f4] rounded-full flex items-center justify-center mx-auto mb-5">
                <span className="material-symbols-outlined text-[#c6c6c6]" style={{ fontSize: 32 }}>manage_search</span>
              </div>
              <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-[#777777] mb-2">No Creators Found</p>
              <p className="font-headline font-bold text-black text-xl mb-2">Refine your campaign brief</p>
              <p className="text-sm text-[#474747] leading-relaxed max-w-sm mx-auto">
                No creators matched your query. Try broadening your product description or target audience to get better results.
              </p>
            </div>
            <div className="p-6 bg-[#f9f9f9]">
              <p className="text-[10px] font-bold uppercase tracking-widest text-[#777777] mb-4">Tips for better matches</p>
              <div className="space-y-3">
                {[
                  { icon: 'description', text: 'Use at least 20 words in your product description for better AI matching' },
                  { icon: 'group', text: 'Be specific about your target audience — age, interests, platform' },
                  { icon: 'payments', text: 'A higher budget signals premium campaigns and attracts top creators' },
                  { icon: 'person_add', text: 'More creators will appear as the platform grows — check back soon' },
                ].map(item => (
                  <div key={item.icon} className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-black mt-0.5 shrink-0" style={{ fontSize: 16 }}>{item.icon}</span>
                    <p className="text-sm text-[#474747]">{item.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-[#777777]">Matched Creators</p>
                <p className="text-xl font-headline font-bold text-black mt-1">{results.length} Alignments Found</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">              {results.map(r => (
                <div key={r.creator._id ?? r.creator.id} className="bg-white border border-[#e8e8e8] rounded-xl overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.03)] hover:shadow-[0_20px_60px_rgba(0,0,0,0.06)] transition-shadow">
                  <div className="h-32 bg-[#e8e8e8] relative">
                    {r.creator.avatar_url
                      ? <img src={r.creator.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                      : <div className="w-full h-full flex items-center justify-center text-3xl font-black text-[#c6c6c6] font-headline">
                          {r.creator.name[0]}
                        </div>
                    }
                    <div className="absolute top-3 left-3 bg-black text-white text-[10px] font-bold px-2 py-1 rounded uppercase tracking-widest">
                      {Math.round(r.match_score * 100)}% Match
                    </div>
                  </div>
                  <div className="p-5">
                    <p className="font-headline font-bold text-black text-base">{r.creator.name}</p>
                    <div className="flex flex-wrap gap-1 mt-2 mb-3">
                      {r.creator.niche.slice(0,3).map(n => (
                        <span key={n} className="text-[10px] bg-[#f3f3f4] text-[#474747] px-2 py-0.5 rounded uppercase tracking-wider font-medium">{n}</span>
                      ))}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-[#777777] mb-4">
                      <span className="flex items-center gap-1">
                        <span className="material-symbols-outlined" style={{fontSize:13}}>people</span>
                        {fmt(r.creator.followers)}
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="material-symbols-outlined" style={{fontSize:13}}>trending_up</span>
                        {(r.creator.engagement_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                    <button onClick={() => { setSelectedCreator(r.creator._id ?? r.creator.id ?? ''); setDealResult(null); setOfferError('') }}
                      className="w-full border border-black text-black text-xs font-bold py-2 rounded-lg hover:bg-black hover:text-white transition-all">
                      Send Offer
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Offer Modal */}
      {selectedCreator && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
          <div className="bg-white rounded-xl p-8 w-full max-w-md shadow-2xl border border-[#e8e8e8]">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-[#777777]">New Offer</p>
                <h3 className="text-xl font-headline font-bold text-black">Deploy Capital</h3>
              </div>
              <button onClick={() => setSelectedCreator(null)} className="text-[#777777] hover:text-black">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {dealResult ? (
              <div className="text-center py-6">
                <div className="w-16 h-16 bg-black rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="material-symbols-outlined text-white" style={{fontSize:28}}>check</span>
                </div>
                <p className="font-headline font-bold text-black text-lg mb-1">Offer Deployed</p>
                <p className="text-xs text-[#777777] uppercase tracking-widest">Status: <span className="font-bold text-black">{dealResult.status}</span></p>
                <button onClick={() => setSelectedCreator(null)}
                  className="mt-6 bg-black text-white px-8 py-2.5 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity">
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleOffer} className="space-y-4">
                {[
                  { label: 'Offer Amount (USD)', type: 'number', val: offerAmount, set: setOfferAmount, placeholder: '2500', min: '1' },
                  { label: 'Deliverables', type: 'text', val: deliverables, set: setDeliverables, placeholder: '1 Instagram Reel + 2 Stories' },
                  { label: 'Deadline', type: 'date', val: deadline, set: setDeadline, placeholder: '' },
                ].map(f => (
                  <div key={f.label}>
                    <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">{f.label}</label>
                    <input type={f.type} value={f.val} onChange={e => f.set(e.target.value)}
                      placeholder={f.placeholder} required min={f.min}
                      className="w-full border border-[#e2e2e2] rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors" />
                  </div>
                ))}
                {offerError && <p className="text-xs text-red-600">{offerError}</p>}
                <button type="submit" disabled={offerLoading}
                  className="w-full bg-black text-white py-3 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50">
                  {offerLoading ? 'Deploying...' : 'Deploy Offer'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Counter Response Modal */}
      {selectedDeal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
          <div className="bg-white rounded-xl p-8 w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl border border-[#e8e8e8]">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-[#777777]">Counter Offer</p>
                <h3 className="text-xl font-headline font-bold text-black">Respond to Creator</h3>
              </div>
              <button onClick={() => { setSelectedDeal(null); setShowBusinessCounterForm(false) }} className="text-[#777777] hover:text-black">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm mb-2"><span className="font-bold">Original Offer:</span> ${selectedDeal.offer_amount}</p>
              {selectedDeal.counter_amount && (
                <p className="text-sm mb-2"><span className="font-bold">Counter Amount:</span> ${selectedDeal.counter_amount}</p>
              )}
              <p className="text-sm mb-2"><span className="font-bold">Deliverables:</span> {selectedDeal.deliverables}</p>
              {selectedDeal.counter_deliverables && (
                <p className="text-sm mb-2"><span className="font-bold">Counter Deliverables:</span> {selectedDeal.counter_deliverables}</p>
              )}
              {selectedDeal.counter_message && (
                <div className="mt-3 p-3 bg-yellow-50 rounded border border-yellow-200">
                  <p className="text-xs font-bold mb-1">Creator Message:</p>
                  <p className="text-sm">{selectedDeal.counter_message}</p>
                </div>
              )}
            </div>

            {dealActionError && <p className="text-xs text-red-600 mb-3">{dealActionError}</p>}

            {!showBusinessCounterForm && !showAcceptConfirmation && (
              <div className="space-y-2">
                <button onClick={() => {
                  if (hasTermsChanged(selectedDeal)) {
                    setShowAcceptConfirmation(true)
                  } else {
                    handleAcceptCounter(selectedDeal.id ?? selectedDeal._id ?? '')
                  }
                }} 
                  disabled={dealActionLoading}
                  className="w-full bg-black text-white py-2.5 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50">
                  {dealActionLoading ? 'Processing...' : 'Accept Counter'}
                </button>
                <button onClick={() => setShowBusinessCounterForm(true)} 
                  disabled={dealActionLoading}
                  className="w-full border border-black text-black py-2.5 rounded-lg text-sm font-bold hover:bg-black hover:text-white transition-all">
                  Counter Back
                </button>
                <button onClick={() => handleRejectCounter(selectedDeal.id ?? selectedDeal._id ?? '')} 
                  disabled={dealActionLoading}
                  className="w-full border border-gray-300 text-gray-700 py-2.5 rounded-lg text-sm font-bold hover:bg-gray-100 transition-all">
                  {dealActionLoading ? 'Processing...' : 'Reject Counter'}
                </button>
              </div>
            )}

            {showAcceptConfirmation && (
              <div className="space-y-3">
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-xs font-bold text-yellow-900 mb-2">⚠️ TERMS HAVE CHANGED</p>
                  <p className="text-sm text-yellow-900 mb-3">
                    The creator has proposed different terms. By accepting, you agree to:
                  </p>
                  <div className="space-y-2 text-sm">
                    {selectedDeal.counter_amount && selectedDeal.counter_amount !== selectedDeal.offer_amount && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Amount:</span>
                        <span className="font-bold">
                          <span className="line-through text-gray-400">${selectedDeal.offer_amount}</span>
                          {' → '}
                          <span className="text-yellow-900">${selectedDeal.counter_amount}</span>
                        </span>
                      </div>
                    )}
                    {selectedDeal.counter_deliverables && selectedDeal.counter_deliverables !== selectedDeal.deliverables && (
                      <div>
                        <p className="text-gray-600 mb-1">Deliverables changed:</p>
                        <p className="text-xs text-gray-500 line-through">{selectedDeal.deliverables}</p>
                        <p className="text-xs text-yellow-900 font-bold mt-1">{selectedDeal.counter_deliverables}</p>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleAcceptCounter(selectedDeal.id ?? selectedDeal._id ?? '')} 
                    disabled={dealActionLoading}
                    className="flex-1 bg-black text-white py-2.5 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50">
                    {dealActionLoading ? 'Processing...' : 'Confirm Accept'}
                  </button>
                  <button onClick={() => setShowAcceptConfirmation(false)}
                    disabled={dealActionLoading}
                    className="flex-1 border border-gray-300 py-2.5 rounded-lg text-sm font-bold hover:bg-gray-100 transition-all">
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {showBusinessCounterForm && (
              <form onSubmit={handleBusinessCounter} className="space-y-3">
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Message (optional)</label>
                  <textarea value={businessCounterMessage} onChange={e => setBusinessCounterMessage(e.target.value)}
                    placeholder="Explain your counter offer..."
                    className="w-full border border-[#e2e2e2] rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors resize-none" 
                    rows={3} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Counter Amount (optional)</label>
                  <input type="number" value={businessCounterAmount} onChange={e => setBusinessCounterAmount(e.target.value)}
                    placeholder="Enter new amount" min="0.01" step="0.01"
                    className="w-full border border-[#e2e2e2] rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors" />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Counter Deliverables (optional)</label>
                  <textarea value={businessCounterDeliverables} onChange={e => setBusinessCounterDeliverables(e.target.value)}
                    placeholder="Propose modified deliverables..."
                    className="w-full border border-[#e2e2e2] rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors resize-none" 
                    rows={2} />
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={dealActionLoading}
                    className="flex-1 bg-black text-white py-2.5 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50">
                    {dealActionLoading ? 'Sending...' : 'Send Counter'}
                  </button>
                  <button type="button" onClick={() => setShowBusinessCounterForm(false)}
                    className="flex-1 border border-gray-300 py-2.5 rounded-lg text-sm font-bold hover:bg-gray-100 transition-all">
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </Layout>
  )
}
