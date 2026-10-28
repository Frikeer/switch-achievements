import { Link, Navigate, useNavigate, useSearchParams } from 'react-router'
import { AuthCard } from '@/components/auth-card'
import { ErrorAlert } from '@/components/common'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi, isVerificationPending, useAuthMutation, useSession } from '@/lib/auth'

/** Only allow redirects to paths on this site. */
function safeNext(next: string | null) {
  return next?.startsWith('/') && !next.startsWith('//') ? next : '/'
}

export function LoginPage() {
  const { user } = useSession()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const next = safeNext(params.get('next'))
  const login = useAuthMutation(({ email, password }: { email: string; password: string }) =>
    authApi.login(email, password),
  )

  if (user) return <Navigate to={next} replace />

  if (login.data && isVerificationPending(login.data)) {
    return (
      <AuthCard
        title="Verify your email"
        description="Your email address isn't verified yet. We've sent you a new link; open it to finish logging in."
      />
    )
  }

  return (
    <AuthCard
      title="Log in"
      footer={
        <p>
          New here?{' '}
          <Link to="/signup" className="underline">
            Create an account
          </Link>
        </p>
      }
    >
      <form
        className="grid gap-4"
        onSubmit={(e) => {
          e.preventDefault()
          const form = new FormData(e.currentTarget)
          login.mutate(
            { email: String(form.get('email')), password: String(form.get('password')) },
            { onSuccess: (resp) => resp.meta?.is_authenticated && navigate(next, { replace: true }) },
          )
        }}
      >
        <ErrorAlert error={login.error} />
        <div className="grid gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" name="email" type="email" autoComplete="email" required />
        </div>
        <div className="grid gap-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link to="/account/password/reset" className="text-xs text-muted-foreground underline">
              Forgot password?
            </Link>
          </div>
          <Input id="password" name="password" type="password" autoComplete="current-password" required />
        </div>
        <Button type="submit" disabled={login.isPending}>
          Log in
        </Button>
      </form>
    </AuthCard>
  )
}
