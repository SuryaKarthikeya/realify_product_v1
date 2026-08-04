import { ROUTES } from '@/constants/routes';

/**
 * The bridge between the Workspace URL vocabulary and the internal domain keys.
 *
 * URLs use the product's words (`/workspace/revenue`); datasets are still keyed
 * by the wire values (`sales`). Converting at this one boundary keeps both
 * stable — the URL can be renamed without touching a dataset, and vice versa.
 */
export const DOMAIN_SEGMENTS = {
  sales:     'revenue',
  margin:    'margin',
  cash:      'cash',
  inventory: 'inventory',
  ads:       'ads',
};

/** The domain Workspace lands on when the URL names none. */
export const DEFAULT_DOMAIN = 'sales';

export const SEGMENT_DOMAINS = Object.fromEntries(
  Object.entries(DOMAIN_SEGMENTS).map(([domain, segment]) => [segment, domain])
);

/** True when `segment` names a real domain. */
export const isDomainSegment = (segment) => Boolean(segment) && segment in SEGMENT_DOMAINS;

/** URL segment (or a legacy domain key) -> internal domain key. */
export const toDomainKey = (segment) => SEGMENT_DOMAINS[segment] || segment || DEFAULT_DOMAIN;

/** Internal domain key -> its AI View URL. */
export const workspacePath = (domain) =>
  `${ROUTES.WORKSPACE}/${DOMAIN_SEGMENTS[domain] || DOMAIN_SEGMENTS[DEFAULT_DOMAIN]}`;

/** Internal domain key -> its Dashboard View URL. */
export const dashboardPath = (domain) =>
  `${ROUTES.WORKSPACE}/dashboard/${DOMAIN_SEGMENTS[domain] || DOMAIN_SEGMENTS[DEFAULT_DOMAIN]}`;

export const WORKSPACE_PATHS = [
  ROUTES.WORKSPACE,
  ...Object.keys(DOMAIN_SEGMENTS).map(workspacePath),
];

/** True when `pathname` is any Workspace screen, in either view mode. */
export const isWorkspacePath = (pathname) =>
  pathname === ROUTES.WORKSPACE || pathname.startsWith(`${ROUTES.WORKSPACE}/`);

/** Internal domain key + index -> that insight's detail URL. */
export const insightPath = (domain, idx) =>
  `${ROUTES.WORKSPACE}/insight/${DOMAIN_SEGMENTS[domain] || DOMAIN_SEGMENTS[DEFAULT_DOMAIN]}/${idx}`;
