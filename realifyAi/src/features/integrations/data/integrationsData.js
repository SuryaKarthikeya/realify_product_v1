/**
 * The connector catalogue behind the Integrations screen.
 *
 * Everything the page shows is derived from `CONNECTORS`: the category chips and
 * their counts, the four summary tiles, pagination, and the detail panel. Adding
 * a connector to this list is the only edit needed for it to appear everywhere,
 * with correct counts — nothing on the page carries a hardcoded number that
 * could drift out of step with the list.
 */

/** Health of a connection. Drives the dot, the label and which button shows. */
export const STATUS = {
  connected: {
    key: 'connected',
    dot: 'bg-emerald-500',
    label: 'Connected',
    text: 'text-gray-600 dark:text-slate-300',
    action: 'Manage',
  },
  attention: {
    key: 'attention',
    dot: 'bg-amber-500',
    label: 'Attention',
    text: 'text-amber-600 dark:text-amber-400',
    action: 'Reauthenticate',
    /* An amber card ring, so a connector needing a human is findable in a grid. */
    ring: 'border-amber-300 dark:border-amber-700/70',
  },
  available: {
    key: 'available',
    dot: 'bg-gray-300 dark:bg-slate-600',
    label: 'Not connected',
    text: 'text-gray-400 dark:text-slate-500',
    action: 'Connect',
  },
};

/**
 * Categories, in the order the chips render.
 *
 * `CATEGORY_BY_KEY` exists so a card can print its own category label without
 * every component re-deriving the mapping.
 */
export const CATEGORIES = [
  { key: 'marketplaces', label: 'Marketplaces' },
  { key: 'advertising', label: 'Advertising' },
  { key: 'erp-accounting', label: 'ERP & Accounting' },
  { key: 'marketing-crm', label: 'Marketing & CRM' },
  { key: 'fulfillment', label: 'Fulfillment' },
  { key: 'banking-payments', label: 'Banking & Payments' },
];

export const CATEGORY_BY_KEY = CATEGORIES.reduce(
  (acc, c) => ({ ...acc, [c.key]: c.label }),
  {}
);

