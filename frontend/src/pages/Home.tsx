import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ThemeToggle } from '../components/ThemeToggle'
import { Button } from '../components/ui'
import { api } from '../lib/api'
import { haptic, initials } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import { useAuth } from '../store/authStore'

type Mode = 'menu' | 'create' | 'join'

/** Time-of-day greeting, the way a game would say it rather than an app. */
function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 5) return 'Burning the midnight oil'
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function Home() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<Mode>('menu')
  const [code, setCode] = useState('')
  const [format, setFormat] = useState('QUICK')
  const [busy, setBusy] = useState(false)
  const [online, setOnline] = useState<boolean | null>(null)

  const user = useAuth((s) => s.user)
  const signOut = useAuth((s) => s.signOut)
  const setSession = useAuction((s) => s.setSession)
  const showToast = useAuction((s) => s.showToast)
  const reset = useAuction((s) => s.reset)
  const savedRoom = useAuction((s) => s.roomCode)

  useEffect(() => {
    api.health().then(() => setOnline(true)).catch(() => setOnline(false))
  }, [])

  async function createRoom() {
    setBusy(true)
    try {
      const room = await api.createRoom({
        host_display_name: user?.display_name ?? 'Manager',
        config: { format },
      })
      setSession({
        userId: room.host_user_id,
        displayName: user?.display_name ?? '',
        roomCode: room.room_code,
        teamId: null,
        franchiseCode: null,
      })
      haptic(20)
      navigate('/lobby')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Could not create room')
    } finally {
      setBusy(false)
    }
  }

  async function joinRoom() {
    if (code.trim().length !== 6) return showToast('Room codes are 6 characters')
    setBusy(true)
    try {
      await api.getRoom(code.trim().toUpperCase())
      setSession({
        userId: user?.id ?? null,
        displayName: user?.display_name ?? '',
        roomCode: code.trim().toUpperCase(),
        teamId: null,
        franchiseCode: null,
      })
      haptic(20)
      navigate('/lobby')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Room not found')
    } finally {
      setBusy(false)
    }
  }

  const name = user?.display_name || user?.username || 'Manager'

  return (
    <div className="app-scroll">
      <div
        className="min-h-full flex flex-col px-6 pb-10"
        style={{ paddingTop: 'calc(var(--safe-top) + 16px)' }}
      >
        {/* Player chip + theme switch */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2.5 min-w-0">
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt=""
                referrerPolicy="no-referrer"
                className="w-10 h-10 rounded-full object-cover shrink-0"
              />
            ) : (
              <div className="w-10 h-10 rounded-full bg-indigo-500/20 text-indigo-300 grid place-items-center font-bold text-sm shrink-0">
                {initials(name)}
              </div>
            )}
            <div className="min-w-0">
              <div className="text-[11px] text-slate-500 leading-none">{greeting()},</div>
              <div className="font-bold truncate leading-tight mt-0.5">{name}</div>
            </div>
          </div>
          <ThemeToggle />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-9"
        >
          <div className="text-[52px] leading-none mb-3">🏏</div>
          <h1 className="text-[32px] leading-tight font-black tracking-tight">
            <span className="bg-gradient-to-r from-gold-400 via-amber-300 to-gold-400 bg-clip-text text-transparent">
              Mega Auction
            </span>
          </h1>
          <p className="text-slate-400 mt-2 text-[15px]">
            Ten franchises. One purse. Outbid the AI.
          </p>
        </motion.div>

        {mode === 'menu' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 }}
            className="space-y-3"
          >
            <Button variant="gold" className="w-full h-14" onClick={() => setMode('create')}>
              Create Auction
            </Button>
            <Button variant="ghost" className="w-full h-14" onClick={() => setMode('join')}>
              Join with Code
            </Button>

            {savedRoom && (
              <button
                onClick={() => navigate('/lobby')}
                className="tap w-full h-12 rounded-2xl border border-line/10 text-sm text-slate-400"
              >
                Resume room <span className="font-mono font-bold text-slate-200">{savedRoom}</span>
              </button>
            )}
          </motion.div>
        )}

        {mode !== 'menu' && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {mode === 'join' && (
              <label className="block">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">
                  Room code
                </span>
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase().slice(0, 6))}
                  placeholder="ABC123"
                  autoCapitalize="characters"
                  autoCorrect="off"
                  className="mt-1.5 w-full h-14 rounded-2xl bg-ink-700 border border-line/10 px-4 outline-none focus:border-indigo-400/60 font-mono text-2xl tracking-[0.3em] text-center"
                />
              </label>
            )}

            {mode === 'create' && (
              <label className="block">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">
                  Auction length
                </span>
                <div className="mt-1.5 grid grid-cols-3 gap-2">
                  {[
                    { id: 'QUICK', label: 'Quick', hint: '~80 lots' },
                    { id: 'STANDARD', label: 'Standard', hint: '~150 lots' },
                    { id: 'FULL', label: 'Full', hint: 'everyone' },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => {
                        setFormat(opt.id)
                        haptic(8)
                      }}
                      className={`tap rounded-2xl py-3 border text-center ${
                        format === opt.id
                          ? 'bg-indigo-500/15 border-indigo-400/50 text-indigo-300'
                          : 'bg-ink-700 border-line/5 text-slate-400'
                      }`}
                    >
                      <div className="text-sm font-bold">{opt.label}</div>
                      <div className="text-[10px] opacity-70 mt-0.5">{opt.hint}</div>
                    </button>
                  ))}
                </div>
              </label>
            )}

            <Button
              variant="gold"
              className="w-full h-14"
              disabled={busy}
              onClick={mode === 'create' ? createRoom : joinRoom}
            >
              {busy ? 'Working…' : mode === 'create' ? 'Create Room' : 'Join Room'}
            </Button>

            <button onClick={() => setMode('menu')} className="tap w-full h-11 text-sm text-slate-500">
              Back
            </button>
          </motion.div>
        )}

        <div className="mt-auto pt-10 space-y-3">
          <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                online === null ? 'bg-slate-600' : online ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
            {online === null ? 'Checking server…' : online ? 'Server online' : 'Server unreachable'}
          </div>
          <button
            onClick={() => {
              reset()
              signOut()
              navigate('/login', { replace: true })
            }}
            className="tap w-full text-xs text-slate-600"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}
