import { useState, useEffect } from 'react'
import axios from 'axios'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Deal {
  id?: string
  _id?: string
  business_id: string
  creator_id: string
  offer_amount: number
  deliverables: string
  deadline: string
  status: string
  ad_idea?: string
  content_url?: string
}

interface CreatorProfile {
  id?: string
  _id?: string
  name: string
  avatar_url?: string
  niche: string[]
  platform: string
  followers: number
  engagement_rate: number
  bio: string
}

function fmt(n: number) {
  if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n/1_000).toFixed(0)}K`
  return String(n)
}

export default function CreatorDashboard() {
  const { token } = useAuth()
  const [deals, setDeals] = useState<Deal[]>([])
  const [profile, setProfile] = useState<CreatorProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null)
  const [contentUrl, setContentUrl] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  const fetchProfile = async () => {
    try {
      const res = await axios.get<CreatorProfile>(`${API_BASE}/api/creators/me`, { headers: { Authorization: `Bearer ${token}` } })
      setProfile(res.data)
    } catch (err: any) {
      if (err?.response?.status === 404) setProfile(null)
      else setError('Failed to load profile')
    }
  }

  const fetchDeals = async () => {
    try {
      const res = await axios.get<Deal[]>(`${API_BASE}/api/deals`, { headers: { Authorization: `Bearer ${token}` } })
      setDeals(res.data)
    } catch {
      setError('Failed to load deals')
    }
  }

  const handleAccept = async (dealId: string) => {
    setActionLoading(true); setActionError('')
    try {
      await axios.put(`${API_BASE}/api/deals/${dealId}/accept`, {}, { headers: { Authorization: `Bearer ${token}` } })
      await fetchDeals()
      setSelectedDeal(null)
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? 'Failed to accept deal')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async (dealId: string) => {
    setActionLoading(true); setActionError('')
    try {
      await axios.put(`${API_BASE}/api/deals/${dealId}/reject`, {}, { headers: { Authorization: `Bearer ${token}` } })
      await fetchDeals()
      setSelectedDeal(null)
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? 'Failed to reject deal')
    } finally {
      setActionLoading(false)
    }
  }

  const handleCounter = async (dealId: string) => {
    setActionLoading(true); setActionError('')
    try {
      await axios.put(`${API_BASE}/api/deals/${dealId}/counter`, {}, { headers: { Authorization: `Bearer ${token}` } })
      await fetchDeals()
      setSelectedDeal(null)
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? 'Failed to counter deal')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSubmitContent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDeal) return
    const dealId = selectedDeal.id ?? selectedDeal._id ?? ''
    setActionLoading(true); setActionError('')
    try {
      await axios.post(`${API_BASE}/api/deals/${dealId}/submit`, { content_url: contentUrl }, { headers: { Authorization: `Bearer ${token}` } })
      await fetchDeals()
      setSelectedDeal(null)
      setContentUrl('')
    } catch (err: any) {
      setActionError(err?.response?.data?.detail ?? 'Failed to submit content')
    } finally {
      setActionLoading(false)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await fetchProfile()
      await fetchDeals()
      setLoading(false)
    }
    loadData()
  }, [])

  if (loading) {
    return <Layout><div className="px-8 py-8"><p>Loading...</p></div></Layout>
  }

  if (error) {
    return <Layout><div className="px-8 py-8"><p className="text-red-600">{error}</p></div></Layout>
  }

  const pendingDeals = deals.filter(d => d.status === 'pending')
  const acceptedDeals = deals.filter(d => d.status === 'accepted')

  return (
    <Layout>
      <div className="px-8 py-8 max-w-6xl">
        <h1 className="text-3xl font-bold mb-6">Creator Dashboard</h1>
        
        {profile && (
          <div className="bg-white border rounded-xl p-6 mb-6">
            <p className="font-bold text-lg">{profile.name}</p>
            <p className="text-sm text-gray-600">{profile.niche.join(', ')}</p>
            <p className="text-sm">{fmt(profile.followers)} followers</p>
          </div>
        )}

        {deals.length === 0 && <p>No deals yet</p>}

        {pendingDeals.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-bold mb-4">Pending Offers ({pendingDeals.length})</h2>
            <div className="grid gap-4">
              {pendingDeals.map(deal => (
                <div key={deal.id ?? deal._id} className="bg-white border rounded-xl p-5">
                  <p className="font-bold">${deal.offer_amount}</p>
                  <p className="text-sm">{deal.deliverables}</p>
                  <button onClick={() => setSelectedDeal(deal)} className="mt-2 px-4 py-2 bg-black text-white rounded">
                    Review
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {acceptedDeals.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-bold mb-4">Accepted Deals ({acceptedDeals.length})</h2>
            <div className="grid gap-4">
              {acceptedDeals.map(deal => (
                <div key={deal.id ?? deal._id} className="bg-white border rounded-xl p-5">
                  <p className="font-bold">${deal.offer_amount}</p>
                  <p className="text-sm">{deal.deliverables}</p>
                  {deal.ad_idea && <p className="text-sm mt-2 bg-gray-100 p-2 rounded">{deal.ad_idea}</p>}
                  <button onClick={() => setSelectedDeal(deal)} className="mt-2 px-4 py-2 bg-black text-white rounded">
                    Submit Content
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {selectedDeal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="bg-white rounded-xl p-8 w-full max-w-md">
            <div className="flex justify-between mb-4">
              <h3 className="text-xl font-bold">Deal Details</h3>
              <button onClick={() => setSelectedDeal(null)}>×</button>
            </div>
            <p className="mb-2">Amount: ${selectedDeal.offer_amount}</p>
            <p className="mb-4">{selectedDeal.deliverables}</p>
            {actionError && <p className="text-red-600 text-sm mb-2">{actionError}</p>}
            {selectedDeal.status === 'pending' && (
              <div className="space-y-2">
                <button onClick={() => handleAccept(selectedDeal.id ?? selectedDeal._id ?? '')} disabled={actionLoading}
                  className="w-full bg-black text-white py-2 rounded">
                  {actionLoading ? 'Processing...' : 'Accept'}
                </button>
                <button onClick={() => handleCounter(selectedDeal.id ?? selectedDeal._id ?? '')} disabled={actionLoading}
                  className="w-full border border-black py-2 rounded">
                  Counter
                </button>
                <button onClick={() => handleReject(selectedDeal.id ?? selectedDeal._id ?? '')} disabled={actionLoading}
                  className="w-full border py-2 rounded">
                  Reject
                </button>
              </div>
            )}
            {selectedDeal.status === 'accepted' && (
              <form onSubmit={handleSubmitContent}>
                <input type="url" value={contentUrl} onChange={e => setContentUrl(e.target.value)}
                  placeholder="Content URL" required className="w-full border rounded px-3 py-2 mb-2" />
                <button type="submit" disabled={actionLoading}
                  className="w-full bg-black text-white py-2 rounded">
                  {actionLoading ? 'Submitting...' : 'Submit'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </Layout>
  )
}
