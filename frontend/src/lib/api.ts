// Thin fetch wrapper for the Django API. Requests go to the same origin (Vite
// proxies /api and /_allauth), so the session cookie is sent automatically;
// unsafe methods need Django's CSRF token echoed back in a header.

export type Game = {
  slug: string
  title: string
  steam_app_id: number | null
  cover_url: string
  on_switch1: boolean
  on_switch2: boolean
  achievement_count: number
  unlocked_count: number | null
  in_library: boolean | null
}

export type Achievement = {
  id: number
  api_name: string
  name: string
  description: string
  hidden: boolean
  icon_url: string
  icon_gray_url: string
  unlocked_at: string | null
  note: string
}

export type GameDetail = Game & { achievements: Achievement[] }

export type Unlock = { achievement_id: number; unlocked_at: string; note: string }

export type Stats = {
  games: number
  completed_games: number
  unlocked: number
  total: number
  percent: number
  per_game: {
    slug: string
    title: string
    cover_url: string
    unlocked: number
    total: number
    percent: number
  }[]
  recent_unlocks: {
    achievement_id: number
    name: string
    icon_url: string
    game_slug: string
    game_title: string
    unlocked_at: string
    note: string
  }[]
}

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown, message: string) {
    super(message)
    this.status = status
    this.body = body
  }
}

function csrfToken() {
  return document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)?.[1] ?? ''
}

// Pulls a readable message out of DRF ({"field": ["msg"]} / {"detail": "msg"})
// and allauth ({"errors": [{"message": "msg"}]}) error bodies.
function errorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object') {
    const b = body as Record<string, unknown>
    if (Array.isArray(b.errors) && b.errors.length) {
      return b.errors.map((e: { message?: string }) => e.message).join(' ')
    }
    if (typeof b.detail === 'string') return b.detail
    const first = Object.values(b).flat()[0]
    if (typeof first === 'string') return first
  }
  return fallback
}

export async function request<T>(method: string, url: string, data?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (data !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') headers['X-CSRFToken'] = csrfToken()

  const resp = await fetch(url, {
    method,
    headers,
    credentials: 'same-origin',
    body: data === undefined ? undefined : JSON.stringify(data),
  })
  const body = resp.status === 204 ? null : await resp.json().catch(() => null)
  if (!resp.ok) {
    throw new ApiError(resp.status, body, errorMessage(body, `Request failed (${resp.status})`))
  }
  return body as T
}

export const api = {
  games: (params: { q?: string; library?: boolean } = {}) => {
    const qs = new URLSearchParams()
    if (params.q) qs.set('q', params.q)
    if (params.library) qs.set('library', '1')
    return request<Game[]>('GET', `/api/games/?${qs}`)
  },
  game: (slug: string) => request<GameDetail>('GET', `/api/games/${slug}/`),
  addToLibrary: (slug: string) => request<unknown>('PUT', `/api/me/games/${slug}/`),
  removeFromLibrary: (slug: string) => request<null>('DELETE', `/api/me/games/${slug}/`),
  unlock: (id: number, data: { unlocked_at?: string; note?: string } = {}) =>
    request<Unlock>('PUT', `/api/me/achievements/${id}/`, data),
  lock: (id: number) => request<null>('DELETE', `/api/me/achievements/${id}/`),
  stats: () => request<Stats>('GET', '/api/me/stats/'),
}
