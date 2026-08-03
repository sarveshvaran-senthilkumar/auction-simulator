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
import { Field } from './Login'

export default function Register() {
  const navigate = useNavigate()
  const signIn = useAuth((s) => s.signIn)
  const showToast = useAuction((s) => s.showToast)

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  const passwordTooShort = password.length > 0 && password.length < 8
  // Mirrors USERNAME_RE on the server, so the rule is visible before you submit.
  const usernameBad = username.length > 0 && !/^[a-zA-Z0-9_.]{2,20}$/.test(username)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!username.trim() || !email.trim() || !password) return showToast('Fill in every field')
    if (password.length < 8) return showToast('Password must be at least 8 characters')

    setBusy(true)
    try {
      const data = await api.register({
        username: username.trim(),
        email: email.trim(),
        password,
      })
      signIn(data.token, data.user)
      haptic([20, 40, 20])
      navigate('/', { replace: true })
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Could not create your account')
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
          <div className="text-[44px] leading-none mb-3">🏏</div>
          <h1 className="text-[28px] leading-tight font-black tracking-tight">Create account</h1>
          <p className="text-slate-400 mt-2 text-[15px]">
            Your name shows up in the lobby and the bid feed.
          </p>
        </motion.div>

        <GoogleButton onDone={() => navigate('/', { replace: true })} />

        <motion.form
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06 }}
          onSubmit={submit}
          className="space-y-4"
        >
          <Field label="Username">
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="sarvesh"
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              maxLength={20}
              className={`w-full h-14 rounded-2xl bg-ink-700 border px-4 outline-none ${
                usernameBad ? 'border-rose-500/60' : 'border-line/10 focus:border-indigo-400/60'
              }`}
            />
            <span
              className={`text-[11px] ml-1 mt-1 block ${
                usernameBad ? 'text-rose-400' : 'text-slate-500'
              }`}
            >
              2–20 characters · letters, numbers, underscore or dot
            </span>
          </Field>

          <Field label="Email">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
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
              placeholder="At least 8 characters"
              autoComplete="new-password"
              className={`w-full h-14 rounded-2xl bg-ink-700 border px-4 outline-none ${
                passwordTooShort
                  ? 'border-rose-500/60'
                  : 'border-line/10 focus:border-indigo-400/60'
              }`}
            />
            {passwordTooShort && (
              <span className="text-[11px] text-rose-400 ml-1 mt-1 block">
                {8 - password.length} more character{8 - password.length === 1 ? '' : 's'}
              </span>
            )}
          </Field>

          <Button type="submit" variant="gold" className="w-full h-14" disabled={busy}>
            {busy ? 'Creating…' : 'Create Account'}
          </Button>
        </motion.form>

        <div className="mt-auto pt-10 text-center text-sm text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 font-semibold">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
