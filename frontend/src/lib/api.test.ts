import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, request } from './api'
import { formatDate, today } from './dates'

function mockFetch(status: number, body: unknown) {
  const fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  })
  vi.stubGlobal('fetch', fetch)
  return fetch
}

describe('request', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('sends the CSRF cookie as a header on unsafe methods', async () => {
    vi.stubGlobal('document', { cookie: 'sessionid=abc; csrftoken=tok123' })
    const fetch = mockFetch(200, { ok: true })

    await request('PUT', '/api/x/', { note: 'hi' })

    const [, init] = fetch.mock.calls[0]
    expect(init.headers['X-CSRFToken']).toBe('tok123')
    expect(init.body).toBe('{"note":"hi"}')
  })

  it.each([
    [{ errors: [{ message: 'Invalid or expired key.' }] }, 'Invalid or expired key.'],
    [{ detail: 'Not found.' }, 'Not found.'],
    [{ unlocked_at: ['Unlock date cannot be in the future.'] }, 'Unlock date cannot be in the future.'],
    [null, 'Request failed (400)'],
  ])('turns error body %j into a message', async (body, message) => {
    mockFetch(400, body)
    const error = await request<never>('GET', '/api/x/').catch((e: unknown) => e as ApiError)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.message).toBe(message)
  })

  it('encodes slugs so they cannot change the API path', async () => {
    vi.stubGlobal('document', { cookie: '' })
    const fetch = mockFetch(200, {})

    await api.game('../me/stats')
    await api.addToLibrary('x/../../achievements/5')

    expect(fetch.mock.calls.map(([url]) => new URL(url, 'http://test').pathname)).toEqual([
      '/api/games/..%2Fme%2Fstats/',
      '/api/me/games/x%2F..%2F..%2Fachievements%2F5/',
    ])
  })
})

describe('dates', () => {
  it('today() is a local YYYY-MM-DD date', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2024, 0, 5, 23, 30))
    expect(today()).toBe('2024-01-05')
    vi.useRealTimers()
  })

  it('formatDate() does not shift the day across time zones', () => {
    const expected = new Date(2024, 4, 1).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
    expect(formatDate('2024-05-01')).toBe(expected)
  })
})
