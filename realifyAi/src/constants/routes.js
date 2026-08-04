/**
 * Every route path in the app. Nothing should hardcode a path string —
 * `routeConfig.jsx`, `RolePermission.js` and every `navigate()` call read
 * from here, so a path can be changed in exactly one place.
 */
export const ROUTES = {
  ONBOARDING:           "/",
  LOGIN:                "/login",
  UNAUTHORIZED:         "/unauthorized",

  // ── Workspace (canonical) ──────────────────────────────────────────────
  // Legacy /intel and /detailed-view URLs still resolve, via the permanent
  // redirects declared in routeConfig.jsx. They are never navigation targets.
  WORKSPACE:            "/workspace",
  REVENUE:              "/workspace/revenue",
  MARGIN:               "/workspace/margin",
  CASH:                 "/workspace/cash",
  INVENTORY:            "/workspace/inventory",
  ADS:                  "/workspace/ads",
  DASHBOARD_VIEW:       "/workspace/dashboard/:domain",
  WORKSPACE_INSIGHT:    "/workspace/insight/:domain/:idx",
  WORKSPACE_SIMULATE:   "/workspace/simulate",
  WORKSPACE_ROLLBACK:   "/workspace/rollback",

  // ── Legacy Workspace URLs (redirect targets only) ──────────────────────
  LEGACY_WORKSPACE:          "/intel",
  LEGACY_REVENUE:            "/intel/sales",
  LEGACY_MARGIN:             "/intel/margin",
  LEGACY_CASH:               "/intel/cash",
  LEGACY_INVENTORY:          "/intel/inventory",
  LEGACY_ADS:                "/intel/ads",
  LEGACY_DASHBOARD_VIEW:     "/detailed-view/:domain",
  LEGACY_WORKSPACE_INSIGHT:  "/intel/insight/:domain/:idx",
  LEGACY_WORKSPACE_SIMULATE: "/intel/simulate",
  LEGACY_WORKSPACE_ROLLBACK: "/intel/rollback",

  HISTORY:              "/history",
  HISTORY_DETAIL:       "/history/detail",
  // DISCOVER:             "/discover",
  SCREENER:             "/research",
  SCREENER_ACTIONS:     "/research/actions/:id",
  CONNECT_MARKETPLACES: "/connect-marketplaces",
  ACTIONS:              "/actions",
  NEW_ANALYSIS:         "/new-analysis",
  SETTINGS:             "/settings",
  // HUBS:                 "/hubs",
  PRODUCT_VIEW:         "/product-view",
  COMPARISON:           "/comparison",
  PRIVACY_POLICY:       "/privacy-policy",
  TERMS_OF_SERVICE:     "/terms-of-service",
  NOTIFICATIONS:        "/notifications",
  ACTION_LOG:           "/action-log",
  PRODUCTS:             "/products",
  CATALOGUE:            "/catalogue",
  AGENTS:               "/agents",
  AGENT_PROFILE:        "/agents/:agentId",
  INTEGRATIONS:         "/integrations",
  CONNECTOR_DETAIL:     "/integrations/:connectorId",
  PROFIT_ADS:           "/profit-ads",
  NAVIGATION:           "/navigation",   // legacy entry point, redirects to ACTION_LOG
};
