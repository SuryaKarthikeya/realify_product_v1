import { SIGNALS_BY_TAB } from '@/data/insightsData';
import { getImpactSign } from '@/config/actionTypeConfig';
import { formatCompactMoney } from '@/utils/formatters';

/**
 * Action Center data — derived from the live Workspace signal set (SIGNALS_BY_TAB)
 * instead of a hand-written list, so the Action Center always reflects the same
 * signals the Workspace surfaces.
 *
 * The shape below is deliberately identical to the previous hand-written data
 * (title / priority / priorityColor / actionId / due / category / status /
 * assignee / description / impact / steps / relatedActions / timeline) so
 * ActionsTable, ActionDetail, ActionStatsCard and useActionFilters keep working
 * unchanged. Signal-native fields (exposure, metrics, miniStats, …) ride along
 * for the simulation modal.
 */

/* Module is always called "Revenue", never "Sales" — matches WORKSPACE_TABS. */
const MODULE_META = {
  sales:     { label: 'Revenue',   code: 'REV', owner: 'Revenue Desk' },
  margin:    { label: 'Margin',    code: 'MAR', owner: 'Margin Desk' },
  cash:      { label: 'Cash',      code: 'CSH', owner: 'Finance Desk' },
  inventory: { label: 'Inventory', code: 'INV', owner: 'Supply Desk' },
  ads:       { label: 'Ads',       code: 'ADS', owner: 'Growth Desk' },
};

/* HIGH + top urgency reads as CRITICAL in the Action Center's priority scale. */
const toPriority = (signal) => {
  const raw = (signal.priority || '').toUpperCase();
  if (raw === 'HIGH') return signal.urgencyVal >= 5 ? 'CRITICAL' : 'HIGH';
  if (raw === 'MED' || raw === 'MEDIUM') return 'MEDIUM';
  return 'LOW';
};

const PRIORITY_COLOR = {
  CRITICAL: 'red',
  HIGH: 'orange',
  MEDIUM: 'yellow',
  LOW: 'blue',
};

const DUE_BY_URGENCY = { 5: 'Today', 4: 'Tomorrow', 3: 'In 3 days', 2: 'This week' };
const TIMELINE_BY_URGENCY = {
  5: 'Act within 24h',
  4: 'Act within 48h',
  3: 'Act this week',
  2: 'Monitor this week',
};

/* No status field on signals — derive it from urgency so all three filter
   options (Pending / In Progress / Completed) stay reachable. */
const toStatus = (urgencyVal) => {
  if (urgencyVal >= 4) return 'Pending';
  if (urgencyVal === 3) return 'In Progress';
  return 'Completed';
};

const buildActionId = (code, index) => `#ACT-${code}-${String(index + 1).padStart(2, '0')}`;

const buildSteps = (signal) => {
  const steps = [
    `Validate the ${signal.tagCategory} signal on ${signal.skuCode} — confidence ${signal.confidenceScore}%.`,
  ];
  if (signal.headlineHighlight) steps.push(signal.headlineHighlight);
  if (signal.recommendedAction?.description) steps.push(signal.recommendedAction.description);
  if (signal.metrics?.velocity && signal.metrics?.threshold) {
    steps.push(`Track ${signal.metrics.velocity} against the ${signal.metrics.threshold} threshold after rollout.`);
  }
  steps.push(`Confirm ${signal.exposureFormatted} exposure is recovered, then log the outcome in the Action Log.`);
  return steps;
};

/* Flatten every module's signals into one action list, preserving module order. */
const FLAT_SIGNALS = Object.entries(SIGNALS_BY_TAB).flatMap(([tabKey, signals]) =>
  signals.map((signal, indexInTab) => ({ signal, tabKey, indexInTab })),
);

const ACTION_ID_BY_SIGNAL_ID = FLAT_SIGNALS.reduce((acc, { signal, tabKey, indexInTab }) => {
  acc[signal.id] = buildActionId(MODULE_META[tabKey].code, indexInTab);
  return acc;
}, {});

