import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { useAuction } from '../store/auctionStore'
import { useAuth } from '../store/authStore'

declare global {
  interface Window {
    google?: any
  }
}

const GSI_SRC = 'https://accounts.google.com/gsi/client'

/** "Continue with Google" using Google Identity Services.
 *
 *  Renders nothing at all when the server has no GOOGLE_CLIENT_ID configured,
 *  so a fresh clone shows a working username/password form rather than a button
 *  that can only fail.
 */
export function GoogleButton({ onDone }: { onDone: () => void }) {
  const holder = useRef<HTMLDivElement>(null)
  const [clientId, setClientId] = useState<string | null>(null)
  const [ready, setReady] = useState(false)
  const signIn = useAuth((s) => s.signIn)
  const showToast = useAuction((s) => s.showToast)

  useEffect(() => {
    api
      .authConfig()
      .then((cfg) => setClientId(cfg.google_enabled ? cfg.google_client_id : null))
      .catch(() => setClientId(null))
  }, [])

  useEffect(() => {
    if (!clientId) return

    function init() {
      if (!window.google?.accounts?.id || !holder.current) return
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: { credential: string }) => {
          try {
            const data = await api.googleLogin(response.credential)
            signIn(data.token, data.user)
            onDone()
          } catch (err) {
            showToast(err instanceof Error ? err.message : 'Google sign-in failed')
          }
        },
      })
      window.google.accounts.id.renderButton(holder.current, {
        theme: 'filled_black',
        size: 'large',
        shape: 'pill',
        text: 'continue_with',
        width: holder.current.offsetWidth || 300,
      })
      setReady(true)
    }

    if (window.google?.accounts?.id) return init()

    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GSI_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', init)
      return () => existing.removeEventListener('load', init)
    }

    const script = document.createElement('script')
    script.src = GSI_SRC
    script.async = true
    script.defer = true
    script.onload = init
    document.head.appendChild(script)
  }, [clientId, signIn, onDone, showToast])

  if (!clientId) return null

  return (
    <div className="w-full">
      <div ref={holder} className="w-full flex justify-center min-h-[44px]" />
      {!ready && (
        <div className="text-center text-xs text-slate-500 py-3">Loading Google sign-in…</div>
      )}
      <div className="flex items-center gap-3 my-5">
        <div className="flex-1 h-px bg-line/10" />
        <span className="text-[11px] uppercase tracking-wider text-slate-500">or</span>
        <div className="flex-1 h-px bg-line/10" />
      </div>
    </div>
  )
}
