/** Vite proxies /api and /ws to the backend in dev, so relative URLs work from
 *  a phone on the LAN without knowing the host's IP. Override with VITE_API_URL
 *  when the backend lives somewhere else. */
const BASE = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; version: string }>('/health'),

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
