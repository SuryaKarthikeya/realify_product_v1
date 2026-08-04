import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import ErrorBoundary from '@/components/feedback/ErrorBoundary';
import AppRoutes from '@/routes/AppRoutes';
import { useOAuth } from '@/hooks/useOAuth';
import { useAuthStore } from '@/store/useAuthStore';

function App() {
  useOAuth();

  // Reconcile persisted auth state against the real session once on boot —
  // the cookie may have expired or been revoked since the last visit.
  const checkSession = useAuthStore((s) => s.checkSession);
  useEffect(() => {
    checkSession();
  }, [checkSession]);

  return (
    <ErrorBoundary>
      <Router>
        <AppRoutes />
      </Router>
    </ErrorBoundary>
  );
}

export default App;
