import { motion } from 'framer-motion'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, franchiseColor, Spinner } from '../components/ui'
import { api } from '../lib/api'
import { haptic } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import type { Franchise } from '../types'

export default function Lobby() {
  const navigate = useNavigate()
  const [teams, setTeams] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState(false)

  const { roomCode, userId, displayName, franchiseCode } = useAuction()
  const setSession = useAuction((s) => s.setSession)
  const showToast = useAuction((s) => s.showToast)
  const franchises = useAuction((s) => s.franchises)
  const setFranchises = useAuction((s) => s.setFranchises)

  const refresh = useCallback(async () => {
    if (!roomCode) return
    try {
      const room = await api.getRoom(roomCode)
      setTeams(room.teams)
      if (room.status !== 'LOBBY') navigate('/retention', { replace: true })
      const mine = room.teams.find((t: any) => t.user_id && t.user_id === userId)
      if (mine) setSession({ teamId: mine.id, franchiseCode: mine.franchise_code })
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Could not load room')
    } finally {
      setLoading(false)
    }
  }, [roomCode, userId, navigate, setSession, showToast])

  useEffect(() => {
    if (!franchises.length) api.franchises().then(setFranchises).catch(() => {})
  }, [franchises.length, setFranchises])

  useEffect(() => {
    if (!roomCode) {
      navigate('/', { replace: true })
      return
    }
    refresh()
    // Lobby is pre-socket, so poll for other people claiming franchises.
    const id = window.setInterval(refresh, 3000)
    return () => window.clearInterval(id)
  }, [refresh, roomCode, navigate])

  async function claim(code: string) {
    if (busy || !roomCode) return
    setBusy(true)
    haptic(12)
    try {
      const room = await api.joinRoom(roomCode, {
        franchise_code: code,
        display_name: displayName,
        user_id: userId,
      })
      const uid = room.joined_user_id ?? userId
      const mine = room.teams.find((t: any) => t.franchise_code === code)
      setSession({ userId: uid, teamId: mine?.id ?? null, franchiseCode: code })
      setTeams(room.teams)
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Could not claim that team')
      refresh()
    } finally {
      setBusy(false)
    }
  }

  async function start() {
    if (!roomCode) return
    if (!franchiseCode) return showToast('Pick a franchise first')
    setBusy(true)
    try {
      await api.startRetention(roomCode)
      haptic([20, 40, 20])
      navigate('/retention')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Could not start')
      setBusy(false)
    }
  }

  const meta = (code: string): Franchise | undefined => franchises.find((f) => f.code === code)

  return (
    <>
      <header className="app-header px-5 pb-3">
        <div className="flex items-center justify-between pt-3">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
              Room code
            </div>
            <button
              onClick={() => {
                navigator.clipboard?.writeText(roomCode ?? '')
                setCopied(true)
                haptic(10)
                window.setTimeout(() => setCopied(false), 1500)
              }}
              className="tap font-mono text-2xl font-black tracking-[0.2em] text-gold-400 active:opacity-70"
            >
              {roomCode}
            </button>
          </div>
          <div className="text-right text-xs text-slate-500">
            {copied ? (
              <span className="text-emerald-400 font-semibold">Copied!</span>
            ) : (
              <span>tap to copy</span>
            )}
            <div className="mt-1 text-slate-400">
              {teams.filter((t) => !t.is_ai).length} human · {teams.filter((t) => t.is_ai).length} AI
            </div>
          </div>
        </div>
      </header>

      <div className="app-scroll px-5 pt-4 pb-40">
        <h2 className="text-lg font-bold mb-1">Choose your franchise</h2>
        <p className="text-sm text-slate-500 mb-4">
          Everything you don't claim is run by the AI.
        </p>

        {loading ? (
          <Spinner label="Loading franchises…" />
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {teams.map((team, i) => {
              const info = meta(team.franchise_code)
              const isMine = team.user_id && team.user_id === userId
              const taken = !team.is_ai && !isMine
              const accent = franchiseColor(team.franchise_code)

              return (
                <motion.button
                  key={team.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  disabled={taken || busy}
                  onClick={() => claim(team.franchise_code)}
                  className={`tap relative rounded-2xl p-3 text-left border overflow-hidden ${
                    isMine
                      ? 'border-transparent ring-2'
                      : taken
                        ? 'bg-ink-800 border-line/5 opacity-45'
                        : 'bg-ink-700 border-line/5'
                  }`}
                  style={
                    isMine
                      ? ({ background: `${accent}22`, '--tw-ring-color': accent } as any)
                      : undefined
                  }
                >
                  <div
                    className="w-9 h-9 rounded-xl grid place-items-center font-black text-[13px] mb-2"
                    style={{ background: accent, color: '#0B1120' }}
                  >
                    {team.franchise_code}
                  </div>
                  <div className="text-[13px] font-bold leading-tight">
                    {info?.name ?? team.franchise_code}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{info?.city ?? ''}</div>

                  <div className="mt-2 text-[10px] font-bold uppercase tracking-wide">
                    {isMine ? (
                      <span className="text-emerald-400">● You</span>
                    ) : taken ? (
                      <span className="text-slate-500">Taken</span>
                    ) : (
                      <span className="text-slate-600">AI</span>
                    )}
                  </div>
                </motion.button>
              )
            })}
          </div>
        )}
      </div>

      <div
        className="shrink-0 px-5 pt-3 bg-ink-800/95 backdrop-blur border-t border-line/5 above-tabbar"
      >
        <Button
          variant="gold"
          className="w-full h-14"
          disabled={!franchiseCode || busy}
          onClick={start}
        >
          {franchiseCode ? `Start as ${franchiseCode}` : 'Pick a franchise'}
        </Button>
      </div>
    </>
  )
}
