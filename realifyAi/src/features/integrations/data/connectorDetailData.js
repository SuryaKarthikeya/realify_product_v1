import { CATEGORY_BY_KEY, isOnboarded } from '@/features/integrations/data/integrationsData';

/**
 * Content for the connector detail page — the screen "Resume Setup" opens.
 *
 * Same shape as the rest of the feature: a per-connector override merged over a
 * default derived from the connector's own row, so all 18 open a fully populated
 * page rather than only the ones written out by hand.
 */

export const DETAIL_PAGE_TABS = [
  'Overview',
  'Onboarding',
  'Scopes & Permissions',
  'Activity',
  'Data',
  'Settings',
];

/* ── Onboarding journey (the right rail, and the wizard's step rail) ── */

export const JOURNEY_STEPS = [
  { key: 'choose', label: 'Choose connector', hint: 'Pick the connector and review what it feeds' },
  { key: 'authorize', label: 'Authorize', hint: 'Grant secure access with OAuth 2.0' },
  { key: 'scopes', label: 'Scopes & permissions', hint: 'Review and save least-privilege scopes' },
  { key: 'consent', label: 'Access & consent', hint: 'Review data handling and consent' },
  { key: 'golive', label: 'Go live', hint: 'First sync completed successfully' },
];

/**
 * How far the journey has actually got.
 *
 * Everything up to Go live is done for a live connector; Go live itself completes
 * either because the user is standing on the wizard's last step right now
 * (`wizardStep`) or because they finished it earlier (`setupComplete`, persisted).
 * Without the second input the rail would drop Go live back to Pending as soon as
 * the user navigated away from the step that completed it.
 */
export const journeyProgress = (connector, wizardStep = 0, setupComplete = false) => {
  const isLive = connector?.status !== 'available';
  const base = isLive ? JOURNEY_STEPS.length - 1 : 0;
  const atGoLive =
    isOnboarded(connector, setupComplete) || wizardStep >= JOURNEY_STEPS.length - 1;
  const completed = Math.max(base, atGoLive ? JOURNEY_STEPS.length : base);

  return {
    completed,
    total: JOURNEY_STEPS.length,
    pct: Math.round((completed / JOURNEY_STEPS.length) * 100),
    steps: JOURNEY_STEPS.map((step, idx) => ({
      ...step,
      idx,
      done: idx < completed,
      /* The last step reads differently once it lands — "first sync completed"
         is a promise before, a statement after. */
      hint: step.key === 'golive' && idx < completed ? 'Integration is now active' : step.hint,
      status: idx < completed ? 'Completed' : 'Pending',
    })),
  };
};

/* ── Overview tab ── */

const OVERVIEW_OVERRIDES = {
  'amazon-sp-api': {
    connectedSince: 'Jul 15, 2026',
    connectedDays: '15 days',
    lastSyncAbsolute: 'Jul 30, 2026 10:42 AM',
    feeds: [
      { name: 'Orders', tag: 'Sales', when: '2m ago' },
      { name: 'Catalog', tag: 'Catalog', when: '2m ago' },
      { name: 'Inventory', tag: 'Inventory', when: '2m ago' },
      { name: 'Pricing', tag: 'Pricing', when: '7m ago' },
      { name: 'Fees', tag: 'Finance', when: '5m ago' },
      { name: 'Settlements', tag: 'Finance', when: '1h ago' },
      { name: 'Returns', tag: 'Sales', when: '11m ago' },
      { name: 'Promotions', tag: 'Marketing', when: '1h ago' },
    ],
    usage: { used: 32418, limit: 200000, window: '24h', resetsIn: '12h 24m' },
  },
  'shopify-admin': {
    connectedSince: 'Jul 18, 2026',
    connectedDays: '12 days',
    lastSyncAbsolute: 'Jul 30, 2026 10:40 AM',
    usage: { used: 8940, limit: 40000, window: '24h', resetsIn: '9h 05m' },
  },
  'meta-ads': {
    connectedSince: 'Jun 02, 2026',
    connectedDays: '58 days',
    lastSyncAbsolute: 'Jul 30, 2026 07:12 AM',
    usage: { used: 18220, limit: 50000, window: '24h', resetsIn: '4h 48m' },
  },
};

/** Sync-activity series for the chart, and what the dropdown can plot. */
export const SYNC_METRICS = ['Data freshness', 'Sync success rate', 'API usage'];
export const SYNC_DAYS = ['Jul 24', 'Jul 25', 'Jul 26', 'Jul 27', 'Jul 28', 'Jul 29', 'Jul 30'];
const SYNC_SERIES = {
  'Data freshness': [48, 62, 55, 68, 53, 72, 66, 74],
  'Sync success rate': [88, 92, 90, 95, 91, 97, 96, 99],
  'API usage': [22, 31, 27, 44, 38, 52, 47, 58],
};
export const syncSeries = (metric) => SYNC_SERIES[metric] || SYNC_SERIES[SYNC_METRICS[0]];

