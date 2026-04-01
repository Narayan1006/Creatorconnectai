interface ActivityItem {
  text: string
  time: string
}

const activities: ActivityItem[] = [
  { text: 'Model V4.2 training completed successfully.', time: '2 hours ago' },
  { text: 'New collaboration request from Studio Noir.', time: '5 hours ago' },
  { text: 'Monthly earnings of $4,280.00 processed.', time: 'Yesterday' },
]

export default function RecentActivity() {
  return (
    <div className="bg-surface_container_lowest rounded-xl p-5 shadow-ambient">
      <h3 className="text-label-upper text-on_surface_variant mb-4">Recent Activity</h3>

      <div className="flex flex-col gap-4">
        {activities.map((item, i) => (
          <div key={i} className="flex gap-3 items-start">
            <div className="w-1.5 h-1.5 rounded-full bg-on_surface_variant mt-1.5 shrink-0" />
            <div>
              <p className="text-sm text-on_surface leading-snug"
                dangerouslySetInnerHTML={{
                  __html: item.text.replace(
                    /Studio Noir|\$4,280\.00/g,
                    (m) => `<strong class="font-semibold">${m}</strong>`
                  ),
                }}
              />
              <p className="text-xs text-on_surface_variant mt-0.5">{item.time}</p>
            </div>
          </div>
        ))}
      </div>

      <button className="mt-5 text-label-upper text-xs text-on_surface_variant hover:text-on_surface transition-colors tracking-widest">
        Clear Notifications
      </button>
    </div>
  )
}
