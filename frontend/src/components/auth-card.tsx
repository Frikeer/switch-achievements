import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

export function AuthCard({
  title,
  description,
  footer,
  children,
}: {
  title: string
  description?: React.ReactNode
  footer?: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <Card className="mx-auto mt-8 max-w-sm">
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      {children && <CardContent>{children}</CardContent>}
      {footer && <CardFooter className="text-sm text-muted-foreground">{footer}</CardFooter>}
    </Card>
  )
}