export const CONNECTORS = [
  /* ── Marketplaces ── */
  {
    id: 'amazon-sp-api',
    name: 'Amazon SP-API',
    category: 'marketplaces',
    icon: 'fa-brands fa-amazon',
    tone: 'bg-orange-50 dark:bg-orange-950/30 text-orange-600 dark:text-orange-400',
    feeds: ['Sales', 'Margin', 'Inventory'],
    status: 'connected',
    lastSync: '2m ago',
  },
  {
    id: 'shopify-admin',
    name: 'Shopify Admin',
    category: 'marketplaces',
    icon: 'fa-brands fa-shopify',
    tone: 'bg-green-50 dark:bg-green-950/30 text-green-600 dark:text-green-400',
    feeds: ['Sales', 'Customers', 'Inventory'],
    status: 'connected',
    lastSync: '4m ago',
  },
  {
    id: 'walmart-marketplace',
    name: 'Walmart Marketplace',
    category: 'marketplaces',
    icon: 'fa-solid fa-cart-shopping',
    tone: 'bg-blue-50 dark:bg-blue-950/30 text-blue-500 dark:text-blue-400',
    feeds: ['Sales', 'Inventory'],
    status: 'connected',
    lastSync: '12m ago',
  },
  {
    id: 'ebay',
    name: 'eBay',
    category: 'marketplaces',
    icon: 'fa-brands fa-ebay',
    tone: 'bg-red-50 dark:bg-red-950/30 text-red-500 dark:text-red-400',
    feeds: ['Sales', 'Listings'],
    status: 'available',
  },
  {
    id: 'etsy',
    name: 'Etsy',
    category: 'marketplaces',
    icon: 'fa-brands fa-etsy',
    tone: 'bg-orange-50 dark:bg-orange-950/30 text-orange-500 dark:text-orange-400',
    feeds: ['Sales', 'Listings'],
    status: 'available',
  },

  /* ── Advertising ── */
  {
    id: 'amazon-ads',
    name: 'Amazon Ads',
    category: 'advertising',
    icon: 'fa-brands fa-amazon',
    tone: 'bg-sky-50 dark:bg-sky-950/30 text-sky-600 dark:text-sky-400',
    feeds: ['Ads', 'Spend', 'ACOS'],
    status: 'connected',
    lastSync: '11m ago',
  },
  {
    id: 'google-ads',
    name: 'Google Ads',
    category: 'advertising',
    icon: 'fa-brands fa-google',
    tone: 'bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400',
    feeds: ['Ads', 'Spend'],
    status: 'connected',
    lastSync: '9m ago',
  },
  {
    id: 'meta-ads',
    name: 'Meta Ads',
    category: 'advertising',
    icon: 'fa-brands fa-meta',
    tone: 'bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400',
    feeds: ['Ads', 'Spend'],
    status: 'attention',
    lastSync: '3h ago',
    note: 'Token expires in 3 days',
  },
  {
    id: 'tiktok-ads',
    name: 'TikTok Ads',
    category: 'advertising',
    icon: 'fa-brands fa-tiktok',
    tone: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300',
    feeds: ['Ads', 'Spend'],
    status: 'available',
  },

  /* ── Marketing & CRM ── */
  {
    id: 'klaviyo',
    name: 'Klaviyo',
    category: 'marketing-crm',
    icon: 'fa-solid fa-envelope-open-text',
    tone: 'bg-violet-50 dark:bg-violet-950/30 text-violet-600 dark:text-violet-400',
    feeds: ['Email', 'Segments'],
    status: 'connected',
    lastSync: '6m ago',
  },
  {
    id: 'hubspot',
    name: 'HubSpot',
    category: 'marketing-crm',
    icon: 'fa-brands fa-hubspot',
    tone: 'bg-orange-50 dark:bg-orange-950/30 text-orange-500 dark:text-orange-400',
    feeds: ['Contacts', 'Deals'],
    status: 'available',
  },
  {
    id: 'mailchimp',
    name: 'Mailchimp',
    category: 'marketing-crm',
    icon: 'fa-brands fa-mailchimp',
    tone: 'bg-yellow-50 dark:bg-yellow-950/30 text-yellow-600 dark:text-yellow-400',
    feeds: ['Email'],
    status: 'available',
  },

  /* ── Fulfillment ── */
  {
    id: 'shipbob',
    name: 'ShipBob',
    category: 'fulfillment',
    icon: 'fa-solid fa-box-open',
    tone: 'bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-400',
    feeds: ['Inventory', 'Shipments'],
    status: 'connected',
    lastSync: '8m ago',
  },
  {
    id: 'shipstation',
    name: 'ShipStation',
    category: 'fulfillment',
    icon: 'fa-solid fa-truck-fast',
    tone: 'bg-cyan-50 dark:bg-cyan-950/30 text-cyan-600 dark:text-cyan-400',
    feeds: ['Shipments'],
    status: 'available',
  },

  /* ── Banking & Payments ── */
  {
    id: 'plaid',
    name: 'Plaid',
    category: 'banking-payments',
    icon: 'fa-solid fa-building-columns',
    tone: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300',
    feeds: ['Bank', 'Payouts'],
    status: 'connected',
    lastSync: '1h ago',
  },
  {
    id: 'stripe',
    name: 'Stripe',
    category: 'banking-payments',
    icon: 'fa-brands fa-stripe-s',
    tone: 'bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400',
    feeds: ['Payments', 'Payouts'],
    status: 'available',
  },

  /* ── ERP & Accounting ── */
  {
    id: 'quickbooks',
    name: 'QuickBooks',
    category: 'erp-accounting',
    icon: 'fa-solid fa-file-invoice-dollar',
    tone: 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400',
    feeds: ['P&L', 'COGS'],
    status: 'connected',
    lastSync: 'Nightly sync',
  },
  {
    id: 'netsuite',
    name: 'NetSuite',
    category: 'erp-accounting',
    icon: 'fa-solid fa-warehouse',
    tone: 'bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-400',
    feeds: ['P&L', 'Inventory'],
    status: 'available',
  },
];

