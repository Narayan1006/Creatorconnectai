import CampaignCard from '../components/CampaignCard'
import CollaboratorCard from '../components/CollaboratorCard'
import RecentActivity from '../components/RecentActivity'
import ImpressionsCard from '../components/ImpressionsCard'

const collaborators = [
  { matchScore: 98, name: 'Elena Voss', specialty: 'Generative High Fashion' },
  { matchScore: 94, name: 'Marcus Aris', specialty: 'Architectural AI Specialist' },
  { matchScore: 91, name: 'Sasha Grey', specialty: 'Motion Art & Diffusion' },
]

export default function Dashboard() {
  return (
    <div className="flex-1 flex flex-col">
      <div className="flex flex-1">
        {/* Main content */}
        <main className="flex-1 min-w-0 px-8 py-8">
          {/* Page header */}
          <div className="mb-8">
            <h1 className="text-[1.75rem] font-semibold text-on_surface tracking-tight leading-tight">
              Studio Overview
            </h1>
            <p className="text-sm text-on_surface_variant mt-1">
              Welcome back. Your active campaigns are performing 12% above benchmark.
            </p>
          </div>

          {/* Campaign cards row */}
          <div className="flex gap-4 mb-8">
            <CampaignCard
              icon="auto_awesome"
              status="ACTIVE"
              title="Cyber-Summer Editorial"
              subtitle="AI Lifestyle & Fashion Fusion"
              progressLabel="Generation Progress"
              progress={84}
            />
            <CampaignCard
              icon="architecture"
              status="DRAFTING"
              title="Ethereal Spaces v2"
              subtitle="Interior Design Concepts"
              progressLabel="Optimization"
              progress={32}
            />
            {/* Right panel placeholder to match layout */}
            <div className="w-[260px] shrink-0" />
          </div>

          {/* Recommended collaborators */}
          <div className="mb-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-on_surface">Recommended Collaborators</h2>
              <button className="text-sm font-medium text-primary hover:opacity-80 transition-opacity">
                View All Matches
              </button>
            </div>
            <div className="flex gap-4">
              {collaborators.map((c) => (
                <CollaboratorCard key={c.name} {...c} />
              ))}
            </div>
          </div>
        </main>

        {/* Right sidebar panel */}
        <aside className="w-[260px] shrink-0 px-4 py-8 flex flex-col gap-0">
          <RecentActivity />
          <ImpressionsCard />
        </aside>
      </div>
    </div>
  )
}
