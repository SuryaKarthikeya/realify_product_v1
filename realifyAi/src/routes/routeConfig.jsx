import { lazy } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { ROUTES } from '@/constants/routes';
import { DEFAULT_DOMAIN, DOMAIN_SEGMENTS } from '@/features/workspace';
import RedirectWithParams from '@/routes/RedirectWithParams';

/**
 * Route registry.
 *
 * Every route-level view is code-split. Adding a page means adding one lazy
 * import and one entry below — no other file changes.
 *
 * Workspace is a nested route: `/workspace` is the parent and each domain is a
 * child segment, so the URL structure mirrors the product structure. The
 * catch-all must stay last.
 */

const Onboarding                = lazy(() => import('@/features/onboarding/pages/OnboardingLayout'));
const MarketplaceConnectionPage = lazy(() => import('@/features/onboarding/pages/MarketplaceConnectionPage'));
const PrivacyPolicy             = lazy(() => import('@/features/onboarding/pages/PrivacyPolicy'));
const TermsOfService            = lazy(() => import('@/features/onboarding/pages/TermsOfService'));

const WorkspacePage             = lazy(() => import('@/features/workspace/pages/WorkspacePage'));
const InsightDetailPage         = lazy(() => import('@/features/workspace/pages/InsightDetailPage'));
const RollbackPage              = lazy(() => import('@/features/workspace/pages/RollbackPage'));
const SimulationPage            = lazy(() => import('@/features/workspace/modules/simulation/pages/SimulationPage'));
const DashboardViewPage         = lazy(() => import('@/features/workspace/modules/dashboard-view/pages/DashboardViewPage'));

const History                   = lazy(() => import('@/features/history/pages/HistoryPage'));
const HistoryDetailPage         = lazy(() => import('@/features/history/pages/HistoryDetailPage'));

const Screener                  = lazy(() => import('@/features/screener/pages/ScreenerPage'));
const ScreenerActionDetailPage  = lazy(() => import('@/features/screener/pages/ScreenerActionDetailPage'));

const ActionsPage               = lazy(() => import('@/features/action-center/pages/ActionsPage'));
const NewAnalysisPage           = lazy(() => import('@/features/new-analysis/pages/NewAnalysisPage'));
const SettingsPage              = lazy(() => import('@/features/settings/pages/SettingsPage'));
const ProductViewPage           = lazy(() => import('@/features/product-view/pages/ProductViewPage'));
const ComparisonPage            = lazy(() => import('@/features/comparison/pages/ComparisonPage'));
const ProductsListPage          = lazy(() => import('@/features/products/pages/ProductsListPage'));
const AgentsPage                = lazy(() => import('@/features/agents/pages/AgentsPage'));
const AgentProfilePage          = lazy(() => import('@/features/agents/pages/AgentProfilePage'));
const IntegrationsPage          = lazy(() => import('@/features/integrations/pages/IntegrationsPage'));
const ConnectorDetailPage       = lazy(() => import('@/features/integrations/pages/ConnectorDetailPage'));
const NotificationsPage         = lazy(() => import('@/features/notifications/pages/NotificationsPage'));
const ActionLogPage             = lazy(() => import('@/features/action-log/pages/ActionLogPage'));
const ProfitAdsPage             = lazy(() => import('@/features/profit-ads/pages/ProfitAdsPage'));

const InviteLoginPage           = lazy(() => import('@/features/auth/pages/InviteLoginPage'));
const Unauthorized              = lazy(() => import('@/features/auth/pages/Unauthorized'));

// Built and shipped, but intentionally unrouted — see ARCHITECTURE.md
// "Parked features". Uncomment the import and the matching entry below to
// re-enable; nothing else needs to change.
const DiscoverPage              = lazy(() => import('@/features/discover/pages/DiscoverPage'));
const HubsPage                  = lazy(() => import('@/features/hubs/pages/HubsPage'));

/** Strips the `/workspace/` prefix so a constant can be used as a child path. */
const child = (absolutePath) => absolutePath.slice(ROUTES.WORKSPACE.length + 1);

/** `/workspace` and everything beneath it. */
const workspaceRoute = {
  path: ROUTES.WORKSPACE,
  element: <Outlet />,
  children: [
    // Bare /workspace is never a resting place — land on the default domain
    // so the URL always names what is on screen.
    { index: true, element: <Navigate to={DOMAIN_SEGMENTS[DEFAULT_DOMAIN]} replace /> },
    { path: child(ROUTES.DASHBOARD_VIEW),     element: <DashboardViewPage /> },
    { path: child(ROUTES.WORKSPACE_INSIGHT),  element: <InsightDetailPage /> },
    { path: child(ROUTES.WORKSPACE_SIMULATE), element: <SimulationPage /> },
    { path: child(ROUTES.WORKSPACE_ROLLBACK), element: <RollbackPage /> },
    // One page renders every domain; the :domainSegment param decides which.
    // Static siblings above rank higher, so they are never shadowed.
    { path: ':domainSegment', element: <WorkspacePage fullWidthInsights={true} /> },
  ],
};

