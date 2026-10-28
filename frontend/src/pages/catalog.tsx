import { useQuery } from '@tanstack/react-query'
import { SearchIcon } from 'lucide-react'
import { useDeferredValue } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ConsoleBadges, Cover, ErrorAlert, ProgressLine } from '@/components/common'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { api, type Game } from '@/lib/api'
import { useSession } from '@/lib/auth'

function GameCard({ game }: { game: Game }) {
  return (
    <Link to={`/games/${game.slug}`} className="group">
      <Card className="h-full gap-0 overflow-hidden py-0 transition-shadow group-hover:shadow-md">
        <Cover src={game.cover_url} alt={game.title} />
        <CardContent className="space-y-3 py-4">
          <div className="flex items-start justify-between gap-2">
            <h2 className="font-medium leading-tight">{game.title}</h2>
            <ConsoleBadges game={game} />
          </div>
          {game.unlocked_count !== null && (game.in_library || game.unlocked_count > 0) ? (
            <ProgressLine unlocked={game.unlocked_count} total={game.achievement_count} />
          ) : (
            <p className="text-xs text-muted-foreground">{game.achievement_count} achievements</p>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}

export function CatalogPage() {
  const { user } = useSession()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const library = !!user && params.get('library') === '1'
  const deferredQ = useDeferredValue(q)

  const games = useQuery({
    queryKey: ['games', { q: deferredQ, library }],
    queryFn: () => api.games({ q: deferredQ, library }),
    placeholderData: (prev) => prev,
  })

  const update = (key: string, value: string) =>
    setParams(
      (p) => {
        if (value) p.set(key, value)
        else p.delete(key)
        return p
      },
      { replace: true },
    )

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold">{library ? 'My games' : 'Games'}</h1>
        <div className="flex gap-2">
          {user && (
            <div className="flex rounded-lg border p-0.5">
              <Button variant={library ? 'ghost' : 'secondary'} size="sm" onClick={() => update('library', '')}>
                All
              </Button>
              <Button variant={library ? 'secondary' : 'ghost'} size="sm" onClick={() => update('library', '1')}>
                My games
              </Button>
            </div>
          )}
          <div className="relative w-full sm:w-64">
            <SearchIcon className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search games"
              className="pl-8"
              value={q}
              onChange={(e) => update('q', e.target.value)}
            />
          </div>
        </div>
      </div>

      <ErrorAlert error={games.error} />

      {games.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-60 rounded-xl" />
          ))}
        </div>
      ) : games.data?.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {games.data.map((g) => (
            <GameCard key={g.slug} game={g} />
          ))}
        </div>
      ) : (
        games.data && (
          <p className="py-12 text-center text-muted-foreground">
            {q
              ? `No games match "${q}".`
              : library
                ? 'Your library is empty. Open a game and add it, or tick an achievement.'
                : 'No games in the catalog yet.'}
          </p>
        )
      )}
    </div>
  )
}