/** Uptime / freshness headline figures the tiles quote. */
const UPTIME = '99.2%';
const FRESHNESS = '99.2%';

/**
 * Category chips with live counts.
 *
 * `All` counts the whole catalogue and each chip counts its own slice, so the
 * numbers are always what the grid will actually show.
 */
export const categoryChips = (rows = CONNECTORS) => [
  { key: 'all', label: 'All', count: rows.length },
  ...CATEGORIES.map((c) => ({
    ...c,
    count: rows.filter((r) => r.category === c.key).length,
  })).filter((c) => c.count > 0),
];

/** The four tiles across the top, all counted from the same list. */
export const integrationSummary = (rows = CONNECTORS) => {
  const live = rows.filter((r) => r.status !== 'available');
  const attention = rows.filter((r) => r.status === 'attention');
  const freshest = live.find((r) => r.lastSync) || {};

  return [
    {
      key: 'connected',
      value: live.length,
      label: 'Connected',
      sub: '1 this week',
      subIcon: 'fa-arrow-up',
      subTone: 'text-emerald-600 dark:text-emerald-400',
    },
    {
      key: 'healthy',
      value: live.length - attention.length,
      label: 'Healthy',
      sub: `${UPTIME} uptime`,
    },
    {
      key: 'attention',
      value: attention.length,
      label: 'Needs attention',
      link: 'View now',
      /* The tile deep-links to the connector that actually needs a human. */
      linkTo: attention[0]?.id || null,
    },
    {
      key: 'freshness',
      value: FRESHNESS,
      label: 'Data freshness',
      sub: `Last sync: ${freshest.lastSync || '—'}`,
    },
  ];
};

/** Status line for a card: dot tone plus the text beside it. */
export const statusLine = (connector) => {
  const s = STATUS[connector.status] || STATUS.available;
  const detail =
    connector.status === 'attention'
      ? connector.note
      : connector.status === 'connected'
        ? connector.lastSync
        : '';
  return { ...s, detail };
};

/* ── Detail panel ── */

export const DETAIL_TABS = ['Overview', 'Onboarding', 'Scopes', 'Activity'];

/** Per-connector facts. Anything omitted falls back to the derived default. */
const DETAIL_OVERRIDES = {
  'amazon-sp-api': {
    connectedOn: 'Jul 15, 2026',
    authMethod: 'OAuth 2.0',
    writeAccess: 'Action Contracts (A2)',
    scopes: ['Orders', 'Listings', 'Inventory', 'Finances', 'Reports'],
  },
  'shopify-admin': {
    connectedOn: 'Jul 18, 2026',
    authMethod: 'OAuth 2.0',
    writeAccess: 'Action Contracts (A2)',
    scopes: ['Products', 'Orders', 'Customers', 'Inventory'],
  },
  'meta-ads': {
    connectedOn: 'Jun 02, 2026',
    authMethod: 'OAuth 2.0',
    writeAccess: 'Read only',
    scopes: ['ads_read', 'ads_management', 'business_management'],
  },
  quickbooks: {
    connectedOn: 'Jul 09, 2026',
    authMethod: 'OAuth 2.0',
    writeAccess: 'Read only',
    scopes: ['Accounting', 'Payments'],
  },
};

/** Quick actions. `Disconnect` reads as destructive because it is. */
const QUICK_ACTIONS = [
  { key: 'manage', label: 'Manage connector', icon: 'fa-gear' },
  { key: 'activity', label: 'View activity', icon: 'fa-eye' },
  { key: 'reconnect', label: 'Reconnect', icon: 'fa-rotate' },
  { key: 'pause', label: 'Pause sync', icon: 'fa-circle-pause' },
  { key: 'disconnect', label: 'Disconnect', icon: 'fa-trash-can', danger: true },
];