/**
 * Legacy URL -> canonical URL. These paths shipped before the Workspace
 * rename, so they stay resolvable indefinitely: existing bookmarks and shared
 * links must keep working. They are redirect sources only — nothing in the app
 * navigates to them.
 */
const LEGACY_REDIRECTS = [
  [ROUTES.LEGACY_WORKSPACE,          ROUTES.WORKSPACE],
  [ROUTES.LEGACY_REVENUE,            ROUTES.REVENUE],
  [ROUTES.LEGACY_MARGIN,             ROUTES.MARGIN],
  [ROUTES.LEGACY_CASH,               ROUTES.CASH],
  [ROUTES.LEGACY_INVENTORY,          ROUTES.INVENTORY],
  [ROUTES.LEGACY_ADS,                ROUTES.ADS],
  [ROUTES.LEGACY_WORKSPACE_SIMULATE, ROUTES.WORKSPACE_SIMULATE],
  [ROUTES.LEGACY_WORKSPACE_ROLLBACK, ROUTES.WORKSPACE_ROLLBACK],
];

/** Same, for legacy URLs that carry params. */
const LEGACY_PARAM_REDIRECTS = [
  [ROUTES.LEGACY_WORKSPACE_INSIGHT, ROUTES.WORKSPACE_INSIGHT],
  [ROUTES.LEGACY_DASHBOARD_VIEW,    ROUTES.DASHBOARD_VIEW],
];

export const routes = [
  { path: ROUTES.ONBOARDING, element: <Onboarding /> },

  workspaceRoute,

  { path: ROUTES.HISTORY,           element: <History /> },
  { path: ROUTES.HISTORY_DETAIL,    element: <HistoryDetailPage /> },
  // { path: ROUTES.DISCOVER,       element: <DiscoverPage /> },
  { path: ROUTES.SCREENER_ACTIONS,  element: <ScreenerActionDetailPage /> },
  { path: `${ROUTES.SCREENER}/*`,   element: <Screener /> },
  { path: ROUTES.CONNECT_MARKETPLACES, element: <MarketplaceConnectionPage /> },
  { path: ROUTES.ACTIONS,           element: <ActionsPage /> },
  { path: ROUTES.NEW_ANALYSIS,      element: <NewAnalysisPage /> },
  { path: ROUTES.SETTINGS,          element: <SettingsPage /> },
  // { path: ROUTES.HUBS,           element: <HubsPage /> },
  { path: ROUTES.PRODUCT_VIEW,      element: <ProductViewPage /> },
  { path: ROUTES.COMPARISON,        element: <ComparisonPage /> },
  { path: ROUTES.NOTIFICATIONS,     element: <NotificationsPage /> },
  { path: ROUTES.PRODUCTS,          element: <ProductsListPage /> },
  { path: ROUTES.CATALOGUE,         element: <ProductsListPage /> },
  { path: ROUTES.AGENTS,            element: <AgentsPage /> },
  { path: ROUTES.AGENT_PROFILE,     element: <AgentProfilePage /> },
  { path: ROUTES.INTEGRATIONS,      element: <IntegrationsPage /> },
  { path: ROUTES.CONNECTOR_DETAIL,  element: <ConnectorDetailPage /> },
  { path: ROUTES.ACTION_LOG,        element: <ActionLogPage /> },
  { path: ROUTES.NAVIGATION,        element: <Navigate to={ROUTES.ACTION_LOG} replace /> },
  { path: ROUTES.PROFIT_ADS,        element: <ProfitAdsPage /> },

  { path: ROUTES.LOGIN,             element: <InviteLoginPage /> },
  { path: ROUTES.UNAUTHORIZED,      element: <Unauthorized /> },
  { path: ROUTES.PRIVACY_POLICY,    element: <PrivacyPolicy /> },
  { path: ROUTES.TERMS_OF_SERVICE,  element: <TermsOfService /> },

  // Legacy Workspace URLs — kept resolvable so old links never 404.
  ...LEGACY_REDIRECTS.map(([from, to]) => ({
    path: from,
    element: <Navigate to={to} replace />,
  })),
  ...LEGACY_PARAM_REDIRECTS.map(([from, to]) => ({
    path: from,
    element: <RedirectWithParams to={to} />,
  })),

  { path: '*', element: <Navigate to={ROUTES.ONBOARDING} replace /> },
];

// Referenced so the parked lazy chunks stay reachable to the bundler exactly as
// they were before the refactor. Remove alongside the commented routes above if
// the features are ever retired.
export const PARKED = { DiscoverPage, HubsPage };
