import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const PLATFORMS = ['youtube', 'instagram', 'tiktok']
const NICHE_OPTIONS = ['tech', 'fashion', 'lifestyle', 'fitness', 'food', 'travel', 'gaming', 'finance', 'education', 'beauty', 'music', 'art']

export default function RegisterPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [role, setRole] = useState<'business' | 'creator'>('business')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Common
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Business fields
  const [companyName, setCompanyName] = useState('')
  const [industry, setIndustry] = useState('')

  // Creator fields
  const [creatorName, setCreatorName] = useState('')
  const [bio, setBio] = useState('')
  const [platform, setPlatform] = useState('youtube')
  const [followers, setFollowers] = useState('')
  const [engagementRate, setEngagementRate] = useState('')
  const [selectedNiches, setSelectedNiches] = useState<string[]>([])
  const [portfolioUrl, setPortfolioUrl] = useState('')

  const toggleNiche = (n: string) =>
    setSelectedNiches(prev => prev.includes(n) ? prev.filter(x => x !== n) : [...prev, n])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (role === 'creator' && selectedNiches.length === 0) {
      setError('Please select at least one niche.')
      return
    }

    setLoading(true)
    try {
      // 1. Register auth account
      const payload: Record<string, string> = { email, password, role }
      if (role === 'business') {
        payload.company_name = companyName
        payload.industry = industry
      }
      await axios.post(`${API_BASE}/api/auth/register`, payload)

      // 2. Login to get token
      const loginRes = await axios.post(
        `${API_BASE}/api/auth/login`,
        new URLSearchParams({ username: email, password }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      )
      const token = loginRes.data.access_token
      login(token, loginRes.data.user)

      // 3. If creator, create profile
      if (role === 'creator') {
        await axios.post(
          `${API_BASE}/api/creators`,
          {
            name: creatorName,
            avatar_url: '',
            niche: selectedNiches,
            platform,
            followers: parseInt(followers),
            engagement_rate: parseFloat(engagementRate) / 100,
            bio,
            portfolio_url: portfolioUrl || undefined,
          },
          { headers: { Authorization: `Bearer ${token}` } }
        )
      }

      navigate(role === 'business' ? '/business' : '/creator')
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = "w-full border border-[#e2e2e2] bg-white rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors"
  const labelCls = "text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2"

  return (
    <div className="min-h-screen bg-[#f9f9f9] font-body flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-black text-white flex-col justify-between p-16">
        <div className="text-xl font-black font-headline tracking-tighter">CreatorConnectAI</div>
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-white/40 mb-4">Join the Ecosystem</p>
          <h2 className="text-4xl font-headline font-extrabold tracking-tighter leading-tight mb-6">
            The Future of<br />Influence is<br />Algorithmic.
          </h2>
          <p className="text-white/60 text-lg leading-relaxed max-w-sm">
            Join the private beta of the world's most disciplined creator marketplace.
          </p>
        </div>
        <p className="text-[10px] text-white/30 uppercase tracking-widest">Limited spots available for Q4 intake.</p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center px-8 py-12 overflow-y-auto">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h1 className="text-3xl font-headline font-extrabold tracking-tighter text-black mb-2">Create account.</h1>
            <p className="text-[#474747] text-sm">Secure your position in the ecosystem.</p>
          </div>

          {/* Role toggle */}
          <div className="grid grid-cols-2 gap-2 mb-6 p-1 bg-[#eeeeee] rounded-lg">
            {(['business', 'creator'] as const).map(r => (
              <button key={r} type="button" onClick={() => setRole(r)}
                className={`py-2.5 rounded-md text-sm font-bold transition-all ${role === r ? 'bg-black text-white shadow-sm' : 'text-[#474747] hover:text-black'}`}>
                {r === 'business' ? 'Enterprise' : 'Creator'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Common fields */}
            <div>
              <label className={labelCls}>Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required className={inputCls} />
            </div>
            <div>
              <label className={labelCls}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required minLength={8} className={inputCls} />
            </div>

            {/* Business fields */}
            {role === 'business' && (
              <>
                <div>
                  <label className={labelCls}>Company Name</label>
                  <input type="text" value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder="Acme Corp" required className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>Industry</label>
                  <input type="text" value={industry} onChange={e => setIndustry(e.target.value)} placeholder="Fashion, Tech, Beauty..." required className={inputCls} />
                </div>
              </>
            )}

            {/* Creator fields */}
            {role === 'creator' && (
              <>
                <div>
                  <label className={labelCls}>Your Name</label>
                  <input type="text" value={creatorName} onChange={e => setCreatorName(e.target.value)} placeholder="Alex Rivera" required className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>Bio</label>
                  <textarea value={bio} onChange={e => setBio(e.target.value)} placeholder="Tell brands about your content and audience..." required rows={3}
                    className="w-full border border-[#e2e2e2] bg-white rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors resize-none" />
                </div>
                <div>
                  <label className={labelCls}>Platform</label>
                  <select value={platform} onChange={e => setPlatform(e.target.value)} className={inputCls}>
                    {PLATFORMS.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelCls}>Followers</label>
                    <input type="number" value={followers} onChange={e => setFollowers(e.target.value)} placeholder="250000" required min={1} className={inputCls} />
                  </div>
                  <div>
                    <label className={labelCls}>Engagement %</label>
                    <input type="number" value={engagementRate} onChange={e => setEngagementRate(e.target.value)} placeholder="4.5" required min={0.1} max={100} step={0.1} className={inputCls} />
                  </div>
                </div>
                <div>
                  <label className={labelCls}>Niche (select all that apply)</label>
                  <div className="flex flex-wrap gap-2">
                    {NICHE_OPTIONS.map(n => (
                      <button key={n} type="button" onClick={() => toggleNiche(n)}
                        className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all capitalize ${
                          selectedNiches.includes(n) ? 'bg-black text-white border-black' : 'bg-white text-[#474747] border-[#e2e2e2] hover:border-black'
                        }`}>
                        {n}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className={labelCls}>Portfolio URL (optional)</label>
                  <input type="url" value={portfolioUrl} onChange={e => setPortfolioUrl(e.target.value)} placeholder="https://yourportfolio.com" className={inputCls} />
                </div>
              </>
            )}

            {error && <p className="text-xs text-red-600">{error}</p>}

            <button type="submit" disabled={loading}
              className="w-full bg-black text-white py-3 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50">
              {loading ? (role === 'creator' ? 'Setting up profile...' : 'Creating account...') : 'Secure My Position'}
            </button>
          </form>

          <p className="text-center text-sm mt-6 text-[#474747]">
            Already have an account?{' '}
            <Link to="/login" className="text-black font-bold hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
