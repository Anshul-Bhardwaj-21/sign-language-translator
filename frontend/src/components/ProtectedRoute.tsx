import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAppContext } from '../contexts/AppContext'

export function ProtectedRoute() {
  const { user } = useAppContext()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}

