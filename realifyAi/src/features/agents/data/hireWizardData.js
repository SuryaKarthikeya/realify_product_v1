/**
 * Content for the three-step hire wizard that follows the specialist preview:
 * Choose specialist → Assign coverage → Review & launch.
 *
 * The preview screen's own five-stage rail (Connect … Graduate) describes the
 * specialist's ramp; this rail describes the hire itself. They are different
 * things, which is why they are separate lists.
 */
export const WIZARD_STEPS = [
  { key: 'specialist', label: 'Choose specialist', sub: 'Pricing & Margin' },
  { key: 'coverage', label: 'Assign coverage', sub: 'Define where & how it operates' },
  { key: 'review', label: 'Review & launch', sub: 'Confirm and start' },
];

/**
 * Category tree the specialist can be scoped to.
 *
 * `children` nest arbitrarily deep; `defaultOpen` mirrors the branch the design
 * shows expanded. Ids are what selection is tracked by, so renaming a label
 * cannot silently drop a user's coverage.
 */
export const COVERAGE_TREE = [
  {
    id: 'home-kitchen',
    label: 'Home & Kitchen',
    icon: 'fa-house',
    defaultOpen: true,
    children: [
      {
        id: 'cookware',
        label: 'Cookware',
        defaultOpen: true,
        children: [
          { id: 'fry-pans', label: 'Fry Pans' },
          { id: 'pots-pans', label: 'Pots & Pans' },
          { id: 'saucepans', label: 'Saucepans' },
          { id: 'bakeware', label: 'Bakeware' },
        ],
      },
      { id: 'kitchen-tools', label: 'Kitchen Tools' },
    ],
  },
  { id: 'home-appliances', label: 'Home Appliances', children: [
    { id: 'vacuums', label: 'Vacuums' },
    { id: 'small-appliances', label: 'Small Appliances' },
  ] },
  { id: 'dining-serveware', label: 'Dining & Serveware', children: [
    { id: 'dinnerware', label: 'Dinnerware' },
    { id: 'drinkware', label: 'Drinkware' },
  ] },
];

/** Coverage selected when the wizard opens — the branch the design shows ticked. */
export const DEFAULT_COVERAGE = ['home-kitchen', 'cookware', 'fry-pans'];

export const WORKSPACES = [
  { id: 'northwind', initials: 'NH', label: 'Northwind Home & Kitchen' },
  { id: 'northwind-eu', initials: 'NE', label: 'Northwind EU' },
  { id: 'harbour', initials: 'HB', label: 'Harbour Living' },
];

export const TEAMS = [
  { id: 'pricing', label: 'Pricing Team' },
  { id: 'growth', label: 'Growth Team' },
  { id: 'operations', label: 'Operations Team' },
];

/**
 * The autonomy dial, ordered least to most capable.
 *
 * Multi-select: the user may grant more than one level, and `benefits` on the
 * recommended level is what the review step summarises.
 */
export const AUTONOMY_LEVELS = [
  {
    key: 'observe',
    label: 'Observe',
    icon: 'fa-eye',
    lines: ['Monitors and reports.', 'No system changes.'],
    benefits: ['Reads your data without touching it', 'Surfaces what it notices', 'Zero blast radius'],
  },
  {
    key: 'suggest',
    label: 'Suggest',
    icon: 'fa-lightbulb',
    lines: ['Makes recommendations.', 'Needs approval.'],
    benefits: ['Proposes every change as an ask', 'Nothing moves without your click', 'You see the reasoning first'],
  },
  {
    key: 'assist',
    label: 'Assist',
    icon: 'fa-bolt',
    recommended: true,
    lines: ['Acts within guardrails.', 'Human in the loop.'],
    benefits: [
      'Can take actions within defined guardrails',
      'Requires approval for important decisions',
      'You stay in control',
    ],
  },
  {
    key: 'act',
    label: 'Act',
    icon: 'fa-crosshairs',
    lines: ['Operates autonomously.', 'Within policy.'],
    benefits: ['Acts without an approval step', 'Bounded by the Playbook', 'Opens a case on any breach'],
  },
];

/** Default grant — the level the design shows chosen. */
export const DEFAULT_AUTONOMY = ['assist'];

/** Review-step sidebar. */
export const WHAT_HAPPENS_NEXT = [
  {
    title: 'Starts in Shadow mode',
    description: 'The specialist will observe, learn and simulate actions before recommending.',
  },
  {
    title: 'Follows the Pricing & Margin playbook',
    description: 'Uses proven signals, rules and guardrails built by Realify.',
  },
  {
    title: 'Monitors 24/7',
    description: 'Watches 5 signals every clock and surfaces insights daily.',
  },
  {
    title: 'Reports to you',
    description: "You'll get alerts, weekly performance reports and recommendations.",
  },
];

export const EXPECTED_OUTCOMES = [
  'Protect CM3 and MAP',
  'Maintain price image and cover',
  'Respond to competitor moves faster',
  'Increase margin and profitability',
];

/** Launch-screen checklist. The last item is still running, hence the spinner. */
export const ONBOARDING_TASKS = [
  { label: 'Connected to workspace', done: true },
  { label: 'Playbook loaded', done: true },
  { label: 'Coverage assigned', done: true },
  { label: 'Reading historical data...', done: false },
];

export const ONBOARDING_PROGRESS = 42;

/* ── helpers ── */

/** Flattens the tree so a selection of ids can be resolved to labels. */
export const flattenTree = (nodes = COVERAGE_TREE, out = []) => {
  for (const node of nodes) {
    out.push(node);
    if (node.children) flattenTree(node.children, out);
  }
  return out;
};

/** Every id in the tree — what "Select all" grants. */
export const allCoverageIds = () => flattenTree().map((n) => n.id);

/**
 * The selected coverage as an ordered path, deepest last, so it reads as a
 * breadcrumb ("Home & Kitchen › Cookware › Fry Pans") rather than an id list.
 */
export const coveragePath = (selected = []) => {
  const walk = (nodes, trail = []) => {
    for (const node of nodes) {
      const next = selected.includes(node.id) ? [...trail, node] : trail;
      if (node.children) {
        const deeper = walk(node.children, next);
        if (deeper.length > next.length) return deeper;
      }
      if (selected.includes(node.id) && next.length > trail.length) return next;
    }
    return trail;
  };
  return walk(COVERAGE_TREE);
};

/** The autonomy levels a selection maps to, in dial order. */
export const selectedAutonomy = (keys = []) =>
  AUTONOMY_LEVELS.filter((l) => keys.includes(l.key));

/**
 * Label for the trust chip. One level names itself; several are summarised by
 * the most capable, since that is the ceiling the user actually granted.
 */
export const autonomyLabel = (keys = []) => {
  const levels = selectedAutonomy(keys);
  if (levels.length === 0) return 'Not set';
  if (levels.length === 1) return levels[0].label;
  return `${levels[levels.length - 1].label} +${levels.length - 1}`;
};
