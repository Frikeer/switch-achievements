import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { Layout } from '@/components/layout'
import { Toaster } from '@/components/ui/sonner'
import { ApiError } from '@/lib/api'
import { CatalogPage } from '@/pages/catalog'
import { DashboardPage } from '@/pages/dashboard'
import { GamePage } from '@/pages/game'
import { LoginPage } from '@/pages/login'
import { NotFoundPage } from '@/pages/not-found'
import { PasswordResetKeyPage, PasswordResetRequestPage } from '@/pages/password-reset'
import { SignupPage } from '@/pages/signup'
import { VerifyEmailPage } from '@/pages/verify-email'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Don't retry client errors such as 404 or 403.
      retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
    },
  },
})

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <CatalogPage /> },
      { path: '/games/:slug', element: <GamePage /> },
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/login', element: <LoginPage /> },
      { path: '/signup', element: <SignupPage /> },
      { path: '/account/verify-email/:key', element: <VerifyEmailPage /> },
      { path: '/account/password/reset', element: <PasswordResetRequestPage /> },
      { path: '/account/password/reset/key/:key', element: <PasswordResetKeyPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster position="bottom-right" />
    </QueryClientProvider>
  </StrictMode>,
)
