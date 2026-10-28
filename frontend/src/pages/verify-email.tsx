import { useEffect, useRef } from 'react'
import { Link, useParams } from 'react-router'
import { AuthCard } from '@/components/auth-card'
import { ErrorAlert } from '@/components/common'
import { Button } from '@/components/ui/button'
import { authApi, useAuthMutation } from '@/lib/auth'

export function VerifyEmailPage() {
  const { key = '' } = useParams()
  const verify = useAuthMutation(authApi.verifyEmail)
  const sent = useRef(false)

  // Verify once on load (refs guard against StrictMode's double effect).
  useEffect(() => {
    if (!sent.current) {
      sent.current = true
      verify.mutate(key)
    }
  }, [key, verify])

  if (verify.error) {
    return (
      <AuthCard title="Verification failed">
        <ErrorAlert error={verify.error} />
      </AuthCard>
    )
  }
  if (!verify.data) return <AuthCard title="Verifying your email…" />

  return verify.data.meta?.is_authenticated ? (
    <AuthCard title="Email verified" description="You're all set and logged in.">
      <Button asChild>
        <Link to="/">Browse games</Link>
      </Button>
    </AuthCard>
  ) : (
    <AuthCard title="Email verified" description="Your email address is confirmed. Log in to continue.">
      <Button asChild>
        <Link to="/login">Log in</Link>
      </Button>
    </AuthCard>
  )
}
