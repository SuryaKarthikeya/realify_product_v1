import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import BriefCard from '@/components/data-display/brief/BriefCard';
import SignalsTable from '@/features/workspace/components/SignalsTable';
import CompactKpiStrip from '@/features/workspace/components/CompactKpiStrip';
import FilterSelect from '@/features/workspace/components/FilterSelect';
import DateFilterSelect from '@/features/workspace/components/DateFilterSelect';
import SkuFilterPopover from '@/features/workspace/components/SkuFilterPopover';
import {
  IMPACT_BANDS,
  ACTION_OPTIONS_BY_DOMAIN,
  EMPTY_SKU_FILTER,
} from '@/features/workspace/skuFilterOptions';
import { formatCompactMoney, formatNumber } from '@/utils/formatters';
import {
  isFilterOff,
  matchesChannel,
  matchesCategory,
  matchesStatus,
} from '@/features/workspace/signalFilters';
import InsightDetailsPanel from '@/features/workspace/components/InsightDetailsPanel';
import DismissModal from '@/features/workspace/components/DismissModal';
import RepriceModal from '@/features/workspace/components/RepriceModal';
import CaseReportModal from '@/features/workspace/components/CaseReportModal';
import { useWorkspaceOverview } from '@/features/workspace/hooks/useWorkspaceOverview';
import { useWorkspaceDomainCards } from '@/features/workspace/hooks/useWorkspaceDomainCards';
import { useViewModeStore } from '@/store/useViewModeStore';
import { useWorkspaceFilterStore } from '@/store/useWorkspaceFilterStore';
import { useUIStore } from '@/store/useUIStore';
import { useStickyOnScroll } from '@/hooks/useStickyOnScroll';
import {
  dashboardPath,
  toDomainKey,
  workspacePath,
  DOMAIN_SEGMENTS,
} from '@/features/workspace/workspaceRoutes';
import { ROUTES } from '@/constants/routes';
import { PRODUCT_CATEGORIES } from '@/constants/filterOptions';

const MAIN_TABS = [
  { key: 'sales', label: 'Revenue' },
  { key: 'margin', label: 'Margin' },
  { key: 'inventory', label: 'Inventory' },
  { key: 'ads', label: 'Ads' },
  { key: 'cash', label: 'Cash' },
];

/** Icon + fallback title for each of the 5 main KPI cards, keyed by internal domain key. */
const KPI_CARD_META = {
  sales: { icon: 'fa-arrow-trend-up', title: 'Revenue' },
  margin: { icon: 'fa-percent', title: 'Margin' },
  inventory: { icon: 'fa-boxes-stacked', title: 'Inventory value' },
  ads: { icon: 'fa-bullhorn', title: 'Ad spend' },
  cash: { icon: 'fa-wallet', title: 'Cash received' },
};

/** GET /api/workspace's `kpis[].id` -> this app's internal domain key. */
const API_KPI_ID_TO_KEY = {
  revenue: 'sales',
  margin: 'margin',
  inventory: 'inventory',
  ads: 'ads',
  cash: 'cash',
};

/** The label shown beneath every KPI/sub-stat card. */
const TIME_RANGES = {
  '7D': { label: 'Last 7 days' },
  '30D': { label: 'Last 30 days' },
  '60D': { label: 'Last 60 days' },
  ALL: { label: 'All time' },
};

const DEFAULT_RANGE = TIME_RANGES['30D'];

/** `window` query param sent to the API for the 'ALL' range — there's no
 *  real "unbounded" option server-side, so this stands in as a window wide
 *  enough to cover any shop's history (10 years). Deliberately not a more
 *  extreme value (e.g. 100 years) — an unusually large `window` is more
 *  likely to hit backend validation/clamping than a merely generous one. */
const ALL_TIME_WINDOW_DAYS = 3650;

/**
 * How to render each domain's raw sub-stat value from GET /api/workspace/{domain}.
 * Keyed by this app's internal domain key, then by the API's `cards[].key`.
 */
