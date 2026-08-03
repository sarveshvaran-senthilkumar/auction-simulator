import { motion } from 'framer-motion'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GoogleButton } from '../components/GoogleButton'
import { ThemeToggle } from '../components/ThemeToggle'
import { Button } from '../components/ui'
import { api } from '../lib/api'
import { haptic } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import { useAuth } from '../store/authStore'

export default function Login() {
  const navigate = useNavigate()
  const signIn = useAuth((s) => s.signIn)
  const showToast = useAuction((s) => s.showToast)

  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!identifier.trim() || !password) return showToast('Enter your details')
    setBusy(true)
    try {
      const data = await api.login({ identifier: identifier.trim(), password })
      signIn(data.token, data.user)
      haptic(20)
      navigate('/', { replace: true })
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Could not sign in')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-scroll">
      <div
        className="min-h-full flex flex-col px-6 pb-10"
        style={{ paddingTop: 'calc(var(--safe-top) + 20px)' }}
      >
        <div className="flex justify-end">
          <ThemeToggle />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8 mt-4"
        >
          <div className="text-[52px] leading-none mb-3">🏏</div>
          <h1 className="text-[30px] leading-tight font-black tracking-tight">
            <span className="bg-gradient-to-r from-gold-400 via-amber-300 to-gold-400 bg-clip-text text-transparent">
              Mega Auction
            </span>
          </h1>
          <p className="text-slate-400 mt-2 text-[15px]">Sign in to take a franchise.</p>
        </motion.div>

        <GoogleButton onDone={() => navigate('/', { replace: true })} />

        <motion.form
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06 }}
          onSubmit={submit}
          className="space-y-4"
        >
          <Field label="Username or email">
            <input
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="sarvesh"
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              className="w-full h-14 rounded-2xl bg-ink-700 border border-line/10 px-4 outline-none focus:border-indigo-400/60"
            />
          </Field>

          <Field label="Password">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              className="w-full h-14 rounded-2xl bg-ink-700 border border-line/10 px-4 outline-none focus:border-indigo-400/60"
            />
          </Field>

          <Button type="submit" variant="gold" className="w-full h-14" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign In'}
          </Button>
        </motion.form>

        <div className="mt-auto pt-10 text-center text-sm text-slate-500">
          New here?{' '}
          <Link to="/register" className="text-indigo-400 font-semibold">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  )
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">
        {label}
      </span>
      <div className="mt-1.5">{children}</div>
    </label>
  )
}
