import { type ReactNode, lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Analytics } from '@vercel/analytics/react';
import { ErrorBoundary } from '@/components/error-boundary';
import { Route, Switch, useLocation, Router as WouterRouter } from 'wouter';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 0,
    },
  },
});

// Lazy page imports — design subagent will create these
const LandingPage        = lazy(() => import('@/pages/landing'));
const DemoPage           = lazy(() => import('@/pages/demo'));
const DashboardPage      = lazy(() => import('@/pages/dashboard'));
const CallsPage          = lazy(() => import('@/pages/calls'));
const StatementPage      = lazy(() => import('@/pages/statement-detail'));
const ClustersPage       = lazy(() => import('@/pages/clusters'));
const ClusterDetailPage  = lazy(() => import('@/pages/cluster-detail'));
const NotFoundPage       = lazy(() => import('@/pages/not-found-page'));

function PageSpinner() {
  return (
    <div
      className="state-panel"
      style={{
        minHeight: '100vh',
        border: 'none',
        background: 'var(--e-bg)',
      }}
    >
      <div className="spinner" />
      <div className="pager-meta">Loading GAWAH</div>
    </div>
  );
}

function Router() {
  return (
    <RoutedErrorBoundary>
      <Suspense fallback={<PageSpinner />}>
        <Switch>
          <Route path="/"                        component={LandingPage} />
          <Route path="/demo"                    component={DemoPage} />
          <Route path="/dashboard"               component={DashboardPage} />
          <Route path="/dashboard/:refCode"      component={StatementPage} />
          <Route path="/calls"                   component={CallsPage} />
          <Route path="/clusters"                component={ClustersPage} />
          <Route path="/clusters/:clusterId"     component={ClusterDetailPage} />
          <Route                                 component={NotFoundPage} />
        </Switch>
      </Suspense>
    </RoutedErrorBoundary>
  );
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

/** Tracks SPA navigations for Vercel Web Analytics (must sit inside WouterRouter). */
function VercelAnalytics() {
  const [location] = useLocation();
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const path = `${base}${location || '/'}`.replace(/\/{2,}/g, '/') || '/';

  return <Analytics mode={import.meta.env.PROD ? 'production' : 'development'} path={path} route={location || '/'} />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
        <Router />
        <VercelAnalytics />
      </WouterRouter>
    </QueryClientProvider>
  );
}

export default App;