const CARD_VALUE_FORMAT = {
  sales: { net_revenue: 'money', orders: 'count', conversion_rate: 'percent', aov: 'money', buybox_pct: 'percent' },
  margin: { cm1: 'money', gross_margin: 'money', cm2: 'money', cm3: 'money', unprofitable_skus: 'count' },
  inventory: { days_of_cover: 'days', oos_risks: 'money', oos_skus: 'count', sell_through_pct: 'percent', dead_inventory: 'money' },
  ads: { total_ad_spend: 'money', roas: 'ratio', margin_adj_roas: 'ratio', ctr: 'percent', cpc: 'money' },
  cash: { cash_balance: 'money', cash_inflow: 'money', cash_outflow: 'money', net_cash_flow: 'money', payouts_pending: 'money' },
};

const formatCardValue = (value, format) => {
  if (value === null || value === undefined) return '—';
  switch (format) {
    case 'money': return formatCompactMoney(value);
    case 'percent': return `${value}%`;
    case 'ratio': return `${value}x`;
    case 'days': return `${value}d`;
    case 'count': return formatNumber(value);
    default: return String(value);
  }
};

/* ── Filter bar options. First entry is the "no filter" default. ── */
// Derived from the single taxonomy so this list can never drift from the data.
const CATEGORY_OPTIONS = [
  { value: 'all', label: 'All' },
  ...PRODUCT_CATEGORIES.map((c) => ({ value: c.value, label: c.label })),
];

const CHANNEL_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'amazon', label: 'Amazon' },
  { value: 'walmart', label: 'Walmart' },
  { value: 'shopify', label: 'Shopify' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'executed', label: 'Executed' },
  { value: 'not_executed', label: 'Not Executed' },
];

/** Ads domain only — the ad platform a campaign ran on. */
const AD_PLATFORM_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'amazon-ads', label: 'Amazon Ads' },
  { value: 'meta-ads', label: 'Meta Ads' },
  { value: 'google-ads', label: 'Google Ads' },
];

/** Inventory domain only filters */
const FULFILLMENT_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'fba', label: 'FBA' },
  { value: '3pl', label: '3PL' },
  { value: 'fbm', label: 'FBM' },
];

const STOCKOUT_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: '3', label: '3 days' },
  { value: '4-7', label: '4–7 days' },
  { value: '8-14', label: '8–14 days' },
];

const CONFIDENCE_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: '>85', label: '> 85%' },
  { value: '<70', label: '<70%' },
];

/** Cash domain only filters */
const URGENCY_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: '<=7', label: '≤7 days' },
  { value: '<=30', label: '≤30 days' },
  { value: '<=90', label: '≤90 days' },
];

const CASH_DIRECTION_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'inflow_accelerating', label: 'Inflow Accelerating' },
  { value: 'outflow_reducing', label: 'Outflow Reducing' },
];

/** Text search across the fields a row actually shows. */
const matchesSearch = (signal, term) => {
  if (!term.trim()) return true;
  const haystack = [
    signal.campaign,
    signal.skuCode,
    signal.category,
    signal.headline,
    signal.headlineHighlight,
    signal.tagCategory,
  ].filter(Boolean).join(' ').toLowerCase();
  return haystack.includes(term.trim().toLowerCase());
};

