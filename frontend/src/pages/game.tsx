import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeftIcon, EyeIcon, LockIcon, PencilIcon } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { toast } from 'sonner'
import { ConsoleBadges, Cover, ErrorAlert, ProgressLine } from '@/components/common'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { type Achievement, api, type GameDetail } from '@/lib/api'
import { useSession } from '@/lib/auth'
import { formatDate, today } from '@/lib/dates'
import { cn } from '@/lib/utils'

type Filter = 'all' | 'unlocked' | 'locked'

type UnlockChange = { id: number; unlocked: boolean; unlocked_at?: string; note?: string }

/** Tick/untick/edit an achievement, updating the game page optimistically. */
function useUnlockMutation(slug: string) {
  const queryClient = useQueryClient()
  const key = ['game', slug]

  return useMutation({
    mutationFn: ({ id, unlocked, unlocked_at, note }: UnlockChange) =>
      unlocked ? api.unlock(id, { unlocked_at, note }) : api.lock(id),
    onMutate: async (change) => {
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<GameDetail>(key)
      queryClient.setQueryData<GameDetail>(key, (game) => {
        if (!game) return game
        const achievements = game.achievements.map((a) =>
          a.id !== change.id
            ? a
            : change.unlocked
              ? { ...a, unlocked_at: change.unlocked_at ?? a.unlocked_at ?? today(), note: change.note ?? a.note }
              : { ...a, unlocked_at: null, note: '' },
        )
        return {
          ...game,
          achievements,
          in_library: change.unlocked ? true : game.in_library,
          unlocked_count: achievements.filter((a) => a.unlocked_at).length,
        }
      })
      return { previous }
    },
    onError: (error, _change, context) => {
      if (context?.previous) queryClient.setQueryData(key, context.previous)
      toast.error(error.message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: key })
      queryClient.invalidateQueries({ queryKey: ['games'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

function EditUnlockDialog({
  achievement,
  onClose,
  onSave,
}: {
  achievement: Achievement | null
  onClose: () => void
  onSave: (change: UnlockChange) => void
}) {
  return (
    <Dialog open={!!achievement} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        {achievement && (
          <form
            key={achievement.id}
            className="grid gap-4"
            onSubmit={(e) => {
              e.preventDefault()
              const form = new FormData(e.currentTarget)
              onSave({
                id: achievement.id,
                unlocked: true,
                unlocked_at: String(form.get('unlocked_at')),
                note: String(form.get('note')),
              })
              onClose()
            }}
          >
            <DialogHeader>
              <DialogTitle>{achievement.name}</DialogTitle>
              <DialogDescription>When did you unlock this, and anything worth remembering?</DialogDescription>
            </DialogHeader>
            <div className="grid gap-2">
              <Label htmlFor="unlocked_at">Unlocked on</Label>
              <Input
                id="unlocked_at"
                name="unlocked_at"
                type="date"
                required
                max={today()}
                defaultValue={achievement.unlocked_at ?? today()}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="note">Note</Label>
              <Textarea id="note" name="note" placeholder="Optional" defaultValue={achievement.note} />
            </div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit">Save</Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}

function AchievementRow({
  achievement: a,
  canEdit,
  onToggle,
  onEdit,
}: {
  achievement: Achievement
  canEdit: boolean
  onToggle: (unlocked: boolean) => void
  onEdit: () => void
}) {
  const unlocked = !!a.unlocked_at
  const [revealed, setRevealed] = useState(false)
  const masked = a.hidden && !unlocked && !revealed
  const icon = unlocked ? a.icon_url : a.icon_gray_url || a.icon_url

  return (
    <li className={cn('flex items-start gap-3 rounded-lg border p-3', unlocked && 'border-primary/30 bg-muted/40')}>
      {icon ? (
        <img src={icon} alt="" loading="lazy" className={cn('size-12 shrink-0 rounded', masked && 'blur-sm')} />
      ) : (
        <div className="flex size-12 shrink-0 items-center justify-center rounded bg-muted">
          <LockIcon className="size-5 text-muted-foreground" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <label htmlFor={`ach-${a.id}`} className={cn('font-medium', canEdit && 'cursor-pointer')}>
          {masked ? 'Hidden achievement' : a.name}
        </label>
        {masked ? (
          <button
            type="button"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
            onClick={() => setRevealed(true)}
          >
            <EyeIcon className="size-3.5" /> Reveal spoiler
          </button>
        ) : (
          a.description && <p className="text-sm text-muted-foreground">{a.description}</p>
        )}
        {unlocked && (
          <p className="mt-1 text-xs text-muted-foreground">
            Unlocked {formatDate(a.unlocked_at!)}
            {a.note && <span className="block whitespace-pre-line italic">{a.note}</span>}
          </p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {unlocked && canEdit && (
          <Button variant="ghost" size="icon-sm" onClick={onEdit} aria-label={`Edit date and note for ${a.name}`}>
            <PencilIcon />
          </Button>
        )}
        <Checkbox
          id={`ach-${a.id}`}
          className="size-5"
          checked={unlocked}
          disabled={!canEdit}
          onCheckedChange={(checked) => onToggle(checked === true)}
          aria-label={unlocked ? `Mark ${a.name} as locked` : `Mark ${a.name} as unlocked`}
        />
      </div>
    </li>
  )
}

export function GamePage() {
  const { slug = '' } = useParams()
  const { user } = useSession()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<Filter>('all')
  const [editing, setEditing] = useState<Achievement | null>(null)

  // User-specific data, but no user in the key: logging in/out resets queries.
  const game = useQuery({ queryKey: ['game', slug], queryFn: () => api.game(slug) })
  const data = game.data

  const unlock = useUnlockMutation(slug)
  const library = useMutation({
    mutationFn: (add: boolean) => (add ? api.addToLibrary(slug) : api.removeFromLibrary(slug)),
    onSuccess: (_r, add) => {
      toast.success(add ? 'Added to your games' : 'Removed from your games')
      queryClient.invalidateQueries({ queryKey: ['game', slug] })
      queryClient.invalidateQueries({ queryKey: ['games'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: (error) => toast.error(error.message),
  })

  if (game.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 rounded-xl" />
        <Skeleton className="h-20 rounded-lg" />
        <Skeleton className="h-20 rounded-lg" />
      </div>
    )
  }
  if (!data) return <ErrorAlert error={game.error} />

  const achievements = data.achievements
  const unlockedCount = achievements.filter((a) => a.unlocked_at).length
  const visible = achievements.filter((a) =>
    filter === 'all' ? true : filter === 'unlocked' ? a.unlocked_at : !a.unlocked_at,
  )

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeftIcon className="size-4" /> All games
      </Link>

      <div className="flex flex-col gap-6 sm:flex-row">
        <Cover src={data.cover_url} alt={data.title} className="rounded-xl sm:w-72" />
        <div className="flex flex-1 flex-col gap-3">
          <div>
            <h1 className="text-2xl font-semibold">{data.title}</h1>
            <ConsoleBadges game={data} />
          </div>
          <ProgressLine unlocked={unlockedCount} total={achievements.length} />
          {user ? (
            <Button
              variant={data.in_library ? 'outline' : 'default'}
              className="self-start"
              disabled={library.isPending}
              onClick={() => library.mutate(!data.in_library)}
            >
              {data.in_library ? 'Remove from my games' : 'Add to my games'}
            </Button>
          ) : (
            <p className="text-sm text-muted-foreground">
              <Link to="/login" className="underline">
                Log in
              </Link>{' '}
              to track your progress.
            </p>
          )}
        </div>
      </div>

      <div className="flex w-fit rounded-lg border p-0.5">
        {(['all', 'unlocked', 'locked'] as const).map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'secondary' : 'ghost'}
            size="sm"
            className="capitalize"
            onClick={() => setFilter(f)}
          >
            {f}
          </Button>
        ))}
      </div>

      {visible.length ? (
        <ul className="space-y-2">
          {visible.map((a) => (
            <AchievementRow
              key={a.id}
              achievement={a}
              canEdit={!!user}
              onToggle={(unlocked) => unlock.mutate({ id: a.id, unlocked })}
              onEdit={() => setEditing(a)}
            />
          ))}
        </ul>
      ) : (
        <p className="py-8 text-center text-muted-foreground">
          {achievements.length ? `No ${filter} achievements.` : 'This game has no achievements yet.'}
        </p>
      )}

      <EditUnlockDialog achievement={editing} onClose={() => setEditing(null)} onSave={unlock.mutate} />
    </div>
  )
}
