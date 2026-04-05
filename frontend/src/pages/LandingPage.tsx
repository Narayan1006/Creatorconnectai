import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="bg-[#f9f9f9] font-body text-[#1a1c1c] min-h-screen">

      {/* ── TopNavBar ── */}
      <nav className="fixed top-0 w-full z-50 bg-neutral-50/80 backdrop-blur-xl shadow-[0_10px_40px_rgba(0,0,0,0.04)]">
        <div className="flex justify-between items-center w-full px-8 py-4 max-w-7xl mx-auto">
          <div className="text-xl font-bold tracking-tighter text-black font-headline">CreatorConnectAI</div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="font-headline tracking-tight text-sm font-medium text-neutral-500 hover:text-black transition-colors">
              Login
            </button>
            <button
              onClick={() => navigate('/register')}
              className="bg-black text-[#e2e2e2] px-5 py-2 text-sm font-medium rounded-md hover:opacity-90 transition-opacity">
              Join Waitlist
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative pt-40 pb-24 px-8 overflow-hidden">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
          <div className="lg:col-span-7 space-y-8">
            <span className="text-[#777777] tracking-widest uppercase font-semibold text-xs bg-[#eeeeee] px-3 py-1 rounded">
              Intelligence for Influence
            </span>
            <h1 className="text-5xl md:text-7xl font-extrabold font-headline tracking-tighter leading-[1.05] text-black">
              Precision-Matched <br/>Creator Capital
            </h1>
            <p className="text-xl text-[#474747] max-w-xl leading-relaxed">
              The Monolithic Curator for high-growth brands. Deploy AI to architect perfect creator alignments, manage verified submissions, and automate capital flow.
            </p>
            <div className="flex flex-wrap gap-4 pt-4">
              <button
                onClick={() => navigate('/register')}
                className="bg-black text-[#e2e2e2] px-8 py-4 text-base font-semibold rounded-md shadow-lg flex items-center gap-2 hover:scale-[1.02] transition-all">
                Join the Ecosystem
                <span className="material-symbols-outlined text-lg">arrow_forward</span>
              </button>
              <button
                onClick={() => navigate('/business')}
                className="bg-[#e2e2e2] text-black px-8 py-4 text-base font-semibold rounded-md flex items-center gap-2 hover:bg-[#dadada] transition-colors">
                Explore Marketplace
              </button>
            </div>
          </div>

          <div className="lg:col-span-5 relative">
            <div className="relative z-10 aspect-[4/5] rounded-xl overflow-hidden bg-[#e8e8e8] shadow-2xl">
              <img
                className="w-full h-full object-cover grayscale opacity-90"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuBjjA3rS6tTj4eW-fPmsadaslljRdOHrU98ZGZcA_4ioqtBbC-Kz1f8Q_XCFtC_5n-9zIsdyPqv7LPbtYd3d3EV0bSCGVxs03oA9vrggga4DOw1I7_hoW2Rt4QSY2SaDv4fHhkud9Y1KCEZcijLPpyljyrzb5_KG797TQYjqG_Z9trojZ9hDnHqy_M92fnTPEmvhGY0fxPWX6wmwm-HFGUJktUG1FP9bK54C1OAuMIuP2TjSvunNiL4pReVY2DeOuFzDyhE_gRan_R8"
                alt="Abstract architectural monochrome"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
              <div className="absolute bottom-6 left-6 right-6 glass-panel p-6 rounded-lg border border-white/10">
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-xs font-bold text-black mb-1 uppercase tracking-widest">Active Campaign</p>
                    <p className="text-lg font-headline font-bold text-black">Curated Collective Vol. 1</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold font-headline">$142.5k</p>
                    <p className="text-[10px] text-[#777777] uppercase tracking-widest">Allocated</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -top-12 -right-12 w-64 h-64 bg-[#eeeeee] rounded-full mix-blend-multiply filter blur-3xl opacity-70" />
            <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-[#e2e2e2] rounded-full mix-blend-multiply filter blur-3xl opacity-50" />
          </div>
        </div>
      </section>

      {/* ── Social Proof ── */}
      <section className="py-12 bg-[#f3f3f4] border-y border-[#c6c6c6]/10">
        <div className="max-w-7xl mx-auto px-8">
          <p className="text-center text-[10px] font-bold text-[#777777] uppercase tracking-[0.3em] mb-10">
            Trusted by The Vanguard of Commerce
          </p>
          <div className="flex flex-wrap justify-center gap-x-16 gap-y-8 opacity-40 grayscale">
            {['NEVADA.','AXIOM','VIRTUE','SYNERGY','MONOLITH'].map(b => (
              <div key={b} className="text-xl font-black font-headline">{b}</div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features Bento Grid ── */}
      <section className="py-24 px-8 bg-[#f9f9f9]">
        <div className="max-w-7xl mx-auto">
          <div className="mb-20 text-center max-w-2xl mx-auto">
            <h2 className="text-4xl font-headline font-extrabold tracking-tighter text-black mb-6">
              The Curator's Methodology
            </h2>
            <p className="text-[#474747] text-lg">
              A frictionless pipeline designed for the precision of luxury brands and the agility of elite creators.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Discovery Engine — large */}
            <div className="md:col-span-2 bg-[#f3f3f4] rounded-xl p-10 flex flex-col justify-between group overflow-hidden relative">
              <div className="z-10">
                <div className="w-12 h-12 bg-black text-[#e2e2e2] flex items-center justify-center rounded-lg mb-8">
                  <span className="material-symbols-outlined">insights</span>
                </div>
                <h3 className="text-3xl font-headline font-bold mb-4">Discovery Engine</h3>
                <p className="text-[#474747] text-lg max-w-md leading-relaxed">
                  Our AI analyzes over 400 data points to find creators whose aesthetic DNA matches your brand's core values.
                </p>
              </div>
              <div className="mt-12 z-10">
                <button className="text-black font-bold flex items-center gap-2 group-hover:gap-4 transition-all">
                  Learn about AI Matching
                  <span className="material-symbols-outlined">arrow_right_alt</span>
                </button>
              </div>
              <div className="absolute bottom-0 right-0 w-1/2 h-full opacity-10 group-hover:scale-105 transition-transform duration-700">
                <img
                  className="w-full h-full object-cover grayscale"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuByqt-xUJ7aiLBuWfDLKBapv0nWEvNQqH8dEQJChvwJSq0r783FSlgjc01DFvvKHap5-A1TR2v01pLijwXbGsamNceLTxFcgeWon1pYSS0YQIT29B4ZoV-NyUPjO83eNbvtMdmduwY9aod1FPZHjS_fnqsaWo3NB0R8p7Z7Rson7wIsXTEm2XBWC0VBOiX8HKfGErwsrYEiGGsM9T13RNpHeGje_C_qFXoH3fNZ3kSL57ZBQZPmHCFjFsntKiNmq3lRUUYS8sxXGU-M"
                  alt=""
                />
              </div>
            </div>

            {/* AI Ideas */}
            <div className="bg-[#e2e2e2] rounded-xl p-10 flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 bg-white text-black flex items-center justify-center rounded-lg mb-8 shadow-sm">
                  <span className="material-symbols-outlined">layers</span>
                </div>
                <h3 className="text-2xl font-headline font-bold mb-4">AI Ideas</h3>
                <p className="text-[#474747] leading-relaxed">
                  Generate campaign concepts that resonate instantly with target demographics.
                </p>
              </div>
              <div className="mt-8">
                <div className="h-1 w-full bg-[#eeeeee] rounded-full overflow-hidden">
                  <div className="h-full bg-black w-2/3" />
                </div>
                <p className="text-[10px] mt-2 uppercase tracking-widest font-bold text-[#777777]">Conceptual Accuracy</p>
              </div>
            </div>

            {/* Verified Intake */}
            <div className="bg-white rounded-xl p-10 flex flex-col justify-between shadow-[0_10px_40px_rgba(0,0,0,0.03)] border border-[#c6c6c6]/10">
              <div>
                <div className="w-12 h-12 bg-[#f3f3f4] text-black flex items-center justify-center rounded-lg mb-8">
                  <span className="material-symbols-outlined">verified</span>
                </div>
                <h3 className="text-2xl font-headline font-bold mb-4">Verified Intake</h3>
                <p className="text-[#474747] leading-relaxed">
                  Automated quality control for all creator submissions before they reach your desk.
                </p>
              </div>
              <div className="mt-8 flex -space-x-3">
                {[
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuC4fQBgJz7Owf-ktjPTWdPMqv7Zj3kHZVzJozTxw61Bh6JC7tmlhnoNzVD2-kT_0IQQaDwQhfUJLC07sJBcMhOEkcLVO7TceOeccoQjUcIgRwtPl_x4QDH9W0FHvHsm6t0vWlIh-uwsPJW0oWesD60c1r8kxguAKEvj23iaEXOsmAVaPa4yTDBBhuMSH9N6XMjgnNxoq65X24wZk9VENbzFtvteozic9G0Ev32SLOOTgHxzM814VtIiMyFX2Tg0_mwL8Z3172C7VcYs',
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuARyFxA60voG9v6VoLmLVsU4dd23b72jBkEsB5cYG8mCsFK9x0naV_OkBbKJglAzBMvJO8rdCBOXwiS08F6EmSPgMk8gfv28WCILnc_my7Pkx9fZ70LlMcTizkQpwJpSywB6WGf1p1awVbii_jusZcwbYMd9h3V9s3hDGrs_iccZpEOieTS1Q8zCt0mDR38rTYTW87yhP3ypgY53bLu3IDQdsnBjbE1U6BiQqlcqCo5eIcxWK49WnQdChkdVBpDxJLJMz0yEgfqwjjX',
                ].map((src, i) => (
                  <div key={i} className="w-10 h-10 rounded-full border-2 border-white bg-[#e2e2e2] overflow-hidden">
                    <img className="w-full h-full object-cover grayscale" src={src} alt="" />
                  </div>
                ))}
                <div className="w-10 h-10 rounded-full border-2 border-white bg-[#e2e2e2] flex items-center justify-center text-[10px] font-bold">+12k</div>
              </div>
            </div>

            {/* Automated Capital Flow — large dark */}
            <div className="md:col-span-2 bg-black text-[#e2e2e2] rounded-xl p-10 flex flex-col md:flex-row gap-12 items-center">
              <div className="flex-1">
                <div className="w-12 h-12 bg-[#e2e2e2] text-black flex items-center justify-center rounded-lg mb-8">
                  <span className="material-symbols-outlined">payments</span>
                </div>
                <h3 className="text-3xl font-headline font-bold mb-4">Automated Capital Flow</h3>
                <p className="text-[#e2e2e2]/70 text-lg leading-relaxed">
                  Instant smart-contract payments upon milestone approval. Scale your budget without the administrative overhead.
                </p>
                <button className="mt-8 bg-[#e2e2e2] text-black px-6 py-3 text-sm font-bold rounded-md hover:bg-[#e2e2e2]/80 transition-colors">
                  Setup Payment Rails
                </button>
              </div>
              <div className="w-full md:w-1/3 bg-[#3b3b3b] rounded-lg p-6 space-y-4">
                <div className="flex justify-between items-center text-xs border-b border-white/10 pb-3">
                  <span className="opacity-60">Status</span>
                  <span className="bg-white/10 px-2 py-0.5 rounded text-[10px]">Processing</span>
                </div>
                <div className="space-y-1">
                  <div className="text-[10px] opacity-40 uppercase tracking-widest">Amount</div>
                  <div className="text-xl font-headline font-bold">$12,450.00</div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                  <span className="text-[10px] font-bold opacity-80">Verified Transaction</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Business vs Creator ── */}
      <section className="py-24 px-8 bg-[#f3f3f4]">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-1 px-1 bg-[#c6c6c6]/20 rounded-2xl overflow-hidden">
            {/* For Enterprise */}
            <div className="bg-[#f9f9f9] p-12 md:p-20">
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#777777] mb-4 block">For Enterprise</span>
              <h3 className="text-4xl font-headline font-extrabold mb-8">Architect Your Brand</h3>
              <ul className="space-y-6">
                {[
                  { title: 'Predictive ROI Engine', desc: 'Forecast campaign performance before the first dollar is spent.' },
                  { title: 'Legal & Compliance Vault', desc: 'Automated usage rights and contract management for global scaling.' },
                  { title: 'Multi-Channel Orchestration', desc: 'Synchronize creators across TikTok, Reels, and YouTube from one hub.' },
                ].map(item => (
                  <li key={item.title} className="flex gap-4">
                    <span className="material-symbols-outlined text-black">check_circle</span>
                    <div>
                      <p className="font-bold text-lg">{item.title}</p>
                      <p className="text-[#474747] text-sm">{item.desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => navigate('/register?role=business')}
                className="mt-12 w-full py-4 border border-black text-black font-bold hover:bg-black hover:text-white transition-all rounded-md">
                Request Demo
              </button>
            </div>

            {/* For Talent */}
            <div className="bg-white p-12 md:p-20">
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#777777] mb-4 block">For Talent</span>
              <h3 className="text-4xl font-headline font-extrabold mb-8">Elevate Your Practice</h3>
              <ul className="space-y-6">
                {[
                  { title: 'Premium Tier Access', desc: 'Connect with established brands looking for long-term partners, not one-offs.' },
                  { title: 'Instant Payouts', desc: 'No more net-30. Get paid the moment your content is approved.' },
                  { title: 'Creative Copilot', desc: 'AI tools to help you refine briefs and optimize your content for reach.' },
                ].map(item => (
                  <li key={item.title} className="flex gap-4">
                    <span className="material-symbols-outlined text-black" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                    <div>
                      <p className="font-bold text-lg">{item.title}</p>
                      <p className="text-[#474747] text-sm">{item.desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => navigate('/register?role=creator')}
                className="mt-12 w-full py-4 bg-black text-[#e2e2e2] font-bold rounded-md hover:shadow-xl transition-all">
                Apply to Join
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="py-32 px-8 bg-[#f9f9f9]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl md:text-6xl font-headline font-extrabold tracking-tighter mb-10 leading-none">
            The Future of Influence is Algorithmic.
          </h2>
          <p className="text-xl text-[#474747] mb-12 max-w-2xl mx-auto">
            Join the private beta of the world's most disciplined creator marketplace.
          </p>
          <div className="inline-flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => navigate('/register')}
              className="bg-black text-[#e2e2e2] px-12 py-5 text-lg font-bold rounded-md hover:scale-[1.03] transition-all">
              Secure Waitlist Position
            </button>
            <button className="bg-[#e2e2e2] text-black px-12 py-5 text-lg font-bold rounded-md hover:bg-[#dadada] transition-all">
              Talk to an Architect
            </button>
          </div>
          <p className="mt-8 text-[10px] text-[#777777] uppercase tracking-widest font-medium">
            Limited spots available for Q4 intake.
          </p>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="w-full border-t border-neutral-200/10 bg-neutral-100">
        <div className="flex flex-col md:flex-row justify-between items-center w-full px-12 py-10 max-w-7xl mx-auto">
          <div className="mb-8 md:mb-0 text-center md:text-left">
            <div className="text-sm font-bold text-black mb-2">CreatorConnectAI</div>
            <p className="text-[10px] tracking-widest uppercase text-neutral-400">
              © 2024 CreatorConnectAI. The Monolithic Curator.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-8">
            {['Privacy','Terms','Contact','API','Status'].map(l => (
              <a key={l} className="text-xs tracking-widest uppercase text-neutral-400 hover:text-black transition-all hover:underline" href="#">
                {l}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}