const numberFmt = (n) => n.toLocaleString('en-US');

/** Everything the Overview tab renders for one connector. */
export const connectorOverview = (connector) => {
  if (!connector) return null;
  const o = OVERVIEW_OVERRIDES[connector.id] || {};
  const isLive = connector.status !== 'available';
  const needsAttention = connector.status === 'attention';

  const usage = o.usage || { used: 4120, limit: 25000, window: '24h', resetsIn: '6h 10m' };
  const usagePct = Math.round((usage.used / usage.limit) * 100);

  /* A connector with no hand-written feed list still gets one, built from the
     lenses its row already declares. */
  const feeds =
    o.feeds ||
    connector.feeds.map((f, i) => ({
      name: f,
      tag: f,
      when: isLive ? ['2m ago', '7m ago', '15m ago', '1h ago'][i % 4] : '—',
    }));

  return {
    isLive,
    needsAttention,
    stats: [
      {
        key: 'status',
        label: 'Connection status',
        value: needsAttention ? 'Needs attention' : isLive ? 'Connected & healthy' : 'Not connected',
        sub: needsAttention ? connector.note : isLive ? 'All systems normal' : 'Connect to begin syncing',
        tone: needsAttention ? 'amber' : isLive ? 'emerald' : 'muted',
        icon: needsAttention ? 'fa-triangle-exclamation' : 'fa-circle-check',
      },
      {
        key: 'freshness',
        label: 'Data freshness',
        value: isLive ? (needsAttention ? '91.4%' : '99.2%') : '—',
        sub: isLive ? (needsAttention ? 'Degraded' : 'Excellent') : 'No data yet',
        tone: needsAttention ? 'amber' : 'emerald',
        big: true,
      },
      {
        key: 'last-sync',
        label: 'Last successful sync',
        value: isLive ? connector.lastSync : 'Never',
        sub: isLive ? o.lastSyncAbsolute || 'Jul 30, 2026 10:30 AM' : '—',
      },
      {
        key: 'since',
        label: 'Connected since',
        value: isLive ? o.connectedSince || 'Jul 21, 2026' : '—',
        sub: isLive ? o.connectedDays || '9 days' : '—',
      },
      {
        key: 'auth',
        label: 'Auth method',
        value: 'OAuth 2.0',
        sub: 'Auto refresh enabled',
      },
    ],
    feeds,
    feedsSummary: `${feeds.length} active feeds syncing to RCDP`,
    usage: {
      ...usage,
      pct: usagePct,
      usedLabel: numberFmt(usage.used),
      limitLabel: numberFmt(usage.limit),
      remainingLabel: numberFmt(usage.limit - usage.used),
      rateLabel: `${numberFmt(usage.limit)} calls / ${usage.window}`,
    },
  };
};

/** Feed tag colours, keyed by the lens the feed belongs to. */
export const FEED_TAG_TONES = {
  Sales: 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400',
  Margin: 'bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400',
  Inventory: 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400',
  Finance: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400',
  Catalog: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300',
  Pricing: 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400',
  Marketing: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400',
  Reports: 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400',
  Customers: 'bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400',
  Listings: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300',
  Ads: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400',
  Spend: 'bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400',
};

/* ── Right rail ── */

export const RAIL_QUICK_ACTIONS = [
  { key: 'activity', label: 'View activity', icon: 'fa-eye' },
  { key: 'reconnect', label: 'Reconnect', icon: 'fa-rotate' },
  { key: 'pause', label: 'Pause sync', icon: 'fa-circle-pause' },
  { key: 'disconnect', label: 'Disconnect', icon: 'fa-trash-can', danger: true },
];

/** Recent-activity feed for the rail. Derived from the connector's own feeds. */
export const railActivity = (connector) => {
  if (!connector || connector.status === 'available') {
    return [{ label: 'Not connected yet', when: '—', done: false }];
  }
  const o = OVERVIEW_OVERRIDES[connector.id];
  if (o?.feeds) {
    return [
      { label: `${o.feeds[2]?.name || 'Inventory'} feed synced`, when: '2 minutes ago', done: true },
      { label: `${o.feeds[0].name} feed synced`, when: '2 minutes ago', done: true },
      { label: `${o.feeds[1].name} updated`, when: '5 minutes ago', done: true },
      { label: `${o.feeds[3]?.name || 'Pricing'} feed synced`, when: '7 minutes ago', done: true },
      { label: `${o.feeds[4]?.name || 'Fees'} feed synced`, when: '15 minutes ago', done: true },
    ];
  }
  const times = ['2 minutes ago', '5 minutes ago', '12 minutes ago', '1 hour ago', '3 hours ago'];
  return connector.feeds
    .concat(['Token refresh', 'Backfill'])
    .slice(0, 5)
    .map((f, i) => ({ label: `${f} feed synced`, when: times[i], done: true }));
};

