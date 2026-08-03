/** Vite proxies /api and /ws to the backend in dev, so relative URLs work from
 *  a phone on the LAN without knowing the host's IP. Override with VITE_API_URL
 *  when the backend lives somewhere else. */
const BASE = import.meta.env.VITE_API_URL ?? ''

/** Read the token straight from persisted storage rather than importing the
 *  auth store, which would make this module and the store circular. */
function authHeader(): Record<string, string> {
  try {
    const raw = localStorage.getItem('ipl-auction-auth')
    const token = raw ? JSON.parse(raw)?.state?.token : null
    return token ? { Authorization: `Bearer ${token}` } : {}
  } catch {
    return {}
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(),
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    throw new Error(await errorMessage(res))
  }
  return res.json() as Promise<T>
}

/** Turn an error response into something worth showing a person.
 *
 *  FastAPI returns plain strings for HTTPException but an *array* of
 *  {loc, msg} objects for 422 validation failures, which is why an unreadable
 *  "Request failed (422)" used to leak through on a bad username.
 */
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    const detail = body?.detail

    if (typeof detail === 'string') return detail

    if (Array.isArray(detail) && detail.length) {
      const first = detail[0]
      // Pydantic prefixes custom validator messages with "Value error, ".
      const msg = String(first?.msg ?? '').replace(/^Value error,\s*/i, '')
      // loc is like ["body", "username"] — name the field so it's actionable.
      const field = Array.isArray(first?.loc)
        ? first.loc.filter((p: unknown) => p !== 'body').pop()
        : null
      if (msg && field) return `${String(field).replace(/_/g, ' ')}: ${msg}`
      if (msg) return msg
    }
  } catch {
    /* non-JSON error body */
  }
  return `Request failed (${res.status})`
}

export const api = {
  health: () => request<{ status: string; version: string }>('/health'),

  authConfig: () =>
    request<{ google_enabled: boolean; google_client_id: string }>('/api/auth/config'),

  register: (body: {
    username: string
    email: string
    password: string
    display_name?: string
  }) => request<any>('/api/auth/register', { method: 'POST', body: JSON.stringify(body) }),

  login: (body: { identifier: string; password: string }) =>
    request<any>('/api/auth/login', { method: 'POST', body: JSON.stringify(body) }),

  googleLogin: (idToken: string) =>
    request<any>('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken }),
    }),

  me: () => request<any>('/api/auth/me'),

  franchises: () => request<any[]>('/api/franchises'),

  createRoom: (body: { host_display_name: string; franchise_code?: string; config?: any }) =>
    request<any>('/api/rooms', { method: 'POST', body: JSON.stringify(body) }),

  getRoom: (code: string) => request<any>(`/api/rooms/${code}`),

  joinRoom: (
    code: string,
    body: { franchise_code: string; display_name?: string; user_id?: string | null },
  ) => request<any>(`/api/rooms/${code}/join`, { method: 'POST', body: JSON.stringify(body) }),

  startRetention: (code: string) => request<any>(`/api/rooms/${code}/start`, { method: 'POST' }),

  roomState: (code: string) => request<any>(`/api/rooms/${code}/state`),

  retentionPool: (code: string, teamId: string) =>
    request<any>(`/api/rooms/${code}/retention-pool/${teamId}`),

  results: (code: string) => request<any>(`/api/rooms/${code}/results`),

  unsold: (code: string) =>
    request<{ total: number; returning: number; players: any[] }>(
      `/api/rooms/${code}/unsold`,
    ),

  players: (params: Record<string, string | number | boolean | undefined>) => {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') qs.set(k, String(v))
    })
    return request<{ total: number; items: any[] }>(`/api/players?${qs}`)
  },

  player: (id: string) => request<any>(`/api/players/${id}`),
}

export function wsUrl(code: string, userId: string): string {
  const explicit = import.meta.env.VITE_WS_URL
  if (explicit) return `${explicit}/ws/auction/${code}?user_id=${userId}`
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${location.host}/ws/auction/${code}?user_id=${userId}`
}
