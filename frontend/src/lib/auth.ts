import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, request } from './api'

// django-allauth headless "browser" client API.
// https://docs.allauth.org/en/latest/headless/openapi-specification/
const BASE = '/_allauth/browser/v1'

export type User = { id: number; email: string; display: string }

type Flow = { id: string; is_pending?: boolean }

export type AuthResponse = {
  status: number
  data?: { user?: User; flows?: Flow[] }
  meta?: { is_authenticated: boolean }
}

// allauth answers 401 for "not logged in (yet)", e.g. after signup while email
// verification is pending, or after logout. Treat that as a normal result.
async function authRequest(method: string, path: string, data?: unknown): Promise<AuthResponse> {
  try {
    return await request<AuthResponse>(method, BASE + path, data)
  } catch (e) {
    if (e instanceof ApiError && (e.status === 401 || e.status === 410)) {
      return e.body as AuthResponse
    }
    throw e
  }
}

export const isVerificationPending = (resp: AuthResponse) =>
  !!resp.data?.flows?.some((f) => f.id === 'verify_email' && f.is_pending)

export const authApi = {
  session: () => authRequest('GET', '/auth/session'),
  login: (email: string, password: string) => authRequest('POST', '/auth/login', { email, password }),
  signup: (email: string, password: string) => authRequest('POST', '/auth/signup', { email, password }),
  logout: () => authRequest('DELETE', '/auth/session'),
  verifyEmail: (key: string) => authRequest('POST', '/auth/email/verify', { key }),
  requestPasswordReset: (email: string) => authRequest('POST', '/auth/password/request', { email }),
  resetPassword: (key: string, password: string) => authRequest('POST', '/auth/password/reset', { key, password }),
}

const SESSION_KEY = ['session']

/** The logged-in user, or null. Fetching the session also sets the CSRF cookie. */
export function useSession() {
  const query = useQuery({ queryKey: SESSION_KEY, queryFn: authApi.session, staleTime: Infinity })
  return {
    user: query.data?.meta?.is_authenticated ? (query.data.data?.user ?? null) : null,
    isLoading: query.isLoading,
  }
}

/**
 * Wraps an auth call so that the session (and every user-specific query) is
 * refreshed from its response.
 */
export function useAuthMutation<V>(fn: (vars: V) => Promise<AuthResponse>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (resp) => {
      const wasAuthenticated = queryClient.getQueryData<AuthResponse>(SESSION_KEY)?.meta?.is_authenticated
      queryClient.setQueryData(SESSION_KEY, resp)
      if (wasAuthenticated !== resp.meta?.is_authenticated) {
        queryClient.resetQueries({ predicate: (q) => q.queryKey[0] !== SESSION_KEY[0] })
      }
    },
  })
}
