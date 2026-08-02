import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { TabBar } from './components/TabBar'
import { Toast } from './components/ui'
import { RoomGate } from './RoomGate'
import AuctionRoom from './pages/AuctionRoom'
import Home from './pages/Home'
import Lobby from './pages/Lobby'
import MySquad from './pages/MySquad'
import PlayerPool from './pages/PlayerPool'
import Results from './pages/Results'
import RetentionPhase from './pages/RetentionPhase'
import Teams from './pages/Teams'
import { useAuction } from './store/auctionStore'

/** Routes that show the bottom tab bar. Setup flows are full-screen. */
const TAB_ROUTES = ['/auction', '/squad', '/teams', '/pool']

export default function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const room = useAuction((s) => s.room)
  const showTabs = TAB_ROUTES.some((r) => location.pathname.startsWith(r))

  // The room's phase is the source of truth for which screen you belong on, so a
  // reconnect or a phase change moves everyone without any manual navigation.
  useEffect(() => {
    if (!room) return
    const path = location.pathname
    if (room.status === 'RETENTION' && !path.startsWith('/retention')) {
      navigate('/retention', { replace: true })
    } else if (room.status === 'IN_PROGRESS' && (path === '/' || path.startsWith('/lobby') || path.startsWith('/retention'))) {
      navigate('/auction', { replace: true })
    } else if (room.status === 'COMPLETED' && !path.startsWith('/results')) {
      navigate('/results', { replace: true })
    }
  }, [room?.status, location.pathname, navigate, room])

  return (
    <div className="app-shell">
      <Toast />
      <Routes>
        <Route path="/" element={<Home />} />
        {/* The lobby sits outside RoomGate: someone joining by code has no user
            id until they claim a franchise, and there is no socket yet either. */}
        <Route path="/lobby" element={<Lobby />} />
        <Route element={<RoomGate />}>
          <Route path="/retention" element={<RetentionPhase />} />
          <Route path="/auction" element={<AuctionRoom />} />
          <Route path="/squad" element={<MySquad />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/pool" element={<PlayerPool />} />
          <Route path="/results" element={<Results />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {showTabs && <TabBar />}
    </div>
  )
}