/* ── Onboarding wizard ── */

/** Step 1 — the connector being wired up, described in its own terms. */
export const chooseConnectorCard = (connector) => ({
  name: connector.name,
  categoryLabel: CATEGORY_BY_KEY[connector.category] || connector.category,
  badge: 'Recommended',
  description:
    connector.id === 'amazon-sp-api'
      ? 'Read orders, inventory, fees, settlements and more through Amazon Selling Partner API.'
      : `Read ${connector.feeds.join(', ').toLowerCase()} and more through the ${connector.name} API.`,
});

/** Step 2 — the assurances shown before handing the user to the provider. */
export const AUTHORIZE_PILLARS = [
  {
    key: 'secure',
    icon: 'fa-lock',
    title: 'Secure connection',
    body: 'OAuth 2.0 encryption keeps your data safe',
  },
  {
    key: 'least-privilege',
    icon: 'fa-key',
    title: 'Least-privilege access',
    body: 'You control exactly what Realify can access',
  },
  {
    key: 'revocable',
    icon: 'fa-rotate-left',
    title: 'Revocable anytime',
    body: 'Disconnect anytime from the provider or Realify',
  },
];

export const authorizeNextSteps = (connector) => [
  `You'll be redirected to ${providerName(connector)}`,
  `Sign in and approve Realify's access`,
  `We'll verify the connection and fetch your data`,
  `You'll choose what to read and write in the next step`,
];

/** The provider a connector authorises against, for the OAuth copy. */
export const providerName = (connector) =>
  connector.name.replace(/ (SP-API|Admin|Ads|Marketplace)$/i, '') || connector.name;

/** Step 3 — read scopes. `recommended` ones are pre-selected. */
const SCOPE_SETS = {
  'amazon-sp-api': [
    { key: 'orders', label: 'Orders', scope: 'orders:read', description: 'Read order and shipment information', recommended: true },
    { key: 'inventory', label: 'Inventory', scope: 'inventory:read', description: 'Read inventory levels and availability', recommended: true },
    { key: 'pricing', label: 'Pricing', scope: 'pricing:read', description: 'Read pricing, fees, and promotions', recommended: true },
    { key: 'catalog', label: 'Catalog', scope: 'catalog:read', description: 'Read product and catalog information', recommended: true },
    { key: 'finance', label: 'Finance', scope: 'finance:read', description: 'Read settlements, fees and financial reports', recommended: true },
    { key: 'feedback', label: 'Customer feedback', scope: 'feedback:read', description: 'Read customer reviews and feedback', recommended: false },
  ],
};

export const readScopes = (connector) =>
  SCOPE_SETS[connector.id] ||
  connector.feeds.map((f) => ({
    key: f.toLowerCase(),
    label: f,
    scope: `${f.toLowerCase().replace(/[^a-z0-9]/g, '')}:read`,
    description: `Read ${f.toLowerCase()} data from your ${connector.name} account`,
    recommended: true,
  }));

/** Step 3 — write permissions, behind the second segment. */
export const writePermissions = (connector) => [
  { key: 'pricing-write', label: 'Update pricing', scope: 'pricing:write', description: `Change prices on ${connector.name} within your guardrails`, recommended: false },
  { key: 'inventory-write', label: 'Update inventory', scope: 'inventory:write', description: 'Adjust quantities and restock dates', recommended: false },
  { key: 'listing-write', label: 'Update listings', scope: 'listings:write', description: 'Edit titles, bullets and imagery', recommended: false },
];

export const SCOPE_SEGMENTS = [
  { key: 'read', label: 'Read scopes', sub: 'Data Realify can read' },
  { key: 'write', label: 'Write permissions', sub: 'Actions Realify can take' },
];

/** Step 4 — consent. Each block is a claim plus the guarantees behind it. */
export const CONSENT_BLOCKS = [
  {
    key: 'handling',
    icon: 'fa-database',
    title: 'Data handling',
    body: "We only read the data you've allowed and store it in Realify's secure, encrypted environment.",
    points: ['Encrypted in transit and at rest', 'Stored in your tenant', 'Never sold or shared'],
  },
  {
    key: 'usage',
    icon: 'fa-shield-halved',
    title: 'Data usage',
    body: "Your data is used to power Realify's analytics, insights, and automation within your workspace.",
    points: ['Used for insights and recommendations', 'Used for automation you approve', 'No training of third-party models'],
  },
  {
    key: 'control',
    icon: 'fa-sliders',
    title: 'Your control',
    body: 'You can revoke access, adjust scopes, or delete your data at any time.',
    points: ['Revoke anytime', 'Adjust scopes anytime', 'Request data deletion'],
  },
];

