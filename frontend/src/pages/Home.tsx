import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui'
import { api } from '../lib/api'
import { haptic } from '../lib/format'
import { useAuction } from '../store/auctionStore'

type Mode = 'menu' | 'create' | 'join'

export default function Home() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<Mode>('menu')
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [format, setFormat] = useState('QUICK')
  const [busy, setBusy] = useState(false)
  const [online, setOnline] = useState<boolean | null>(null)

  const setSession = useAuction((s) => s.setSession)
  const showToast = useAuction((s) => s.showToast)
  const reset = useAuction((s) => s.reset)
  const savedName = useAuction((s) => s.displayName)
  const savedRoom = useAuction((s) => s.roomCode)

  useEffect(() => {
    if (savedName) setName(savedName)
    api.health().then(() => setOnline(true)).catch(() => setOnline(false))
  }, [savedName])

  async function createRoom() {
    if (!name.trim()) return showToast('Enter your name')
    setBusy(true)
    try {
      const room = await api.createRoom({
        host_display_name: name.trim(),
        config: { format },
      })
      setSession({
        userId: room.host_user_id,
        displayName: name.trim(),
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
    if (!name.trim()) return showToast('Enter your name')
    if (code.trim().length !== 6) return showToast('Room codes are 6 characters')
    setBusy(true)
    try {
      await api.getRoom(code.trim().toUpperCase())
      setSession({
        userId: null,
        displayName: name.trim(),
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

  return (
    <div className="app-scroll">
      <div
        className="min-h-full flex flex-col px-6 pb-10"
        style={{ paddingTop: 'calc(var(--safe-top) + 48px)' }}
      >
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="text-[52px] leading-none mb-3">🏏</div>
          <h1 className="text-[32px] leading-tight font-black tracking-tight">
            <span className="bg-gradient-to-r from-gold-400 via-amber-200 to-gold-400 bg-clip-text text-transparent">
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
                className="tap w-full h-12 rounded-2xl border border-white/10 text-sm text-slate-400"
              >
                Resume room <span className="font-mono font-bold text-slate-200">{savedRoom}</span>
              </button>
            )}
          </motion.div>
        )}

        {mode !== 'menu' && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <Field label="Your name">
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Team owner"
                autoComplete="nickname"
                maxLength={20}
                className="w-full h-14 rounded-2xl bg-ink-700 border border-white/10 px-4 outline-none focus:border-indigo-400/60"
              />
            </Field>

            {mode === 'join' && (
              <Field label="Room code">
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase().slice(0, 6))}
                  placeholder="ABC123"
                  autoCapitalize="characters"
                  autoCorrect="off"
                  inputMode="text"
                  className="w-full h-14 rounded-2xl bg-ink-700 border border-white/10 px-4 outline-none focus:border-indigo-400/60 font-mono text-2xl tracking-[0.3em] text-center"
                />
              </Field>
            )}

            {mode === 'create' && (
              <Field label="Auction length">
                <div className="grid grid-cols-3 gap-2">
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
                          ? 'bg-indigo-500/15 border-indigo-400/50 text-indigo-200'
                          : 'bg-ink-700 border-white/5 text-slate-400'
                      }`}
                    >
                      <div className="text-sm font-bold">{opt.label}</div>
                      <div className="text-[10px] opacity-70 mt-0.5">{opt.hint}</div>
                    </button>
                  ))}
                </div>
              </Field>
            )}

            <Button
              variant="gold"
              className="w-full h-14"
              disabled={busy}
              onClick={mode === 'create' ? createRoom : joinRoom}
            >
              {busy ? 'Working…' : mode === 'create' ? 'Create Room' : 'Join Room'}
            </Button>

            <button
              onClick={() => {
                setMode('menu')
                reset()
              }}
              className="tap w-full h-11 text-sm text-slate-500"
            >
              Back
            </button>
          </motion.div>
        )}

        <div className="mt-auto pt-10 flex items-center justify-center gap-2 text-xs text-slate-500">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              online === null ? 'bg-slate-600' : online ? 'bg-emerald-500' : 'bg-rose-500'
            }`}
          />
          {online === null ? 'Checking server…' : online ? 'Server online' : 'Server unreachable'}
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">
        {label}
      </span>
      <div className="mt-1.5">{children}</div>
    </label>
  )
}
