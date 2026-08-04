/**
 * The four subscription tiers.
 *
 * Annual prices are derived from the monthly ones rather than written twice —
 * a hardcoded pair would silently drift the moment a price changed, and the
 * "Save 17%" claim next to the toggle has to stay true.
 */

export const ANNUAL_DISCOUNT = 0.17;

export const BILLING_CYCLES = [
  { key: 'monthly', label: 'Monthly billing' },
  { key: 'annual', label: 'Annual billing', badge: `SAVE ${Math.round(ANNUAL_DISCOUNT * 100)}%` },
];

/** Monthly-equivalent price for a cycle, rounded to whole dollars. */
export const priceFor = (plan, cycle) => {
  if (plan.isCustomPrice) return plan.price;
  const monthly = plan.monthly;
  const value = cycle === 'annual' ? Math.round(monthly * (1 - ANNUAL_DISCOUNT)) : monthly;
  return `$${value.toLocaleString('en-US')}`;
};

export const SUBSCRIPTION_PLANS = [
  {
    id: 'observe',
    name: 'Observe',
    monthly: 49,
    tagline: 'See what Realify would do, before you let it act.',
    trial: '14-day free trial',
    cta: 'Start free trial',
    features: [
      '250 managed SKU-channels',
      '1 sales channel',
      'Daily data refresh',
      'Recommendations only, never acts on its own',
      'Full agent and lens access',
      'Shadow Mode - see what would have happened',
    ],
  },
  {
    id: 'operate',
    name: 'Operate',
    monthly: 799,
    recommended: true,
    tagline: 'Coordinated profit protection, running every day.',
    inherits: 'Everything in Observe, plus',
    trial: '30-day free trial',
    cta: 'Start free trial',
    features: [
      '2,000 SKU-channels, then $0.18 each',
      'Up to 6 sales channels',
      '4-hour data refresh',
      'Suggest → Assist → Act autonomy control',
      '500 Decisions included, then $0.35',
      '20 copilot hours per month',
    ],
  },
  {
    id: 'orchestrate',
    name: 'Orchestrate',
    monthly: 1499,
    /* The plan this workspace is on. Kept alongside `recommended` so the settings
       page can still answer "what am I paying for" — the marketing page has no
       reason to show it, but this one does. */
    current: true,
    tagline: 'Larger catalogs, more channels, tighter governance.',
    inherits: 'Everything in Operate, plus',
    trial: '30-day free trial',
    cta: 'Start free trial',
    features: [
      '5,000 SKU-channels, then $0.16 each',
      'Unlimited sales channels',
      '2,000 Decisions included, then $0.28',
      '60 copilot hours per month',
      'Custom approval workflows',
      'Compliance attestation pack',
      'Named success manager',
    ],
  },
  {
    id: 'custom',
    name: 'Custom',
    /* Quoted, not metered — shows a label where the others show a price. */
    isCustomPrice: true,
    price: 'Talk to us',
    audience: 'Agencies & enterprise brands',
    tagline: 'Portfolios, white-label, and negotiated terms.',
    inherits: 'Everything in Orchestrate, plus',
    trial: 'Custom pilot',
    cta: 'Talk to sales',
    features: [
      'Pooled capacity across your portfolio',
      'Agency console and white-label',
      'SSO, SCIM, audit logs, MSA',
      'BYOK and private deployment',
      'Outcome-based pricing available',
      'Dedicated onboarding',
    ],
  },
];

/** The small print under the plan grid. */
export const SUBSCRIPTION_FOOTNOTES = [
  { text: `Save ${Math.round(ANNUAL_DISCOUNT * 100)}% with annual billing`, highlight: true },
  { text: 'Cancel anytime' },
  { text: 'Add-on: premium 2-hour data refresh from $99/month' },
  { text: 'Prices in USD, excluding tax' },
];

/**
 * Usage against the current plan's entitlements.
 *
 * The totals are Orchestrate's own numbers, so the meters measure what the plan
 * above actually sells rather than a separate vocabulary of its own.
 */
export const SUBSCRIPTION_USAGE = [
  { label: 'Managed SKU-channels', val: 3412, total: 5000, color: 'bg-brand dark:bg-gray-600' },
  { label: 'Decisions', val: 1180, total: 2000, color: 'bg-brand dark:bg-gray-600' },
  { label: 'Copilot hours', val: 22, total: 60, color: 'bg-brand dark:bg-gray-600' },
  { label: 'Sales channels', val: 6, total: 'Unlimited', color: 'bg-emerald-600', isLabelOnly: true },
];
