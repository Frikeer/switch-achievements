import { useQuery } from '@tanstack/react-query'
import { Link, Navigate } from 'react-router'
import { ErrorAlert, ProgressLine } from '@/components/common'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { api } from '@/lib/api'
import { useSession } from '@/lib/auth'
import { formatDate } from '@/lib/dates'

function StatCard({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <Card className="gap-1 py-4">
      <CardContent>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold tabular-nums">{value}</p>
        {detail && <p className="text-xs text-muted-foreground">{detail}</p>}
      </CardContent>
    </Card>
  )
}

export function DashboardPage() {
  const { user, isLoading } = useSession()
  const stats = useQuery({ queryKey: ['stats'], queryFn: api.stats, enabled: !!user })

  if (!isLoading && !user) return <Navigate to="/login?next=/dashboard" replace />
  if (stats.isLoading || isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    )
  }
  if (!stats.data) return <ErrorAlert error={stats.error} />
  const s = stats.data

  if (!s.games) {
    return (
      <div className="py-12 text-center">
        <h1 className="text-2xl font-semibold">Your dashboard</h1>
        <p className="mt-2 text-muted-foreground">
          No games yet.{' '}
          <Link to="/" className="underline">
            Browse the catalog
          </Link>{' '}
          and start ticking off achievements.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Your dashboard</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Completion" value={`${s.percent}%`} />
        <StatCard label="Achievements" value={s.unlocked} detail={`of ${s.total}`} />
        <StatCard label="Games" value={s.games} />
        <StatCard label="Completed games" value={s.completed_games} detail="100% unlocked" />
      </div>

      <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
        <Card>
          <CardHeader>
            <CardTitle>Progress by game</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {s.per_game.map((g) => (
              <Link key={g.slug} to={`/games/${g.slug}`} className="block rounded-md hover:bg-muted/50">
                <p className="mb-1 text-sm font-medium">{g.title}</p>
                <ProgressLine unlocked={g.unlocked} total={g.total} />
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recently unlocked</CardTitle>
          </CardHeader>
          <CardContent>
            {s.recent_unlocks.length ? (
              <ul className="space-y-3">
                {s.recent_unlocks.map((u) => (
                  <li key={u.achievement_id} className="flex items-center gap-3">
                    {u.icon_url ? (
                      <img src={u.icon_url} alt="" className="size-10 rounded" loading="lazy" />
                    ) : (
                      <div className="size-10 rounded bg-muted" />
                    )}
                    <div className="min-w-0 text-sm">
                      <p className="truncate font-medium">{u.name}</p>
                      <p className="truncate text-muted-foreground">
                        <Link to={`/games/${u.game_slug}`} className="hover:underline">
                          {u.game_title}
                        </Link>{' '}
                        · {formatDate(u.unlocked_at)}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">Nothing unlocked yet.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
