import { useCallback, useEffect, useRef } from 'react'
import { wsUrl } from '../lib/api'
import { haptic } from '../lib/format'
import { useAuction } from '../store/auctionStore'

/** Owns the WebSocket lifecycle for a room and feeds every event into the store.
 *
 *  Phones suspend sockets whenever the app is backgrounded, so this reconnects
 *  with backoff and also re-dials immediately when the tab becomes visible.
 */
export function useAuctionSocket(roomCode: string | null, userId: string | null) {
  const socketRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const timerRef = useRef<number | null>(null)
  const closedByUs = useRef(false)

  const applyEvent = useAuction((s) => s.applyEvent)
  const setConnected = useAuction((s) => s.setConnected)

  const connect = useCallback(() => {
    if (!roomCode || !userId) return
    if (socketRef.current && socketRef.current.readyState <= WebSocket.OPEN) return

    const socket = new WebSocket(wsUrl(roomCode, userId))
    socketRef.current = socket

    socket.onopen = () => {
      retryRef.current = 0
      setConnected(true)
    }

    socket.onmessage = (event) => {
      try {
        const { type, payload } = JSON.parse(event.data)
        if (type === 'LOT_SOLD') haptic(18)
        if (type === 'RTM_PROMPT' || type === 'RTM_COUNTER_PROMPT') haptic([20, 60, 20])
        applyEvent(type, payload)
      } catch {
        /* ignore malformed frames */
      }
    }

    socket.onclose = () => {
      setConnected(false)
      socketRef.current = null
      if (closedByUs.current) return
      // Exponential backoff, capped so a long background stint still recovers.
      const wait = Math.min(8000, 500 * 2 ** retryRef.current++)
      timerRef.current = window.setTimeout(connect, wait)
    }

    socket.onerror = () => socket.close()
  }, [roomCode, userId, applyEvent, setConnected])

  useEffect(() => {
    closedByUs.current = false
    connect()

    const onVisible = () => {
      if (document.visibilityState === 'visible') {
        retryRef.current = 0
        connect()
      }
    }
    document.addEventListener('visibilitychange', onVisible)

    return () => {
      closedByUs.current = true
      document.removeEventListener('visibilitychange', onVisible)
      if (timerRef.current) window.clearTimeout(timerRef.current)
      socketRef.current?.close()
      socketRef.current = null
    }
  }, [connect])

  const send = useCallback((type: string, payload: Record<string, unknown> = {}) => {
    const socket = socketRef.current
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type, payload }))
      return true
    }
    return false
  }, [])

  return {
    send,
    placeBid: (amountLakh: number) => send('PLACE_BID', { amount_lakh: amountLakh }),
    confirmRetention: (playerIds: string[]) => send('RETENTION_CONFIRM', { player_ids: playerIds }),
    decide: (choice: boolean) => send('DECISION', { choice }),
  }
}