/** Step 5 — what happens after the connection lands. */
export const GO_LIVE_NEXT = [
  {
    key: 'sync',
    icon: 'fa-rotate',
    title: 'Initial sync in progress',
    body: "We're fetching your data. This may take a few minutes.",
    status: 'In progress',
    tone: 'active',
  },
  {
    key: 'data',
    icon: 'fa-clock',
    title: 'Data will be available soon',
    body: "You'll be able to explore your data and run actions once the sync is complete.",
    status: 'Upcoming',
    tone: 'idle',
  },
  {
    key: 'monitor',
    icon: 'fa-desktop',
    title: 'Monitor your integration',
    body: 'Check activity and sync status anytime in the Activity tab.',
    status: 'Upcoming',
    tone: 'idle',
  },
];

/* ── Scopes & Permissions tab ── */

/** The access levels a scope can be granted at, and how each reads. */
export const PERMISSION_LEVELS = [
  {
    key: 'read',
    label: 'Read',
    body: 'View data',
    tone: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400',
  },
  {
    key: 'read-write',
    label: 'Read / Write',
    body: 'View and edit data',
    tone: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400',
  },
  {
    key: 'full',
    label: 'Full Access',
    body: 'View, edit and take action',
    tone: 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400',
  },
];

export const ACCESS_LEVEL_BY_KEY = PERMISSION_LEVELS.reduce(
  (acc, l) => ({ ...acc, [l.key]: l }),
  {}
);

/** Access-type filter options above the scope grid. */
export const ACCESS_FILTERS = [
  { key: 'all', label: 'All' },
  ...PERMISSION_LEVELS.map((l) => ({ key: l.key, label: l.label })),
];

/**
 * Granted scopes per connector.
 *
 * `state` is what the counters read: granted / pending / denied. Anything not
 * written out by hand derives a read-only set from the connector's own feeds, so
 * every connector's Scopes tab is populated.
 */
const SCOPE_GRANTS = {
  'amazon-sp-api': [
    { key: 'orders', label: 'Orders', description: 'View orders, order items, shipments and invoices', access: 'read', state: 'granted', authorized: 'May 12, 2025 • 10:24 AM' },
    { key: 'inventory', label: 'Inventory', description: 'View and manage inventory and listings', access: 'read-write', state: 'granted', authorized: 'May 12, 2025 • 10:24 AM' },
    { key: 'feeds', label: 'Feeds', description: 'Create, read and manage feeds', access: 'read-write', state: 'granted', authorized: 'May 12, 2025 • 10:24 AM' },
    { key: 'finances', label: 'Finances', description: 'View financial events, settlements and fees', access: 'read', state: 'granted', authorized: 'May 12, 2025 • 10:24 AM' },
    { key: 'catalog', label: 'Catalog', description: 'View product listings and catalog attributes', access: 'read', state: 'granted', authorized: 'May 12, 2025 • 10:24 AM' },
    { key: 'reports', label: 'Reports', description: 'Request and download business reports', access: 'read', state: 'granted', authorized: 'May 12, 2025 • 10:24 AM' },
  ],
  'meta-ads': [
    { key: 'ads-read', label: 'Ads', description: 'View campaigns, ad sets and creative', access: 'read', state: 'granted', authorized: 'Jun 02, 2026 • 09:10 AM' },
    { key: 'insights', label: 'Insights', description: 'View spend, impressions and conversions', access: 'read', state: 'granted', authorized: 'Jun 02, 2026 • 09:10 AM' },
    { key: 'ads-manage', label: 'Ad management', description: 'Create and pause campaigns and ad sets', access: 'read-write', state: 'pending', authorized: '—' },
    { key: 'business', label: 'Business assets', description: 'Read pages, pixels and product catalogs', access: 'read', state: 'denied', authorized: '—' },
  ],
};

export const connectorScopes = (connector) => {
  if (!connector) return [];
  return (
    SCOPE_GRANTS[connector.id] ||
    connector.feeds.map((f) => ({
      key: f.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      label: f,
      description: `View ${f.toLowerCase()} data from your ${connector.name} account`,
      access: 'read',
      state: connector.status === 'available' ? 'pending' : 'granted',
      authorized: connector.status === 'available' ? '—' : 'May 12, 2025 • 10:24 AM',
    }))
  );
};

/**
 * The four counters above the grid.
 *
 * Every figure is counted from the scope list, so the headline "N total" and the
 * number of cards below it cannot disagree.
 */
