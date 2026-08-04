import httpClient, { identityClient } from '@/services/httpClient';
import { storage } from '@/utils/storage';
import { API_PATHS } from '@/services/endpoints';

/**
 * Warms the sales-intelligence endpoint for the active shop.
 *
 * The response is intentionally not consumed — Workspace renders from
 * local datasets today and this call exists to trigger server-side
 * computation. Returns false when there is no shop to fetch for.
 */
export const fetchSalesIntelligence = async () => {
  const shop = storage.getActiveShop();
  if (!shop) return false;
  const platform = storage.getActivePlatform();
  await httpClient.get(`/${platform}/sales-intelligence`);
  return true;
};

/**
 * Maps one raw `actions[]` row from `/api/workspace` (or `/api/workspace/{domain}`)
 * onto the field names the Actions table — SignalsTable, its column config and
 * the shared Workspace filters — already expect. Both endpoints share this so
 * the mapping can't drift between the overview and a domain response.
 */
const normalizeAction = (action) => ({
  ...action,
  headline: action.description,
  headlineHighlight: action.description,
  whyMattersText: action.why,
  skuCount: action.skus,
  fulfillmentType: action.fulfillment,
  stockoutDays: action.stockout_days,
  exposureFormatted: action.impact,
  type: action.card_type,
  tagCategory: action.action,
});

/** The brief + 5 main KPI cards + overall action table rows shown when the Workspace page opens. */
export const getWorkspaceOverview = async (window = 30) => {
  const { data } = await identityClient.get(API_PATHS.WORKSPACE.OVERVIEW, { params: { window } });
  return { ...data, actions: (data.actions ?? []).map(normalizeAction) };
};

/** The 5 sub-stat cards for one domain, shown once a main KPI card is selected. Actions for that
 *  domain are a separate route — see getWorkspaceDomainActions — this response carries only `cards`. */
export const getWorkspaceDomainCards = async (domain, window = 30) => {
  const { data } = await identityClient.get(API_PATHS.WORKSPACE.DOMAIN(domain), { params: { window } });
  return data;
};

/** That domain's action table rows — GET /api/workspace/{domain}/actions. */
export const getWorkspaceDomainActions = async (domain, window = 30) => {
  const { data } = await identityClient.get(API_PATHS.WORKSPACE.DOMAIN_ACTIONS(domain), { params: { window } });
  return { ...data, actions: (data.actions ?? []).map(normalizeAction) };
};
