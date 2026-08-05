/**
 * Every backend path this app calls, in one place — the same discipline
 * constants/routes.js applies to frontend routes. A path changes here once;
 * nothing else in src/ hardcodes a '/login' or '/onboard/reports' string.
 *
 * These are relative to identityClient's baseURL (`${backendUrl}/api`) in
 * httpClient.js, NOT apiClient's (`${backendUrl}/api/v1`) — login, signup
 * and onboarding are unversioned routes, never mounted under /api/v1.
 */
export const API_PATHS = {
  AUTH: {
    LOGIN: '/login',
    SIGNUP: '/billing/signup',
    LOGOUT: '/logout',
    ME: '/me',
  },
  ONBOARDING: {
    IDENTIFY: '/ingest/identify',
    COMMIT_REPORTS: '/onboard/reports',
    COGS_TEMPLATE: '/cogs/template',
    // Read-only: channel + report catalog, so the checklist can render
    // honestly (real report types, real "unlocks" copy) before the user has
    // dropped a single file — not part of the 3-API scope by name, but
    // required for the CSV Upload step to show real data instead of a blank
    // list pre-upload.
    CATALOG: '/ingest/catalog',
  },
  // Per-tenant data coverage: which canonical fields real uploaded reports have
  // populated, how many detector groups that lights up, and the SKU total.
  // Mounted at /api/data/... and /api/v1/data/... — we use the unversioned one.
  DATA: {
    COMPLETENESS: '/data/completeness',
    SKUS: '/skus',
  },
  // Unversioned, same as ONBOARDING/AUTH above — mounted at /api/workspace,
  // not /api/v1/workspace.
  WORKSPACE: {
    OVERVIEW: '/workspace',
    DOMAIN: (domain) => `/workspace/${domain}`,
    // Domain actions are their own route — unlike OVERVIEW, DOMAIN's response
    // carries only `cards`, not `actions`.
    DOMAIN_ACTIONS: (domain) => `/workspace/${domain}/actions`,
  },
};
