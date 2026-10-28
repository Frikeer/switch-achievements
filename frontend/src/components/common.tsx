import { AlertCircleIcon } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

export function ErrorAlert({ error }: { error: unknown }) {
  if (!error) return null
  return (
    <Alert variant="destructive">
      <AlertCircleIcon />
      <AlertDescription>{error instanceof Error ? error.message : String(error)}</AlertDescription>
    </Alert>
  )
}

export function ProgressLine({ unlocked, total, className }: { unlocked: number; total: number; className?: string }) {
  const percent = total ? Math.round((100 * unlocked) / total) : 0
  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>
          {unlocked} / {total}
        </span>
        <span>{percent}%</span>
      </div>
      <Progress value={percent} aria-label={`${percent}% complete`} />
    </div>
  )
}

export function Cover({ src, alt, className }: { src: string; alt: string; className?: string }) {
  return src ? (
    <img src={src} alt={alt} loading="lazy" className={cn('aspect-[460/215] w-full object-cover', className)} />
  ) : (
    <div
      className={cn(
        'flex aspect-[460/215] w-full items-center justify-center bg-muted text-sm text-muted-foreground',
        className,
      )}
    >
      {alt}
    </div>
  )
}
