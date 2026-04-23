'use client';

/**
 * Protected Route Component
 *
 * Wraps protected pages and redirects to login if not authenticated
 */

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/auth-context';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading, checkAuth } = useAuth();
  const router = useRouter();
  const [isChecking, setIsChecking] = React.useState(true);

  React.useEffect(() => {
    const verifyAuth = async () => {
      if (isLoading) return;

      if (!user) {
        router.push('/login');
        return;
      }

      // Verify token is still valid and user is admin
      const isValid = await checkAuth();
      if (!isValid) {
        router.push('/login');
        return;
      }

      setIsChecking(false);
    };

    verifyAuth();
  }, [user, isLoading, router, checkAuth]);

  if (isLoading || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}
