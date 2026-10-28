import { Link, Navigate } from 'react-router'
import { AuthCard } from '@/components/auth-card'
import { ErrorAlert } from '@/components/common'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi, isVerificationPending, useAuthMutation, useSession } from '@/lib/auth'

export function SignupPage() {
  const { user } = useSession()
  const signup = useAuthMutation(({ email, password }: { email: string; password: string }) =>
    authApi.signup(email, password),
  )

  if (user) return <Navigate to="/" replace />

  if (signup.data && isVerificationPending(signup.data)) {
    return (
      <AuthCard
        title="Check your email"
        description="We've sent you a verification link. Open it in this browser to finish signing up."
      />
    )
  }

  return (
    <AuthCard
      title="Create an account"
      description="Track your Switch achievements across all your games."
      footer={
        <p>
          Already have an account?{' '}
          <Link to="/login" className="underline">
            Log in
          </Link>
        </p>
      }
    >
      <form
        className="grid gap-4"
        onSubmit={(e) => {
          e.preventDefault()
          const form = new FormData(e.currentTarget)
          signup.mutate({ email: String(form.get('email')), password: String(form.get('password')) })
        }}
      >
        <ErrorAlert error={signup.error} />
        <div className="grid gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" name="email" type="email" autoComplete="email" required />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" name="password" type="password" autoComplete="new-password" minLength={8} required />
        </div>
        <Button type="submit" disabled={signup.isPending}>
          Sign up
        </Button>
      </form>
    </AuthCard>
  )
}
