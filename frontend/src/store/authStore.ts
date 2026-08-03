import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Account {
  id: string
  display_name: string
  username: string | null
  email: string | null
  avatar_url: string | null
  is_guest: boolean
}

export type Theme = 'dark' | 'light'

interface AuthState {
  token: string | null
  user: Account | null
  theme: Theme
  signIn: (token: string, user: Account) => void
  signOut: () => void
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

/** Paint the theme onto <html> so the CSS variables in index.css switch. */
export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
  // Keep the phone's status bar / browser chrome in step with the page.
  const meta = document.querySelector('meta[name="theme-color"]')
  meta?.setAttribute('content', theme === 'dark' ? '#0B1120' : '#ECF0F6')
}

function preferredTheme(): Theme {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      theme: preferredTheme(),

      signIn: (token, user) => set({ token, user }),
      signOut: () => set({ token: null, user: null }),

      setTheme: (theme) => {
        applyTheme(theme)
        set({ theme })
      },
      toggleTheme: () => get().setTheme(get().theme === 'dark' ? 'light' : 'dark'),
    }),
    {
      name: 'ipl-auction-auth',
      onRehydrateStorage: () => (state) => {
        // Repaint after the persisted choice loads, so there's no flash of the
        // wrong theme on a reload.
        applyTheme(state?.theme ?? 'dark')
      },
    },
  ),
)