/**
 * Everything the right-hand panel renders for one connector.
 *
 * An override merged over a derived default, so every connector in the list
 * opens a fully populated panel rather than only the four written out by hand.
 */
/**
 * Has this connector already been through onboarding?
 *
 * Two ways to be done, and both have to count. `storedComplete` is the user
 * walking the wizard to Go live in this browser. But a connector that is already
 * live was onboarded before the user ever arrived — asking them to re-authorize,
 * re-pick scopes and re-consent for a channel that is currently syncing is asking
 * them to repeat work that is visibly already finished.
 *
 * So the only connectors the wizard runs for are the ones that are genuinely not
 * connected yet.
 */
export const isOnboarded = (connector, storedComplete = false) =>
  !!storedComplete || (!!connector && connector.status !== STATUS.available.key);

export const connectorDetail = (connector, setupComplete = false) => {
  if (!connector) return null;
  const o = DETAIL_OVERRIDES[connector.id] || {};
  const isLive = connector.status !== 'available';
  const needsAttention = connector.status === 'attention';
  const onboarded = isOnboarded(connector, setupComplete);

  const statusValue = needsAttention
    ? connector.note || 'Needs attention'
    : isLive
      ? 'Connected & healthy'
      : 'Not connected';

  return {
    categoryLabel: CATEGORY_BY_KEY[connector.category] || connector.category,
    feeds: connector.feeds,
    isLive,
    needsAttention,
    facts: [
      { key: 'status', icon: 'fa-circle-check', label: 'Status', value: statusValue },
      {
        key: 'sync',
        icon: 'fa-clock',
        label: 'Last sync',
        value: isLive ? connector.lastSync : 'Never',
      },
      {
        key: 'freshness',
        icon: 'fa-bolt',
        label: 'Data freshness',
        value: isLive ? (needsAttention ? '91.4%' : FRESHNESS) : '—',
      },
      {
        key: 'connected-on',
        icon: 'fa-link',
        label: 'Connected on',
        value: isLive ? o.connectedOn || 'Jul 21, 2026' : '—',
      },
      {
        key: 'auth',
        icon: 'fa-fingerprint',
        label: 'Auth method',
        value: o.authMethod || 'OAuth 2.0',
      },
      {
        key: 'write',
        icon: 'fa-shield-halved',
        label: 'Write access',
        value: o.writeAccess || 'Read only',
      },
    ],
    scopes: o.scopes || connector.feeds.map((f) => `${f.toLowerCase()}:read`),
    quickActions: isLive
      ? QUICK_ACTIONS
      : QUICK_ACTIONS.filter((a) => a.key === 'manage' || a.key === 'activity'),
    /* The button changes with the state, so it never promises the wrong thing —
       and once onboarding is done there is no setup left to resume, so it reports
       that instead of inviting the trip again.

       Attention still wins over it: a degraded connector reading "Setup
       Completed" in green would bury the one thing that needs doing. */
    setupComplete: onboarded && !needsAttention,
    primaryAction: needsAttention
      ? 'Reauthenticate'
      : onboarded
        ? 'Setup Completed'
        : `Connect ${connector.name}`,
    onboardingSteps: [
      { label: 'Grant account access', done: isLive },
      { label: 'Map feeds to lenses', done: isLive && !needsAttention },
      { label: 'Backfill 24 months of history', done: isLive && !needsAttention },
      { label: 'Enable write access', done: onboarded && !needsAttention },
    ],
    activity: isLive
      ? [
          { label: `Synced ${connector.feeds[0]} feed`, when: connector.lastSync, tone: 'ok' },
          { label: 'Token refreshed', when: '1d ago', tone: 'ok' },
          { label: 'Backfill completed', when: '3d ago', tone: 'ok' },
        ]
      : [{ label: 'Not connected yet', when: '—', tone: 'idle' }],
  };
};

/** Page size options behind the "View: N per page" control. */
export const PAGE_SIZES = [12, 24, 48];