export const scopeSummary = (scopes = []) => {
  const total = scopes.length || 1;
  const count = (state) => scopes.filter((s) => s.state === state).length;
  const pct = (n) => Math.round((n / total) * 100);

  return [
    {
      key: 'total',
      value: scopes.length,
      label: 'Total scopes',
      foot: 'Active',
      barPct: 100,
      bar: 'bg-indigo-600',
    },
    {
      key: 'granted',
      value: count('granted'),
      label: 'Granted',
      foot: `${pct(count('granted'))}% enabled`,
      barPct: pct(count('granted')),
      bar: 'bg-emerald-500',
    },
    {
      key: 'pending',
      value: count('pending'),
      label: 'Pending',
      foot: `${pct(count('pending'))}%`,
      barPct: pct(count('pending')),
      bar: 'bg-amber-500',
    },
    {
      key: 'denied',
      value: count('denied'),
      label: 'Denied',
      foot: `${pct(count('denied'))}%`,
      barPct: pct(count('denied')),
      bar: 'bg-rose-500',
    },
  ];
};

/* ── Activity tab ── */

/** Outcome of one logged activity. Drives the dot, the pill and the icon. */
export const ACTIVITY_STATUS = {
  success: {
    key: 'success',
    label: 'Success',
    chip: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400',
    dot: 'bg-emerald-500',
    icon: 'fa-check',
    iconTone: 'text-emerald-500',
    cardChip: 'Completed',
  },
  failed: {
    key: 'failed',
    label: 'Failed',
    chip: 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400',
    dot: 'bg-rose-500',
    icon: 'fa-xmark',
    iconTone: 'text-rose-500',
    cardChip: 'Failed',
  },
  running: {
    key: 'running',
    label: 'In progress',
    chip: 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400',
    dot: 'bg-blue-500',
    icon: 'fa-rotate',
    iconTone: 'text-blue-500',
    cardChip: 'In progress',
  },
};

export const ACTIVITY_TYPES = ['All types', 'Sync', 'Update', 'Auth', 'Export'];
export const ACTIVITY_STATUS_FILTERS = ['All status', 'Success', 'Failed', 'In progress'];

/**
 * The activity log for a connector.
 *
 * `feed` is what the "All feeds" filter narrows on, and the totals above the
 * table are counted from this list rather than stated, so the headline figures
 * and the rows can never disagree.
 */
const ACTIVITY_LOG = {
  'amazon-sp-api': [
    { id: 'a1', label: 'Sales data sync', feed: 'Sales', status: 'success', type: 'Sync', date: 'May 12, 2025', time: '10:24 AM', duration: '1m 24s' },
    { id: 'a2', label: 'Inventory data sync', feed: 'Inventory', status: 'success', type: 'Sync', date: 'May 12, 2025', time: '10:23 AM', duration: '58s' },
    { id: 'a3', label: 'Reports data sync', feed: 'Reports', status: 'failed', type: 'Sync', date: 'May 12, 2025', time: '10:18 AM', duration: '—' },
    { id: 'a4', label: 'Feeds metadata refresh', feed: 'All', status: 'success', type: 'Update', date: 'May 12, 2025', time: '10:15 AM', duration: '32s' },
    { id: 'a5', label: 'Orders data sync', feed: 'Orders', status: 'running', type: 'Sync', date: 'May 12, 2025', time: '10:12 AM', duration: '45s' },
    { id: 'a6', label: 'Token refreshed', feed: 'All', status: 'success', type: 'Auth', date: 'May 12, 2025', time: '09:58 AM', duration: '2s' },
    { id: 'a7', label: 'Settlement report export', feed: 'Finance', status: 'success', type: 'Export', date: 'May 12, 2025', time: '09:40 AM', duration: '1m 06s' },
    { id: 'a8', label: 'Catalog data sync', feed: 'Catalog', status: 'success', type: 'Sync', date: 'May 12, 2025', time: '09:22 AM', duration: '2m 11s' },
    { id: 'a9', label: 'Pricing data sync', feed: 'Pricing', status: 'success', type: 'Sync', date: 'May 12, 2025', time: '09:04 AM', duration: '41s' },
    { id: 'a10', label: 'Returns data sync', feed: 'Sales', status: 'failed', type: 'Sync', date: 'May 12, 2025', time: '08:47 AM', duration: '—' },
  ],
};

/**
 * Lifetime totals the tiles quote — a real log is longer than the page shown.
 *
 * `failed` and `running` are stated and `successful` is the remainder, so the
 * three always sum to `total`. Scaling the visible page's failure rate up to the
 * lifetime count instead produced figures that did not add up.
 */
const ACTIVITY_TOTALS = {
  'amazon-sp-api': { total: 128, failed: 6, running: 2 },
};

