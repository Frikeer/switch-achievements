import { TrophyIcon } from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router'
import { Button } from '@/components/ui/button'
import { authApi, useAuthMutation, useSession } from '@/lib/auth'
import { cn } from '@/lib/utils'

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        cn('text-sm transition-colors hover:text-foreground', isActive ? 'text-foreground' : 'text-muted-foreground')
      }
    >
      {children}
    </NavLink>
  )
}

export function Layout() {
  const { user, isLoading } = useSession()
  const navigate = useNavigate()
  const logout = useAuthMutation(authApi.logout)

  return (
    <div className="min-h-svh bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <TrophyIcon className="size-5 text-red-500" />
            <span className="hidden sm:inline">Switch Achievements</span>
          </Link>
          <nav className="flex items-center gap-4">
            <NavItem to="/">Games</NavItem>
            {user && <NavItem to="/dashboard">Dashboard</NavItem>}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            {isLoading ? null : user ? (
              <>
                <span className="hidden text-sm text-muted-foreground md:inline">{user.email}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={logout.isPending}
                  onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/') })}
                >
                  Log out
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/login">Log in</Link>
                </Button>
                <Button size="sm" asChild>
                  <Link to="/signup">Sign up</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
