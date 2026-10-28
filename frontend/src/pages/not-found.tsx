import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <Link to="/" className="mt-2 inline-block text-muted-foreground underline">
        Back to the games
      </Link>
    </div>
  )
}