export const connectorActivity = (connector) => {
  if (!connector) return [];
  if (ACTIVITY_LOG[connector.id]) return ACTIVITY_LOG[connector.id];
  if (connector.status === 'available') return [];

  /* Derived log so every connected connector has a populated Activity tab. */
  const times = ['10:24 AM', '10:12 AM', '09:48 AM', '09:20 AM', '08:55 AM'];
  return connector.feeds.concat(['Token refresh', 'Backfill']).map((feed, i) => ({
    id: `${connector.id}-${i}`,
    label: `${feed} ${feed.includes('refresh') || feed === 'Backfill' ? 'completed' : 'data sync'}`,
    feed: feed === 'Backfill' || feed === 'Token refresh' ? 'All' : feed,
    status: i === 2 ? 'running' : 'success',
    type: feed === 'Token refresh' ? 'Auth' : 'Sync',
    date: 'May 12, 2025',
    time: times[i % times.length],
    duration: i === 2 ? '45s' : `${20 + i * 9}s`,
  }));
};

/**
 * The four tiles above the log.
 *
 * `total` is the real lifetime count; the success / failure split is scaled from
 * the visible page so the four figures always add up to it.
 */
export const activitySummary = (connector, rows = []) => {
  const count = (s) => rows.filter((r) => r.status === s).length;

  /* Stated totals where we have them, otherwise count the log we do have. */
  const stated = ACTIVITY_TOTALS[connector?.id];
  const total = stated?.total ?? rows.length;
  const failed = stated?.failed ?? count('failed');
  const running = stated?.running ?? count('running');
  const successful = Math.max(0, total - failed - running);

  return [
    { key: 'total', value: total, label: 'Total activities', delta: '18%', dir: 'up', tone: 'emerald' },
    { key: 'successful', value: successful, label: 'Successful', delta: '20%', dir: 'up', tone: 'emerald' },
    { key: 'failed', value: failed, label: 'Failed', delta: '14%', dir: 'down', tone: 'rose' },
    { key: 'running', value: running, label: 'In progress', flat: 'No change vs last 7 days' },
  ];
};

/** Feeds present in a log, for the "All feeds" filter. */
export const activityFeeds = (rows = []) => [
  'All feeds',
  ...Array.from(new Set(rows.map((r) => r.feed))).sort(),
];

/** What the rail's "Upcoming" card announces. */
export const nextScheduledSync = (connector) => ({
  label: `${connector?.feeds?.[connector.feeds.length - 1] || 'Inventory'} data sync`,
  when: 'In 13 minutes',
});

/* ── Data tab ── */

export const DATASET_STATUS = {
  healthy: {
    key: 'healthy',
    label: 'Healthy',
    dot: 'bg-emerald-500',
    text: 'text-emerald-600 dark:text-emerald-400',
  },
  stale: {
    key: 'stale',
    label: 'Stale',
    dot: 'bg-amber-500',
    text: 'text-amber-600 dark:text-amber-400',
  },
  degraded: {
    key: 'degraded',
    label: 'Degraded',
    dot: 'bg-rose-500',
    text: 'text-rose-600 dark:text-rose-400',
  },
};

export const DATASET_STATUS_FILTERS = ['All status', 'Healthy', 'Stale', 'Degraded'];

/**
 * The datasets a connector is syncing.
 *
 * Written out for the connectors worth showing in full; everything else is
 * derived from its own feeds below, so all 18 open a populated table.
 */
const DATASET_OVERRIDES = {
  'amazon-sp-api': [
    { name: 'Sales Orders', feed: 'Sales', records: 320642, when: '2 min ago', at: 'May 12, 2025, 10:24 AM', status: 'healthy' },
    { name: 'Order Items', feed: 'Sales', records: 1128934, when: '2 min ago', at: 'May 12, 2025, 10:24 AM', status: 'healthy' },
    { name: 'Inventory', feed: 'Inventory', records: 45281, when: '3 min ago', at: 'May 12, 2025, 10:23 AM', status: 'healthy' },
    { name: 'FBA Inventory', feed: 'Inventory', records: 28743, when: '3 min ago', at: 'May 12, 2025, 10:23 AM', status: 'healthy' },
    { name: 'Financial Events', feed: 'Finance', records: 12652, when: '8 min ago', at: 'May 12, 2025, 10:18 AM', status: 'healthy' },
    { name: 'Returns', feed: 'Sales', records: 8142, when: '8 min ago', at: 'May 12, 2025, 10:18 AM', status: 'healthy' },
    { name: 'Performance Metrics', feed: 'Reports', records: 1254, when: '15 min ago', at: 'May 12, 2025, 10:11 AM', status: 'healthy' },
    { name: 'Fee Estimates', feed: 'Finance', records: 9832, when: '15 min ago', at: 'May 12, 2025, 10:11 AM', status: 'healthy' },
  ],
  'shopify-admin': [
    { name: 'Orders', feed: 'Sales', records: 214508, when: '4 min ago', at: 'May 12, 2025, 10:22 AM', status: 'healthy' },
    { name: 'Line Items', feed: 'Sales', records: 642190, when: '4 min ago', at: 'May 12, 2025, 10:22 AM', status: 'healthy' },
    { name: 'Customers', feed: 'Customers', records: 88431, when: '6 min ago', at: 'May 12, 2025, 10:20 AM', status: 'healthy' },
    { name: 'Products', feed: 'Catalog', records: 12904, when: '6 min ago', at: 'May 12, 2025, 10:20 AM', status: 'healthy' },
    { name: 'Inventory Levels', feed: 'Inventory', records: 31782, when: '22 min ago', at: 'May 12, 2025, 10:04 AM', status: 'stale' },
    { name: 'Refunds', feed: 'Finance', records: 4128, when: '9 min ago', at: 'May 12, 2025, 10:17 AM', status: 'healthy' },
  ],
};

