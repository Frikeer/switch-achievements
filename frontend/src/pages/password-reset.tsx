import { Link, useParams } from 'react-router'
import { AuthCard } from '@/components/auth-card'
import { ErrorAlert } from '@/components/common'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi, useAuthMutation } from '@/lib/auth'

export function PasswordResetRequestPage() {
  const reset = useAuthMutation(authApi.requestPasswordReset)

  if (reset.isSuccess) {
    return (
      <AuthCard
        title="Check your email"
        description="If an account exists for that address, we've sent a link to reset your password."
      />
    )
  }

  return (
    <AuthCard
      title="Reset your password"
      description="Enter your email and we'll send you a reset link."
      footer={
        <Link to="/login" className="underline">
          Back to log in
        </Link>
      }
    >
      <form
        className="grid gap-4"
        onSubmit={(e) => {
          e.preventDefault()
          reset.mutate(String(new FormData(e.currentTarget).get('email')))
        }}
      >
        <ErrorAlert error={reset.error} />
        <div className="grid gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" name="email" type="email" autoComplete="email" required />
        </div>
        <Button type="submit" disabled={reset.isPending}>
          Send reset link
        </Button>
      </form>
    </AuthCard>
  )
}

export function PasswordResetKeyPage() {
  const { key = '' } = useParams()
  const reset = useAuthMutation((password: string) => authApi.resetPassword(key, password))

  if (reset.isSuccess) {
    return (
      <AuthCard title="Password changed" description="You can now log in with your new password.">
        <Button asChild>
          <Link to="/login">Log in</Link>
        </Button>
      </AuthCard>
    )
  }

  return (
    <AuthCard title="Choose a new password">
      <form
        className="grid gap-4"
        onSubmit={(e) => {
          e.preventDefault()
          reset.mutate(String(new FormData(e.currentTarget).get('password')))
        }}
      >
        <ErrorAlert error={reset.error} />
        <div className="grid gap-2">
          <Label htmlFor="password">New password</Label>
          <Input id="password" name="password" type="password" autoComplete="new-password" minLength={8} required />
        </div>
        <Button type="submit" disabled={reset.isPending}>
          Change password
        </Button>
      </form>
    </AuthCard>
  )
}
