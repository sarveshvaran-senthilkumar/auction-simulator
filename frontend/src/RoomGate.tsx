import { Navigate, Outlet } from 'react-router-dom'
import { RTMSheet } from './components/RTMSheet'
import { useAuction } from './store/auctionStore'
import { useAuctionSocket } from './ws/useAuctionSocket'

/** Holds the single WebSocket for every in-room screen.
 *
 *  Mounting the socket here rather than per-page means switching tabs mid-lot
 *  never drops the connection and re-runs the reconnect backoff.
 */
export function RoomGate() {
  const roomCode = useAuction((s) => s.roomCode)
  const userId = useAuction((s) => s.userId)

  const socket = useAuctionSocket(roomCode, userId)

  if (!roomCode || !userId) return <Navigate to="/" replace />

  return (
    <>
      <Outlet context={socket} />
      <RTMSheet decide={socket.decide} />
    </>
  )
}

export type SocketContext = ReturnType<typeof useAuctionSocket>