/**
 * Records and quality, stated per connector.
 *
 * `records` is the 30-day volume the tiles quote, which is deliberately not the
 * sum of the datasets' lifetime counts — different windows. `quality` drives both
 * the headline percentage and the valid / invalid split, so the health card can
 * never show two figures that fail to add up to the total.
 */
const DATA_TOTALS = {
  'amazon-sp-api': { records: 1240000, quality: 98.6 },
  'shopify-admin': { records: 864000, quality: 99.1 },
};

export const connectorDatasets = (connector) => {
  const stated = DATASET_OVERRIDES[connector?.id];
  if (stated) return stated.map((d) => ({ ...d, key: d.name }));

  /* Derived: one dataset per feed the connector declares, so the table is never
     empty for a connector nobody has written rows for. */
  const feeds = connector?.feeds || [];
  const live = connector?.status !== 'available';
  return feeds.map((feed, i) => ({
    key: feed,
    name: `${feed} records`,
    feed,
    records: [48210, 22184, 9765, 5412][i % 4],
    when: live ? connector.lastSync || `${(i + 1) * 4} min ago` : '—',
    at: live ? 'May 12, 2025, 10:20 AM' : 'Never',
    status: live ? (i === feeds.length - 1 && connector.status === 'attention' ? 'degraded' : 'healthy') : 'stale',
  }));
};

/** Compact record counts — 1.24M / 45.3K / 812. */
export const formatRecords = (n) => {
  if (!Number.isFinite(n)) return '—';
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e4) return `${(n / 1e3).toFixed(1)}K`;
  return n.toLocaleString('en-US');
};

/** Feeds present in a dataset list, for the rail's Type filter. */
export const datasetTypes = (rows = []) => [
  'All types',
  ...Array.from(new Set(rows.map((r) => r.feed))).sort(),
];

/** The four tiles above the dataset table. */
export const dataSummary = (connector, rows = []) => {
  const totals = DATA_TOTALS[connector?.id];
  const records = totals?.records ?? rows.reduce((sum, r) => sum + r.records, 0);
  const quality = totals?.quality ?? (connector?.status === 'attention' ? 91.4 : 99.2);
  const feedCount = new Set(rows.map((r) => r.feed)).size;
  const freshest = rows[0];

  return [
    {
      key: 'datasets',
      label: 'Total datasets',
      value: String(rows.length),
      sub: `Across ${feedCount} feed${feedCount === 1 ? '' : 's'}`,
    },
    {
      key: 'records',
      label: 'Total records',
      value: formatRecords(records),
      sub: 'Last 30 days',
    },
    {
      key: 'received',
      label: 'Last data received',
      value: freshest?.when || '—',
      sub: freshest?.at || 'Never',
    },
    {
      key: 'quality',
      label: 'Data quality',
      value: `${quality}%`,
      sub: 'Valid records',
    },
  ];
};

/**
 * The rail's Data health card.
 *
 * Valid is derived from the quality percentage and invalid is the remainder, so
 * the two rows always sum to the stated total instead of being three independent
 * numbers that can drift apart.
 */
export const dataHealth = (connector, rows = []) => {
  const totals = DATA_TOTALS[connector?.id];
  const records = totals?.records ?? rows.reduce((sum, r) => sum + r.records, 0);
  const quality = totals?.quality ?? (connector?.status === 'attention' ? 91.4 : 99.2);

  const valid = Math.round((records * quality) / 100);
  const invalid = records - valid;

  return {
    quality,
    validLabel: `${formatRecords(valid)} (${quality}%)`,
    invalidLabel: `${formatRecords(invalid)} (${(100 - quality).toFixed(1)}%)`,
  };
};

/* ── Settings tab ── */

const SETTINGS_OVERRIDES = {
  'amazon-sp-api': { connectedOn: 'May 6, 2025, 10:24 AM', connectedBy: 'Nikhil Verma', retention: '90 days' },
  'shopify-admin': { connectedOn: 'May 2, 2025, 09:10 AM', connectedBy: 'Rohit Sharma', retention: '180 days' },
};

