import { NavLink } from 'react-router-dom'
import { haptic } from '../lib/format'
import { useAuction } from '../store/auctionStore'

const TABS = [
  { to: '/auction', label: 'Auction', icon: '🔨' },
  { to: '/squad', label: 'Squad', icon: '👥' },
  { to: '/teams', label: 'Teams', icon: '🏆' },
  { to: '/pool', label: 'Players', icon: '🔍' },
]

export function TabBar() {
  const room = useAuction((s) => s.room)
  const teamId = useAuction((s) => s.teamId)
  const myTeam = room?.teams.find((t) => t.id === teamId)

  return (
    <nav className="app-tabbar">
      <div className="flex">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            onClick={() => haptic(8)}
            className={({ isActive }) =>
              `flex-1 h-[60px] flex flex-col items-center justify-center gap-0.5 relative ${
                isActive ? 'text-indigo-300' : 'text-slate-500'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute top-0 w-8 h-0.5 rounded-full bg-indigo-400" />
                )}
                <span className="text-lg leading-none">{tab.icon}</span>
                <span className="text-[10px] font-semibold tracking-wide">{tab.label}</span>
                {tab.to === '/squad' && myTeam && (
                  <span className="absolute top-2 right-[22%] text-[9px] font-bold text-slate-400 tabular-nums">
                    {myTeam.squad_size}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