/** Icon & color styling for each sub-KPI slot per domain */
const STAT_CARD_META = {
  cash: [
    { icon: 'fa-wallet', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-arrow-down', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-arrow-up', iconBg: 'bg-rose-50 dark:bg-rose-950/60', iconColor: 'text-rose-600 dark:text-rose-400' },
    { icon: 'fa-chart-line', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-credit-card', iconBg: 'bg-blue-50 dark:bg-blue-950/60', iconColor: 'text-blue-600 dark:text-blue-400' },
  ],
  sales: [
    { icon: 'fa-dollar-sign', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-cart-shopping', iconBg: 'bg-blue-50 dark:bg-blue-950/60', iconColor: 'text-blue-600 dark:text-blue-400' },
    { icon: 'fa-tag', iconBg: 'bg-purple-50 dark:bg-purple-950/60', iconColor: 'text-purple-600 dark:text-purple-400' },
    { icon: 'fa-repeat', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-chart-line', iconBg: 'bg-amber-50 dark:bg-amber-950/60', iconColor: 'text-amber-600 dark:text-amber-400' },
  ],
  margin: [
    { icon: 'fa-percent', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-scale-balanced', iconBg: 'bg-blue-50 dark:bg-blue-950/60', iconColor: 'text-blue-600 dark:text-blue-400' },
    { icon: 'fa-coins', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-receipt', iconBg: 'bg-purple-50 dark:bg-purple-950/60', iconColor: 'text-purple-600 dark:text-purple-400' },
    { icon: 'fa-triangle-exclamation', iconBg: 'bg-rose-50 dark:bg-rose-950/60', iconColor: 'text-rose-600 dark:text-rose-400' },
  ],
  inventory: [
    { icon: 'fa-boxes-stacked', iconBg: 'bg-blue-50 dark:bg-blue-950/60', iconColor: 'text-blue-600 dark:text-blue-400' },
    { icon: 'fa-warehouse', iconBg: 'bg-amber-50 dark:bg-amber-950/60', iconColor: 'text-amber-600 dark:text-amber-400' },
    { icon: 'fa-clock', iconBg: 'bg-rose-50 dark:bg-rose-950/60', iconColor: 'text-rose-600 dark:text-rose-400' },
    { icon: 'fa-truck-fast', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-box-open', iconBg: 'bg-purple-50 dark:bg-purple-950/60', iconColor: 'text-purple-600 dark:text-purple-400' },
  ],
  ads: [
    { icon: 'fa-bullhorn', iconBg: 'bg-rose-50 dark:bg-rose-950/60', iconColor: 'text-rose-600 dark:text-rose-400' },
    { icon: 'fa-eye', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-hand-pointer', iconBg: 'bg-emerald-50 dark:bg-emerald-950/60', iconColor: 'text-emerald-600 dark:text-emerald-400' },
    { icon: 'fa-percent', iconBg: 'bg-blue-50 dark:bg-blue-950/60', iconColor: 'text-blue-600 dark:text-blue-400' },
    { icon: 'fa-sack-dollar', iconBg: 'bg-amber-50 dark:bg-amber-950/60', iconColor: 'text-amber-600 dark:text-amber-400' },
  ],
};

const WorkspacePage = () => {
  const { domainSegment } = useParams();
  const activeDomain = toDomainKey(domainSegment);
  const navigate = useNavigate();

  const [selectedMainKpi, setSelectedMainKpi] = useState(null);

  const { setDashboardView, setLastWorkspaceDomain } = useViewModeStore();
  useEffect(() => {
    setDashboardView(false);
    setLastWorkspaceDomain(activeDomain);
  }, [activeDomain]); // eslint-disable-line react-hooks/exhaustive-deps

  // Filter Store
  const {
    marketplace,
    setMarketplace,
    categoryCut,
    setCategoryCut,
    statusFilter,
    setStatusFilter,
    timeRange,
    setTimeRange,
    adPlatform,
    setAdPlatform,
    fulfillmentType,
    setFulfillmentType,
    stockoutTime,
    setStockoutTime,
    confidence,
    setConfidence,
    urgency,
    setUrgency,
    cashDirection,
    setCashDirection,
    executedSignalIds,
    markSignalExecuted,
  } = useWorkspaceFilterStore();

  const [expandedInsight, setExpandedInsight] = useState(null);
  const [panelTab, setPanelTab] = useState('reasons');
  const [isDismissModalOpen, setIsDismissModalOpen] = useState(false);
  const [isRepriceModalOpen, setIsRepriceModalOpen] = useState(false);
  const [isCaseReportModalOpen, setIsCaseReportModalOpen] = useState(false);
  
  const [openDropdown, setOpenDropdown] = useState(null);
  const filterBarRef = React.useRef(null);
  // Watches only the KPI card grid (not the whole section — the Actions table
  // below it is tall enough to stay on screen indefinitely), so the compact
  // strip takes over as soon as the cards themselves scroll away.
  const kpiBlockRef = React.useRef(null);
  const showSticky = useStickyOnScroll(kpiBlockRef, {
    threshold: [0, 0.1, 0.25, 0.28, 0.5, 1.0],
    isStuck: (entry) => entry.intersectionRatio < 0.28,
  });


  
  /**
   * Closes whichever dropdown is open when the click lands outside *any* filter
   * dropdown.
   *
   * Scoping this to a single ref was wrong once the Channel/date controls moved
   * into the KPI header: clicks there counted as "outside", so mousedown closed
   * the menu and the button's click immediately reopened it (the arrow never
   * closed it), and clicking an option unmounted it before the click landed —
   * so nothing could be selected. Matching on the shared marker covers every
   * dropdown regardless of where it renders.
   */
  useEffect(() => {
    if (!openDropdown) return undefined;
    const onPointerDown = (e) => {
      if (!e.target.closest('[data-filter-dropdown]')) setOpenDropdown(null);
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [openDropdown]);

  useEffect(() => {
    if (!openDropdown) return undefined;
    const onKeyDown = (e) => { if (e.key === 'Escape') setOpenDropdown(null); };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [openDropdown]);

  const toggleDropdown = (key) => setOpenDropdown((cur) => (cur === key ? null : key));

  const [skuFilter, setSkuFilter] = useState(EMPTY_SKU_FILTER);


  const currentDomainKey = selectedMainKpi || activeDomain;
  // The Actions table mirrors the KPI grid above it: the overall workspace
  // action list while no domain is selected, or the open domain's own action
  // list once one is — never a client-side filter of the overall list.
  const showingMainKpis = selectedMainKpi === null;
  const isAdsDomain = currentDomainKey === 'ads';
  const isInventoryDomain = currentDomainKey === 'inventory';
  const isCashDomain = currentDomainKey === 'cash';
  const range = TIME_RANGES[timeRange] || DEFAULT_RANGE;
  const windowDays = timeRange === 'ALL' ? ALL_TIME_WINDOW_DAYS : (parseInt(timeRange, 10) || 30);
  const actionOptions = ACTION_OPTIONS_BY_DOMAIN[currentDomainKey] || ACTION_OPTIONS_BY_DOMAIN.sales;

  // GET /api/workspace — brief + 5 main KPI cards + overall actions, loaded once and on window change.
  const {
    brief: briefData,
    kpis: apiKpis,
    actions: overviewActions,
    loading: overviewLoading,
  } = useWorkspaceOverview(windowDays);

  // GET /api/workspace/{domain} — only fires once a main KPI card is selected.
  const { cards: domainCards, actions: domainActions, loading: domainCardsLoading } = useWorkspaceDomainCards(
    selectedMainKpi ? DOMAIN_SEGMENTS[currentDomainKey] : null,
    windowDays
  );

  const mainKpiCards = Object.keys(KPI_CARD_META).map((key) => {
    const meta = KPI_CARD_META[key];
    const apiKpi = apiKpis.find((k) => API_KPI_ID_TO_KEY[k.id] === key);
    return {
      key,
      icon: meta.icon,
      title: apiKpi?.title || meta.title,
      value: apiKpi ? formatCompactMoney(apiKpi.value) : (overviewLoading ? '…' : '—'),
      subtext: range.label,
      isPositive: true,
    };
  });

  const domainValueFormat = CARD_VALUE_FORMAT[currentDomainKey] || {};
  const currentSubStats = domainCards.length
    ? domainCards.map((card) => ({
        title: card.label,
        // CM1/CM2/CM3 carry their own margin % (`card.pct`) — that's the
        // number worth leading with, not the underlying money value.
        value: typeof card.pct === 'number' ? `${card.pct}%` : formatCardValue(card.value, domainValueFormat[card.key]),
        subtext: card.note || range.label,
        isPositive: true,
      }))
    : Array.from({ length: 5 }, () => ({
        title: domainCardsLoading ? '…' : '—',
        value: domainCardsLoading ? '…' : '—',
        subtext: range.label,
        isPositive: true,
      }));

  // Always the current API response's own action list — never the overall
  // list filtered client-side down to a domain, so there's a single source
  // of truth for what's on screen.
  const rawSignals = showingMainKpis ? overviewActions : domainActions;

  // Which signal `type` values the chosen "filter by action" options cover.
  const selectedActionTypes = new Set(
    actionOptions
      .filter((o) => skuFilter.actions.includes(o.key))
      .flatMap((o) => o.types)
  );

  const filteredSignals = rawSignals.filter((s) => {
    // Channel / category / status are multi-select: empty means no filter, and
    // selections within one filter are OR'd together.
    if (!matchesChannel(s, marketplace)) return false;
    if (!matchesCategory(s, categoryCut)) return false;
    if (!matchesStatus(s, statusFilter, executedSignalIds)) return false;

    // Only meaningful on Ads, and only Ads rows carry adPlatform.
    if (isAdsDomain && adPlatform !== 'all' && s.adPlatform !== adPlatform) {
      return false;
    }

    // ── SKU popover filters ──
    if (!matchesSearch(s, skuFilter.search)) return false;

    if (skuFilter.impact.length) {
      const bands = IMPACT_BANDS.filter((b) => skuFilter.impact.includes(b.key));
      if (!bands.some((b) => b.test(s.exposure || 0))) return false;
    }

    if (selectedActionTypes.size && !selectedActionTypes.has(s.type)) return false;

    const isActive = s.isActiveSku !== false;
    if (isActive && !skuFilter.showActive) return false;
    if (!isActive && !skuFilter.showInactive) return false;

    return true;
  });

  // Drives the empty state: with no filter on, an empty table means there is
  // genuinely nothing to act on rather than something being hidden.
  const isAnyFilterActive =
    !isFilterOff(marketplace) ||
    !isFilterOff(categoryCut) ||
    !isFilterOff(statusFilter) ||
    (isAdsDomain && adPlatform !== 'all') ||
    (isInventoryDomain && (fulfillmentType !== 'all' || stockoutTime !== 'all' || confidence !== 'all')) ||
    (isCashDomain && (urgency !== 'all' || cashDirection !== 'all')) ||
    Boolean(skuFilter.search.trim()) ||
    skuFilter.impact.length > 0 ||
    skuFilter.actions.length > 0 ||
    !skuFilter.showActive ||
    !skuFilter.showInactive;

  const clearAllFilters = () => {
    setMarketplace([]);
    setCategoryCut([]);
    setStatusFilter([]);
    setAdPlatform('all');
    setFulfillmentType('all');
    setStockoutTime('all');
    setConfidence('all');
    setUrgency('all');
    setCashDirection('all');
    setSkuFilter(EMPTY_SKU_FILTER);
  };

  // SKU sort applies to whatever labels the rows are showing.
  const sortedSignals = skuFilter.sort
    ? [...filteredSignals].sort((a, b) => {
        const key = (s) => (s.campaign || s.skuCode || '').toLowerCase();
        return skuFilter.sort === 'asc'
          ? key(a).localeCompare(key(b))
          : key(b).localeCompare(key(a));
      })
    : filteredSignals;

  const handleTakeAction = (signal) => {
    markSignalExecuted(signal.id);
    if (signal.tagCategory?.toLowerCase().includes('reprice')) {
      setIsRepriceModalOpen(true);
    }
  };

  const handleSimulateClick = (signal) => {
    setExpandedInsight(signal);
    setPanelTab('analysis');
  };

  const isExpanded = Boolean(expandedInsight);

  const { setSidebarCollapsed } = useUIStore();
  const wasCollapsedRef = React.useRef(null);

  useEffect(() => {
    if (isExpanded) {
      if (wasCollapsedRef.current === null) {
        wasCollapsedRef.current = useUIStore.getState().isSidebarCollapsed;
      }
      setSidebarCollapsed(true);
    } else {
      if (wasCollapsedRef.current !== null) {
        setSidebarCollapsed(wasCollapsedRef.current);
        wasCollapsedRef.current = null;
      }
    }
  }, [isExpanded, setSidebarCollapsed]);

  // KPI card fill + gradient stroke by card type (high = positive/green, low = negative/red).
  // Gradient border via padding-box/border-box so it respects the rounded corners.
  /**
   * The two-layer gradient a KPI card is painted with: a surface on padding-box
   * and an edge on border-box, which is what gives it a gradient border.
   *
   * Both layers come from CSS custom properties rather than literal colours.
   * They have to be set through the `background` shorthand — so an inline style —
   * and an inline style can't carry a `dark:` variant, which is why these cards
   * used to stay white in dark mode while their values turned white and vanished.
   * The vars re-resolve under `.dark`; see the token block in index.css.
   */
  const kpiCardStyle = (isPositive) => ({
    border: '1px solid transparent',
    background: isPositive
      ? 'var(--kpi-pos-surface) padding-box, var(--kpi-pos-edge) border-box'
      : 'var(--kpi-neg-surface) padding-box, var(--kpi-neg-edge) border-box',
  });

  // The compact strip mirrors the grid: domain KPIs while none is selected,
  // otherwise the open domain's sub-KPIs.
  const kpiData = showingMainKpis ? mainKpiCards : currentSubStats;

  const selectDomain = (domain) => {
    setSelectedMainKpi(domain);
    navigate(workspacePath(domain));
  };

  const renderTopControls = (prefix) => (
    <div className="flex items-center gap-2.5 flex-shrink-0">
      <FilterSelect
        label="Channel"
        value={marketplace}
        options={CHANNEL_OPTIONS}
        onChange={setMarketplace}
        multiple
        isOpen={openDropdown === `channel_${prefix}`}
        onToggle={() => toggleDropdown(`channel_${prefix}`)}
        width="w-[140px]"
      />
      
      <DateFilterSelect
        timeRange={timeRange}
        setTimeRange={setTimeRange}
        isOpen={openDropdown === `date_${prefix}`}
        onToggle={() => toggleDropdown(`date_${prefix}`)}
        onClose={() => setOpenDropdown(null)}
      />

      <div className="flex items-center gap-2 pl-1">
        <span className="text-xs font-semibold text-gray-600 dark:text-slate-400">
          Dashboard
        </span>
        <button
          onClick={() =>
            navigate(dashboardPath(activeDomain), {
              state: { from: ROUTES.WORKSPACE },
            })
          }
          className="relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full bg-gray-200 dark:bg-slate-700 transition-colors p-0.5"
        >
          <span className="inline-block h-4 w-4 transform rounded-full bg-white dark:bg-slate-900 shadow-xs transition-transform translate-x-0" />
        </button>
      </div>
    </div>
  );

  return (
    <DashboardLayout
      title="Workspace"
      showSearch={false}
      showTabs={false}
      showAIPrompt={true}
      aiPromptFullWidth={true}
    >
      {/* ── STICKY COMPACT KPI HEADER ── */}
      <CompactKpiStrip
        visible={showSticky}
        kpis={kpiData.slice(0, 5)}
        onKpiClick={showingMainKpis ? (kpi) => selectDomain(kpi.key) : undefined}
        onDashboardClick={() =>
          navigate(dashboardPath(activeDomain), { state: { from: ROUTES.WORKSPACE } })
        }
      />

      <div className="flex flex-col gap-3.5 max-w-[1600px] mx-auto pb-2 font-sans px-3 sm:px-4 pt-2 relative">
        {/* ── SECTION 1: THE BRIEF CARD ── */}
        <BriefCard data={briefData} isLoading={overviewLoading && !briefData} />

        {/* ── SECTION 2: METRICS/KPI + ACTIONS (tinted fill, no frame) ── */}
        <div className="bg-[#f1f5f9]/35 dark:bg-slate-800/30 border border-[#e2e8f0] dark:border-slate-800 rounded-2xl p-4 sm:p-5 space-y-5">
          {/* ── Metrics & KPI block ── */}
          <div ref={kpiBlockRef} className="space-y-3">
          {selectedMainKpi === null ? (
            /* STATE A: DEFAULT VIEW — 5 MAIN KPI CARDS AT TOP */
            <div>
              <div className="flex items-center justify-end gap-3 w-full mb-2.5">
                {renderTopControls('state_a')}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {mainKpiCards.map((kpi) => (
                  <div
                    key={kpi.key}
                    onClick={() => selectDomain(kpi.key)}
                    style={kpiCardStyle(kpi.isPositive)}
                    className="rounded-2xl p-4 flex flex-col justify-between transition-all cursor-pointer shadow-2xs group"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-xs font-semibold text-gray-500 dark:text-slate-400 truncate">
                        {kpi.title}
                      </span>
                    </div>

                    <div className="my-1.5">
                      <p className="text-[20px] font-bold tracking-tight text-gray-900 dark:text-white leading-none">
                        {kpi.value}
                      </p>
                    </div>

                    <div className="flex items-center justify-between gap-1 text-[11px]">
                      <span className="text-gray-400 dark:text-slate-500 truncate">
                        {kpi.subtext}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* STATE B: CARD CLICKED VIEW — PILL TABS + SUB KPIS */
            <div className="space-y-3.5 animate-in fade-in duration-200">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 dark:border-slate-800/80 pb-3">
                <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto scrollbar-hide py-0.5">
                  {MAIN_TABS.map((tab) => {
                    const isSelected = activeDomain === tab.key;
                    return (
                      <button
                        key={tab.key}
                        onClick={() => {
                          if (isSelected && selectedMainKpi) {
                            setSelectedMainKpi(null);
                          } else {
                            selectDomain(tab.key);
                          }
                        }}
                        className={`px-4 py-1.5 text-xs font-bold rounded-xl transition-all whitespace-nowrap ${
                          isSelected
                            ? 'bg-[#18181B] dark:bg-slate-100 text-white dark:text-gray-900 shadow-xs'
                            : 'bg-transparent text-gray-500 hover:text-gray-900 dark:text-slate-400 dark:hover:text-slate-100'
                        }`}
                      >
                        {tab.label}
                      </button>
                    );
                  })}
                </div>

                {renderTopControls('state_b')}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {currentSubStats.map((stat, i) => {
                  return (
                    <div
                      key={i}
                      style={kpiCardStyle(stat.isPositive)}
                      className="rounded-2xl p-4 flex flex-col justify-between transition-all"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-xs font-semibold text-gray-500 dark:text-slate-400 truncate">
                          {stat.title}
                        </span>
                      </div>

                      <div className="my-1.5">
                        <p className="text-[20px] font-bold tracking-tight text-gray-900 dark:text-white leading-none">
                          {stat.value}
                        </p>
                      </div>

                      <div className="flex items-center justify-between gap-1 text-[11px]">
                        <span className="text-gray-400 dark:text-slate-500 truncate" title={stat.subtext}>
                          {stat.subtext}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          </div>

          {/* ── Actions (white table box, nested inside upper section) ── */}
          <div className="bg-white dark:bg-slate-900 border border-[#e2e8f0] dark:border-slate-800 rounded-2xl p-4 sm:p-5">
          {/* One grid for the whole card, so the simulation panel starts on the
              same row as the "Actions" heading rather than below the filter bar. */}
          <div
            className={`grid transition-all duration-300 gap-4 lg:gap-5 items-start ${
              isExpanded ? 'grid-cols-1 lg:grid-cols-[1.25fr_1fr]' : 'grid-cols-1'
            }`}
          >
          <div className="min-w-0 space-y-3">
          <div className="flex flex-col gap-3">
            <div className="flex items-baseline gap-2">
              <h3 className="text-base font-bold text-gray-900 dark:text-white tracking-tight">
                Actions
              </h3>
              <span className="text-xs text-gray-400 dark:text-slate-500 font-normal">
                • {sortedSignals.length} signals
              </span>
            </div>

            <div className="flex items-center justify-between gap-3 flex-wrap py-0.5 relative z-30 w-full" ref={filterBarRef}>
              
              <div className="flex items-center gap-2 flex-wrap">
              <FilterSelect
                label="Category"
                value={categoryCut}
                options={CATEGORY_OPTIONS}
                onChange={setCategoryCut}
                multiple
                isOpen={openDropdown === 'category'}
                onToggle={() => toggleDropdown('category')}
                width="w-[160px]"
              />

              <FilterSelect
                label="Channel"
                value={marketplace}
                options={CHANNEL_OPTIONS}
                onChange={setMarketplace}
                multiple
                isOpen={openDropdown === 'channel'}
                onToggle={() => toggleDropdown('channel')}
                width="w-[140px]"
              />

              <FilterSelect
                label="Status"
                value={statusFilter}
                options={STATUS_OPTIONS}
                onChange={setStatusFilter}
                multiple
                isOpen={openDropdown === 'status'}
                onToggle={() => toggleDropdown('status')}
                width="w-[150px]"
              />

              {/* Ads-only: which ad platform the campaigns ran on. */}
              {isAdsDomain && (
                <FilterSelect
                  label="Advertising"
                  value={adPlatform}
                  options={AD_PLATFORM_OPTIONS}
                  onChange={(v) => { setAdPlatform(v); setOpenDropdown(null); }}
                  isOpen={openDropdown === 'advertising'}
                  onToggle={() => toggleDropdown('advertising')}
                  width="w-[170px]"
                />
              )}

              {/* Inventory-only filters */}
              {isInventoryDomain && (
                <>
                  <FilterSelect
                    label="Fulfillment Type"
                    value={fulfillmentType}
                    options={FULFILLMENT_OPTIONS}
                    onChange={(v) => { setFulfillmentType(v); setOpenDropdown(null); }}
                    isOpen={openDropdown === 'fulfillment'}
                    onToggle={() => toggleDropdown('fulfillment')}
                    width="w-[170px]"
                  />
                  <FilterSelect
                    label="Stockout Time"
                    value={stockoutTime}
                    options={STOCKOUT_OPTIONS}
                    onChange={(v) => { setStockoutTime(v); setOpenDropdown(null); }}
                    isOpen={openDropdown === 'stockout'}
                    onToggle={() => toggleDropdown('stockout')}
                    width="w-[160px]"
                  />
                  <FilterSelect
                    label="Confidence"
                    value={confidence}
                    options={CONFIDENCE_OPTIONS}
                    onChange={(v) => { setConfidence(v); setOpenDropdown(null); }}
                    isOpen={openDropdown === 'confidence'}
                    onToggle={() => toggleDropdown('confidence')}
                    width="w-[140px]"
                  />
                </>
              )}

              {/* Cash-only filters */}
              {isCashDomain && (
                <>
                  <FilterSelect
                    label="Urgency"
                    value={urgency}
                    options={URGENCY_OPTIONS}
                    onChange={(v) => { setUrgency(v); setOpenDropdown(null); }}
                    isOpen={openDropdown === 'urgency'}
                    onToggle={() => toggleDropdown('urgency')}
                    width="w-[140px]"
                  />
                  <FilterSelect
                    label="Cash Direction"
                    value={cashDirection}
                    options={CASH_DIRECTION_OPTIONS}
                    onChange={(v) => { setCashDirection(v); setOpenDropdown(null); }}
                    isOpen={openDropdown === 'cashDirection'}
                    onToggle={() => toggleDropdown('cashDirection')}
                    width="w-[180px]"
                  />
                </>
              )}

              {/* SKU Filter (Custom Popover) */}
              <SkuFilterPopover
                value={skuFilter}
                actionOptions={actionOptions}
                onApply={setSkuFilter}
                isOpen={openDropdown === 'sku'}
                onToggle={() => toggleDropdown('sku')}
                onClose={() => setOpenDropdown(null)}
              />

              </div>

              <div className="flex items-center gap-2 flex-wrap ml-auto">
              {/* Time Range Selector (Custom Popover) */}
              <DateFilterSelect
                timeRange={timeRange}
                setTimeRange={setTimeRange}
                isOpen={openDropdown === 'date'}
                onToggle={() => toggleDropdown('date')}
                onClose={() => setOpenDropdown(null)}
              />
              </div>
            </div>
          </div>

            {/* Flat Actions Table */}
            <div className="overflow-hidden">
              <SignalsTable
                signals={sortedSignals}
                selectedId={expandedInsight?.id}
                onSelect={(sig) => {
                  setExpandedInsight(expandedInsight?.id === sig.id ? null : sig);
                  setPanelTab('reasons');
                }}
                onSimulate={handleSimulateClick}
                onTakeAction={handleTakeAction}
                isCollapsed={isExpanded}
                isFiltered={isAnyFilterActive}
                onClearFilters={clearAllFilters}
                executedSignalIds={executedSignalIds}
                /* Must match the key the rows came from, or Ads rows render
                   against another domain's columns. */
                activeDomain={currentDomainKey}
              />
            </div>
          </div>
          {/* ── end left column ── */}

            {isExpanded && (
              /*
               * The panel already scrolls internally (h-full > flex-1 min-h-0 >
               * overflow-y-auto), but that only engages against a definite
               * height — in an auto-height grid row it just stretched and the
               * whole page scrolled instead.
               *
               * Bounding it to the viewport turns the internal scroll on, and
               * sticky keeps it in place while the Actions table scrolls beside
               * it. The subtraction covers the app header, the sticky offset and
               * the fixed AI prompt bar at the bottom. Only from `lg`, where the
               * split view exists — stacked below that, page scroll is right.
               */
              <div className="overflow-hidden animate-in fade-in slide-in-from-right-4 duration-300">
                <InsightDetailsPanel
                  insight={expandedInsight}
                  activePanelTab={panelTab}
                  onTabChange={setPanelTab}
                  onClose={() => setExpandedInsight(null)}
                />
              </div>
            )}
          </div>
          </div>
        </div>
      </div>

      <DismissModal
        isOpen={isDismissModalOpen}
        onClose={() => setIsDismissModalOpen(false)}
      />
      <RepriceModal
        isOpen={isRepriceModalOpen}
        onClose={() => setIsRepriceModalOpen(false)}
      />
      <CaseReportModal
        isOpen={isCaseReportModalOpen}
        onClose={() => setIsCaseReportModalOpen(false)}
      />
    </DashboardLayout>
  );
};

export default WorkspacePage;