export const SYNC_FREQUENCIES = [
  'Every 5 minutes',
  'Every 15 minutes',
  'Every 30 minutes',
  'Hourly',
  'Daily',
];

export const TIME_ZONES = [
  '(GMT +05:30) Asia/Kolkata',
  '(GMT +00:00) UTC',
  '(GMT -05:00) America/New_York',
  '(GMT -08:00) America/Los_Angeles',
  '(GMT +01:00) Europe/London',
];

export const RETENTION_PERIODS = ['30 days', '90 days', '180 days', '365 days', 'Unlimited'];
export const RATE_LIMIT_MODES = ['Retry automatically', 'Retry with backoff', 'Fail fast'];
export const PARTIAL_DATA_MODES = ['Store available data', 'Discard partial batches'];

/**
 * The Settings tab, section by section.
 *
 * Every field declares its own control (`select` with options, or `toggle`), so
 * the tab renders and edits them generically — adding a setting is one entry
 * here rather than new markup. Values are the defaults the section opens with;
 * the tab owns the edited copy.
 */
export const connectorSettings = (connector) => {
  const o = SETTINGS_OVERRIDES[connector?.id] || {};

  return [
    {
      key: 'sync',
      icon: 'fa-rotate',
      title: 'Sync settings',
      subtitle: `Control how often data is synced from ${connector?.name}.`,
      fields: [
        { key: 'frequency', label: 'Sync frequency', type: 'select', value: 'Every 15 minutes', options: SYNC_FREQUENCIES },
        { key: 'timezone', label: 'Time zone', type: 'select', value: TIME_ZONES[0], options: TIME_ZONES },
        { key: 'autoSync', label: 'Auto sync', type: 'toggle', value: true },
      ],
    },
    {
      key: 'retention',
      icon: 'fa-calendar-days',
      title: 'Data retention',
      subtitle: 'Manage how long your data is stored.',
      fields: [
        { key: 'period', label: 'Data retention period', type: 'select', value: o.retention || '90 days', options: RETENTION_PERIODS },
        { key: 'historical', label: 'Historical data', type: 'toggle', value: true, onLabel: 'Enabled', offLabel: 'Disabled' },
        { key: 'purge', label: 'Delete data after retention', type: 'toggle', value: false, onLabel: 'Enabled', offLabel: 'Disabled' },
      ],
    },
    {
      key: 'alerts',
      icon: 'fa-bell',
      title: 'Alert settings',
      subtitle: 'Configure notifications for sync and data issues.',
      fields: [
        { key: 'syncFailure', label: 'Sync failure alerts', type: 'toggle', value: true },
        { key: 'dataIssue', label: 'Data issue alerts', type: 'toggle', value: true },
        { key: 'recipients', label: 'Recipients', type: 'select', value: '2 users', options: ['1 user', '2 users', '5 users', 'Everyone'] },
      ],
    },
    {
      key: 'advanced',
      icon: 'fa-sliders',
      title: 'Advanced settings',
      subtitle: 'Configure advanced options for data handling and API usage.',
      fields: [
        { key: 'rateLimit', label: 'Rate limit handling', type: 'select', value: RATE_LIMIT_MODES[0], options: RATE_LIMIT_MODES },
        { key: 'partial', label: 'Partial data handling', type: 'select', value: PARTIAL_DATA_MODES[0], options: PARTIAL_DATA_MODES },
        { key: 'scopeValidation', label: 'API scope validation', type: 'toggle', value: true, onLabel: 'Enabled', offLabel: 'Disabled' },
      ],
    },
  ];
};

/** The rail beside Settings. */
export const settingsRail = (connector) => {
  const o = SETTINGS_OVERRIDES[connector?.id] || {};
  const needsAttention = connector?.status === 'attention';
  const isLive = connector?.status !== 'available';

  return {
    about: {
      body: `${connector?.name} provides real-time data from your ${providerName(connector)} seller account.`,
      facts: [
        { key: 'on', icon: 'fa-regular fa-calendar', label: 'Connected on', value: isLive ? o.connectedOn || 'May 6, 2025, 10:24 AM' : 'Not connected' },
        { key: 'by', icon: 'fa-regular fa-user', label: 'Connected by', value: isLive ? o.connectedBy || 'Rohit Sharma' : '—' },
      ],
    },
    help: [
      { key: 'guide', icon: 'fa-book-open', label: 'View integration guide' },
      { key: 'docs', icon: 'fa-file-lines', label: `${connector?.name} docs` },
      { key: 'support', icon: 'fa-headset', label: 'Contact support' },
    ],
    quality: {
      tone: needsAttention ? 'amber' : 'emerald',
      label: needsAttention ? 'Degraded' : 'Healthy',
      body: needsAttention
        ? connector?.note || 'Some feeds are behind. Reauthenticate to restore full sync.'
        : 'All systems are operational and data is syncing as expected.',
    },
  };
};
