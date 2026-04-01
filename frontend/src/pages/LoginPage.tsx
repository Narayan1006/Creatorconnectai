import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/api/auth/login`,
        new URLSearchParams({ username: email, password }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      )
      login(res.data.access_token, res.data.user)
      navigate(res.data.user.role === 'business' ? '/business' : '/creator')
    } catch {
      setError('Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f9f9f9] font-body flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-black text-white flex-col justify-between p-16">
        <div className="text-xl font-black font-headline tracking-tighter">CreatorConnectAI</div>
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-white/40 mb-4">The Monolithic Curator</p>
          <h2 className="text-4xl font-headline font-extrabold tracking-tighter leading-tight mb-6">
            Precision-Matched<br/>Creator Capital
          </h2>
          <p className="text-white/60 text-lg leading-relaxed max-w-sm">
            Deploy AI to architect perfect creator alignments, manage verified submissions, and automate capital flow.
          </p>
        </div>
        <p className="text-[10px] text-white/30 uppercase tracking-widest">© 2024 CreatorConnectAI</p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center px-8">
        <div className="w-full max-w-sm">
          <div className="mb-10">
            <h1 className="text-3xl font-headline font-extrabold tracking-tighter text-black mb-2">Welcome back.</h1>
            <p className="text-[#474747] text-sm">Sign in to your account to continue.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full border border-[#e2e2e2] bg-white rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors"
              />
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-widest text-[#777777] block mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full border border-[#e2e2e2] bg-white rounded-lg px-4 py-3 text-sm text-black placeholder:text-[#c6c6c6] outline-none focus:border-black transition-colors"
              />
            </div>

            {error && <p className="text-xs text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-black text-white py-3 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50 mt-2">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="text-center text-sm mt-8 text-[#474747]">
            Don't have an account?{' '}
            <Link to="/register" className="text-black font-bold hover:underline">Register</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
