import { ROUTES } from "@/constants/routes";

/**
 * Maps each role to the list of base path prefixes it may access.
 *
 * ProtectedRoute uses startsWith matching, so granting "/workspace" also
 * covers "/workspace/revenue", "/workspace/simulate", etc.
 *
 * AppSidebar uses exact matching against nav-item hrefs, which are always
 * the base paths listed here — so the two approaches stay consistent.
 */
export const rolePermissions = {
  admin: [
    ROUTES.NEW_ANALYSIS,          // /new-analysis
    ROUTES.HISTORY,               // /history
    ROUTES.WORKSPACE,         // /intel  (+ all sub-routes) — the Workspace
    ROUTES.SCREENER,              // /research  (+ /research/actions/*)
    ROUTES.SETTINGS,              // /settings
    ROUTES.PRODUCTS,              // /products
    ROUTES.CATALOGUE,             // /catalogue
    ROUTES.AGENTS,                // /agents
    ROUTES.INTEGRATIONS,          // /integrations
    ROUTES.ACTION_LOG,            // /action-log
    ROUTES.PROFIT_ADS,            // /profit-ads
    ROUTES.NOTIFICATIONS,         // /notifications
    ROUTES.CONNECT_MARKETPLACES,  // /connect-marketplaces
    ROUTES.PRODUCT_VIEW,          // /product-view
    ROUTES.ACTIONS,               // /actions
  ],

  analyst: [
    ROUTES.NEW_ANALYSIS,
    ROUTES.HISTORY,
    ROUTES.WORKSPACE,
    ROUTES.SCREENER,
    ROUTES.NOTIFICATIONS,
  ],

  viewer: [
    ROUTES.HISTORY,
    ROUTES.WORKSPACE,
    ROUTES.NOTIFICATIONS,
  ],

  "inventory-planner": [
    ROUTES.WORKSPACE,
    ROUTES.PRODUCTS,
    ROUTES.NOTIFICATIONS,
  ],

  "sales-manager": [
    ROUTES.WORKSPACE,
    ROUTES.SCREENER,
    ROUTES.NOTIFICATIONS,
  ],
};