/* Total exposure per module — the denominator for each action's impact share. */
const MODULE_EXPOSURE_TOTAL = Object.entries(SIGNALS_BY_TAB).reduce((acc, [tab, signals]) => {
  acc[tab] = signals.reduce((sum, s) => sum + (s.exposure || 0), 0);
  return acc;
}, {});

const toAction = ({ signal, tabKey, indexInTab }) => {
  const meta = MODULE_META[tabKey];
  const priority = toPriority(signal);

  /* Impact value/percent are signed: negative where value is currently
     bleeding, positive where there is upside to capture. The percent is the
     signal's share of its module's total exposure — derived, not hand-set. */
  const sign = getImpactSign({ signalType: signal.type });
  const moduleTotal = MODULE_EXPOSURE_TOTAL[tabKey] || 0;
  const impactPct = moduleTotal
    ? Math.round(((signal.exposure || 0) / moduleTotal) * 1000) / 10
    : 0;

  /* Related actions = the other signals inside the same module, capped at 2. */
  const relatedActions = SIGNALS_BY_TAB[tabKey]
    .filter((sibling) => sibling.id !== signal.id)
    .slice(0, 2)
    .map((sibling) => `${ACTION_ID_BY_SIGNAL_ID[sibling.id]} - ${sibling.recommendedAction?.title || sibling.type}`);

  return {
    id: signal.id,
    title: signal.recommendedAction?.title || signal.type,
    priority,
    priorityColor: PRIORITY_COLOR[priority],
    actionId: buildActionId(meta.code, indexInTab),
    due: DUE_BY_URGENCY[signal.urgencyVal] || 'This week',
    category: meta.label,
    status: toStatus(signal.urgencyVal),
    assignee: meta.owner,
    description: signal.whyMattersText,
    impact: signal.intervention,
    steps: buildSteps(signal),
    relatedActions,
    timeline: TIMELINE_BY_URGENCY[signal.urgencyVal] || 'Monitor this week',

    /* ── Signal-native extras (used by the simulation modal) ── */
    tabKey,
    signalType: signal.type,
    tagCategory: signal.tagCategory,
    skuCode: signal.skuCode,
    headline: signal.headline,
    headlineHighlight: signal.headlineHighlight,
    exposure: signal.exposure,
    exposureFormatted: signal.exposureFormatted,
    impactValue: sign * (signal.exposure || 0),
    impactPct: sign * impactPct,
    impactBasisLabel: `${meta.label} exposure share`,
    urgency: signal.urgency,
    confidenceScore: signal.confidenceScore,
    easeVal: signal.easeVal,
    complexityVal: signal.complexityVal,
    metrics: signal.metrics,
    miniStats: signal.miniStats,
  };
};

export const actionDetails = FLAT_SIGNALS.reduce((acc, entry) => {
  acc[entry.signal.id] = toAction(entry);
  return acc;
}, {});

export const actionItems = Object.values(actionDetails);

const countBy = (predicate) => actionItems.filter(predicate).length;

const totalExposure = actionItems.reduce((sum, action) => sum + (action.exposure || 0), 0);

export const actionStats = [
  {
    title: 'Critical Actions',
    value: String(countBy((a) => a.priority === 'CRITICAL')),
    subtitle: 'Requires immediate attention',
    icon: 'fa-exclamation-triangle',
    color: 'from-red-400 to-red-500',
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    borderColor: 'border-red-200',
  },
  {
    title: 'High Priority',
    value: String(countBy((a) => a.priority === 'HIGH')),
    subtitle: 'Action needed within 48h',
    icon: 'fa-arrow-up',
    color: 'from-orange-400 to-orange-500',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200',
  },
  {
    title: 'In Progress',
    value: String(countBy((a) => a.status === 'In Progress')),
    subtitle: 'Currently being addressed',
    icon: 'fa-spinner',
    color: 'from-blue-400 to-blue-500',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200',
  },
  {
    title: 'Exposure at Risk',
    value: formatCompactMoney(totalExposure),
    subtitle: `Across ${actionItems.length} open signals`,
    icon: 'fa-dollar-sign',
    color: 'from-green-400 to-green-500',
    bgColor: 'bg-green-50',
    textColor: 'text-green-700',
    borderColor: 'border-green-200',
  },
];
