import { useEffect } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { TabBar } from './components/TabBar'
import { Toast } from './components/ui'
import { RoomGate } from './RoomGate'
import AuctionRoom from './pages/AuctionRoom'
import Home from './pages/Home'
import Lobby from './pages/Lobby'
import Login from './pages/Login'
import MySquad from './pages/MySquad'
import PlayerPool from './pages/PlayerPool'
import Register from './pages/Register'
import Results from './pages/Results'
import RetentionPhase from './pages/RetentionPhase'
import Teams from './pages/Teams'
import { useAuction } from './store/auctionStore'
import { applyTheme, useAuth } from './store/authStore'

/** Routes that show the bottom tab bar. Setup and auth flows are full-screen. */
const TAB_ROUTES = ['/auction', '/squad', '/teams', '/pool']

/** Everything past the login wall. */
function RequireAuth() {
  const token = useAuth((s) => s.token)
  const location = useLocation()
  if (!token) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

export default function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const room = useAuction((s) => s.room)
  const theme = useAuth((s) => s.theme)
  const showTabs = TAB_ROUTES.some((r) => location.pathname.startsWith(r))

  // Paint the stored theme on first mount; the store repaints on every change.
  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  // The room's phase is the source of truth for which screen you belong on, so a
  // reconnect or a phase change moves everyone without any manual navigation.
  useEffect(() => {
    if (!room) return
    const path = location.pathname
    if (path === '/login' || path === '/register') return
    if (room.status === 'RETENTION' && !path.startsWith('/retention')) {
      navigate('/retention', { replace: true })
    } else if (
      room.status === 'IN_PROGRESS' &&
      (path === '/' || path.startsWith('/lobby') || path.startsWith('/retention'))
    ) {
      navigate('/auction', { replace: true })
    } else if (room.status === 'COMPLETED' && !path.startsWith('/results')) {
      navigate('/results', { replace: true })
    }
  }, [room?.status, location.pathname, navigate, room])

  return (
    <div className="app-shell">
      <Toast />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<RequireAuth />}>
          <Route path="/" element={<Home />} />
          {/* The lobby sits outside RoomGate: someone joining by code has no
              team yet, and there is no socket until they claim a franchise. */}
          <Route path="/lobby" element={<Lobby />} />
          <Route element={<RoomGate />}>
            <Route path="/retention" element={<RetentionPhase />} />
            <Route path="/auction" element={<AuctionRoom />} />
            <Route path="/squad" element={<MySquad />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/pool" element={<PlayerPool />} />
            <Route path="/results" element={<Results />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {showTabs && <TabBar />}
    </div>
  )
}
