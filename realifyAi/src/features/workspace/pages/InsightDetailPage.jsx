import React, { useState, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import {
  INSIGHTS_DATA,
  MARGIN_INSIGHTS_DATA,
  INVENTORY_INSIGHTS_DATA,
  ADS_INSIGHTS_DATA,
  CASH_INSIGHTS_DATA,
} from '@/data/workspaceData';
import { SimulateModal } from '@/features/workspace/modules/simulation';
import { getInsightActionButtons } from '@/features/workspace/utils/insightActionMapper';

const INSIGHTS_BY_INTEL_TAB = {
  sales: INSIGHTS_DATA,
  margin: MARGIN_INSIGHTS_DATA,
  inventory: INVENTORY_INSIGHTS_DATA,
  ads: ADS_INSIGHTS_DATA,
  cash: CASH_INSIGHTS_DATA,
};
import CustomActionModal from '@/components/overlays/CustomActionModal';
import { DEFAULT_DOMAIN, insightPath, toDomainKey, workspacePath } from '@/features/workspace/workspaceRoutes';
import { ROUTES } from '@/constants/routes';



const WORKSPACE_LABELS = {
  sales: 'Sales',
  margin: 'Margin',
  inventory: 'Inventory',
  cash: 'Cash',
  ads: 'Ads',
};

const STEP_TYPE_META = {
  CRITICAL: { bg: 'bg-red-100 dark:bg-red-900/30', color: 'text-red-600 dark:text-red-400' },
  HIGH: { bg: 'bg-amber-100 dark:bg-amber-900/30', color: 'text-amber-600 dark:text-amber-400' },
  OPPORTUNITY: { bg: 'bg-green-100 dark:bg-green-900/30', color: 'text-green-600 dark:text-green-400' },
  INSIGHT: { bg: 'bg-blue-100 dark:bg-blue-900/30', color: 'text-blue-600 dark:text-blue-400' },
  MARKET: { bg: 'bg-purple-100 dark:bg-purple-900/30', color: 'text-purple-600 dark:text-purple-400' },
  PAYMENT: { bg: 'bg-orange-100 dark:bg-orange-900/30', color: 'text-orange-600 dark:text-orange-400' },
};

const INSIGHT_TYPE_META = {
  CRITICAL: { bg: 'bg-red-100 dark:bg-red-900/30', color: 'text-red-600 dark:text-red-400' },
  OPPORTUNITY: { bg: 'bg-green-100 dark:bg-green-900/30', color: 'text-green-600 dark:text-green-400' },
  INSIGHT: { bg: 'bg-blue-100 dark:bg-blue-900/30', color: 'text-blue-600 dark:text-blue-400' },
  MARKET: { bg: 'bg-purple-100 dark:bg-purple-900/30', color: 'text-purple-600 dark:text-purple-400' },
  REVIEW: { bg: 'bg-amber-100 dark:bg-amber-900/30', color: 'text-amber-600 dark:text-amber-400' },
  ALERT: { bg: 'bg-orange-100 dark:bg-orange-900/30', color: 'text-orange-600 dark:text-orange-400' },
};

const PRIORITY_FILTERS = ['All', 'High', 'Medium', 'Low'];

const TAB_STEP_METRIC = {
  sales: (id) => ({ label: 'Price', value: `$${(149.99 - ((id - 1) % 3) * 14.50).toFixed(2)}` }),
  margin: (id) => ({ label: 'Margin', value: `${(58.2 - ((id - 1) % 3) * 4.8).toFixed(1)}%` }),
  inventory: (id) => ({ label: 'Stock', value: `${47 - ((id - 1) % 3) * 11} units` }),
  ads: (id) => ({ label: 'Ad Budget', value: `$${850 - ((id - 1) % 3) * 135}` }),
  cash: (id) => ({ label: 'Revenue', value: `$${(8.4 - ((id - 1) % 3) * 0.9).toFixed(1)}k` }),
};

const STEP_METRICS = {
  CRITICAL: [
    { label: 'Risk Level', value: 'High', color: 'text-red-600 dark:text-red-400' },
    { label: 'Est. Revenue Saved', value: '+$12,400', color: 'text-green-600 dark:text-green-400' },
    { label: 'Time Sensitivity', value: '< 24h', color: 'text-red-600 dark:text-red-400' },
    { label: 'Confidence', value: '94%', color: 'text-blue-600 dark:text-blue-400' },
  ],
  HIGH: [
    { label: 'Est. Revenue Gain', value: '+$8,200', color: 'text-green-600 dark:text-green-400' },
    { label: 'Effort Level', value: 'Medium', color: 'text-amber-600 dark:text-amber-400' },
    { label: 'Time to Execute', value: '2–3 days', color: 'text-gray-700 dark:text-slate-300' },
    { label: 'Confidence', value: '88%', color: 'text-blue-600 dark:text-blue-400' },
  ],
  OPPORTUNITY: [
    { label: 'Market Opportunity', value: '+$18,400', color: 'text-green-600 dark:text-green-400' },
    { label: 'Est. ROAS', value: '5.2x', color: 'text-blue-600 dark:text-blue-400' },
    { label: 'Upside Potential', value: 'High', color: 'text-green-600 dark:text-green-400' },
    { label: 'Confidence', value: '82%', color: 'text-blue-600 dark:text-blue-400' },
  ],
  INSIGHT: [
    { label: 'Data Points', value: '47', color: 'text-gray-700 dark:text-slate-300' },
    { label: 'Impact Score', value: '7.4 / 10', color: 'text-blue-600 dark:text-blue-400' },
    { label: 'Confidence', value: '91%', color: 'text-blue-600 dark:text-blue-400' },
    { label: 'Time to Action', value: '3–5 days', color: 'text-gray-700 dark:text-slate-300' },
  ],
  MARKET: [
    { label: 'Market Reach', value: '2.4 M', color: 'text-purple-600 dark:text-purple-400' },
    { label: 'Competitive Index', value: 'High', color: 'text-amber-600 dark:text-amber-400' },
    { label: 'Confidence', value: '86%', color: 'text-blue-600 dark:text-blue-400' },
    { label: 'Window', value: '5–9 days', color: 'text-gray-700 dark:text-slate-300' },
  ],
  PAYMENT: [
    { label: 'Est. Savings', value: '+$4,200', color: 'text-green-600 dark:text-green-400' },
    { label: 'Outstanding', value: '$18,400', color: 'text-red-600 dark:text-red-400' },
    { label: 'Confidence', value: '95%', color: 'text-blue-600 dark:text-blue-400' },
    { label: 'Processing Time', value: '1–2 days', color: 'text-gray-700 dark:text-slate-300' },
  ],
};

const STEP_OUTCOMES = {
  CRITICAL: [
    'Buy box recovery expected within 24–48 hours of execution',
    'Revenue leakage minimised — estimated $12,400 protected this week',
    'Auto-pricing rules prevent recurrence for affected SKUs',
  ],
  HIGH: [
    'Performance improvement visible within 3–5 days',
    'Estimated +8% revenue uplift across affected SKUs',
    'Reduced manual monitoring load post-execution',
  ],
  OPPORTUNITY: [
    'Revenue uplift of $14,000–$22,000 over the next 14 days',
    'Market share gains in target channels expected',
    'ROAS of 5.0× or higher projected within first 7 days',
  ],
  INSIGHT: [
    'Better data visibility for future decision-making',
    'Operational friction reduced across the affected workflow',
    'Long-term efficiency improvement of ~12% in this area',
  ],
  MARKET: [
    'Market positioning improved vs top 3 competitors',
    'Brand visibility increase across target channels',
    'Competitive intelligence gap reduced significantly',
  ],
  PAYMENT: [
    'Cash flow optimised — payment cycle shortened by up to 3 days',
    'Fee recovery of ~$4,200 from identified discrepancies',
    'Improved settlement reconciliation accuracy',
  ],
};

const getStepMetrics = (type) => STEP_METRICS[type] || STEP_METRICS.INSIGHT;
const getStepOutcomes = (type) => STEP_OUTCOMES[type] || STEP_OUTCOMES.INSIGHT;

const getImplementationPlan = (step) => {
  if (!step) return 'Execute the recommended steps in priority order. Monitor key metrics over the next 48 hours and adjust based on performance data.';
  const { type, title } = step;
  if (type === 'CRITICAL') return `Escalate "${title}" immediately. Assign ownership within 2 hours and set up hourly metric monitoring. Prepare a rollback plan in case performance deviates from target.`;
  if (type === 'HIGH') return `Prioritise "${title}" in your next sprint. Brief the relevant team and validate results against projected impact after 72 hours.`;
  if (type === 'OPPORTUNITY') return `Capture the "${title}" opportunity within the current window. Allocate budget and resources, track leading indicators daily, and scale up if early signals are positive within 48 hours.`;
  if (type === 'MARKET') return `Act on "${title}" before the competitive window closes. Brief marketing and pricing teams; set weekly review cadences to track market response.`;
  return `Implement "${title}" as a measured action. Monitor key metrics over the next 48 hours and adjust based on performance data.`;
};

const getGuardrails = (step) => {
  const type = step?.type;
  if (type === 'CRITICAL') return 'Set price floor rules before any repricing. Monitor buy box and margin every 2 hours. Halt if gross margin drops below 20%. Ensure a rollback plan is ready.';
  if (type === 'OPPORTUNITY') return 'Cap spend increases at 30% per day to avoid overspend. Confirm stock cover before scaling demand. Set a ROAS minimum alert at 3.0×.';
  if (type === 'HIGH') return 'Confirm resource availability before starting. Set clear success metrics for the 72-hour checkpoint. Flag any unexpected dependency on third-party systems or suppliers.';
  return 'Proceed carefully and monitor for unintended side effects. Stop or pause if key metrics deviate beyond acceptable thresholds. Maintain rollback capability throughout execution.';
};

const IntelV2InsightDetailPage = () => {
  const topRef = useRef(null);
  const { domain: domainSegment, idx } = useParams();
  // URLs carry the product vocabulary ('revenue'); datasets are keyed 'sales'.
  const domain = toDomainKey(domainSegment);
  const navigate = useNavigate();
  const location = useLocation();

  const stateData = location.state;
  const stateInsights = stateData?.insights || [];
  const stateDomain = stateData?.domain || domain || DEFAULT_DOMAIN;

  const currentIndex = parseInt(idx ?? 0);
  const insight = stateInsights[currentIndex];

  const [selectedStepId, setSelectedStepId] = useState(null);
  const [isCustomActionOpen, setIsCustomActionOpen] = useState(false);
  const [isSimulateModalOpen, setIsSimulateModalOpen] = useState(false);
  const [simulateSku, setSimulateSku] = useState(null);

  // First step selected by default; use initialStepId when arriving from product page
  const [prevLocationKey, setPrevLocationKey] = useState(location.key);
  if (location.key !== prevLocationKey) {
    setPrevLocationKey(location.key);
    const initId = stateData?.initialStepId ?? insight?.steps?.[0]?.id ?? null;
    setSelectedStepId(initId);
  }

  if (!insight) {
    return (
      <DashboardLayout title="Intelligence" showSearch={false} showTabs={false}>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400 dark:text-slate-500 text-sm">Insight not found.</p>
        </div>
      </DashboardLayout>
    );
  }

  const allSteps = insight.steps || [];
  const selectedStep = selectedStepId !== null ? allSteps.find(s => s.id === selectedStepId) : null;
  const insightMeta = INSIGHT_TYPE_META[insight.type] || INSIGHT_TYPE_META.INSIGHT;
  const recId = `REC-${8000 + currentIndex * 100 + 71}`;

  const handleBack = () => {
    const route = stateData?.sourceRoute || workspacePath(stateDomain) || ROUTES.WORKSPACE;
    if (route === '/product-view' && stateData?.productViewState) {
      navigate(route, { state: stateData.productViewState });
    } else {
      navigate(route, { state: { restoreInsightTab: stateData?.insightTab, restoreItemSubTab: stateData?.itemSubTab } });
    }
  };

  return (
    <DashboardLayout
      title="Intelligence"
      subtitle="Real-time sales analytics"
      showSearch={false}
      showTabs={false}
    >
      <div ref={topRef} />
      {/* Back button */}
      <div className="flex items-center -mt-2 pb-4">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors"
        >
          <i className="fa-solid fa-arrow-left text-sm" />
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 lg:h-[calc(100vh-11rem)]">

        {/* Left: Insight Detail — scrollable */}
        <div className="flex-1 min-w-0 overflow-y-auto custom-scrollbar pr-1 pb-4">

          {/* Main insight card */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">

            {/* Card header: type badge + id + time only */}
            <div className="flex items-center gap-2 flex-wrap mb-3 pb-3 border-b border-gray-100 dark:border-slate-800">
              <span className={`px-2.5 py-1 text-[10px] rounded-lg font-bold uppercase tracking-wider ${insightMeta.bg} ${insightMeta.color}`}>
                {insight.type === 'HIGH' ? 'HIGH IMPACT' : insight.type}
              </span>
              {stateData?.executed && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400">
                  <i className="fa-solid fa-circle-check text-[9px]" /> EXECUTED
                </span>
              )}
              <span className="text-xs text-gray-400 dark:text-slate-500 font-sans">#{recId}</span>
              <span className="text-gray-300 dark:text-slate-700">·</span>
              <span className="text-xs text-gray-500 dark:text-slate-400">{insight.time}</span>
            </div>
            {stateData?.executed && stateData?.executedAt && (
              <div className="mb-4 flex items-center gap-2 px-3 py-2.5 rounded-xl bg-green-50 dark:bg-green-900/15 border border-green-200 dark:border-green-800/40">
                <i className="fa-solid fa-circle-check text-green-500 text-sm flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-green-700 dark:text-green-400">Action Executed</p>
                  <p className="text-[11px] text-green-600/80 dark:text-green-500/80 mt-0.5">Completed on {stateData.executedAt}</p>
                </div>
              </div>
            )}

            {/* Heading */}
            <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100 leading-snug mb-4">
              {insight.heading}
            </h2>

            <div className="space-y-4">
              {/* Analysis Insights */}
              <div>
                <h5 className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-2 flex items-center gap-2">
                  <i className="fa-solid fa-lightbulb" /> ANALYSIS INSIGHTS
                </h5>
                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-xl p-4 border border-gray-100 dark:border-slate-800">
                  {/* Fix 2: no bold/font-semibold on body text */}
                  <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">
                    {insight.body}
                  </p>
                </div>
              </div>

              {/* Action Details — shown when step is selected from sidebar */}
              {selectedStep && (() => {
                const sMeta = STEP_TYPE_META[selectedStep.type] || STEP_TYPE_META.INSIGHT;
                const sLabel = selectedStep.type === 'HIGH' ? 'HIGH IMPACT' : selectedStep.type;
                return (
                  <div>
                    <h5 className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-2 flex items-center gap-2">
                      <i className="fa-solid fa-bolt" /> ACTION DETAILS
                    </h5>
                    <div className="border border-gray-200 dark:border-slate-700 rounded-xl p-4">
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded-md ${sMeta.bg} ${sMeta.color}`}>
                            {sLabel}
                          </span>
                          <span className="text-[9px] text-gray-400 dark:text-slate-500 font-sans">
                            #REC-{8000 + currentIndex * 100 + (typeof selectedStep.id === 'number' ? selectedStep.id * 47 : 71)}
                          </span>
                          <span className="text-gray-300 dark:text-slate-700">·</span>
                          <span className="text-[9px] text-gray-500 dark:text-slate-400">5 min ago</span>
                        </div>
                      </div>
                      <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-3 leading-snug">
                        {selectedStep.title}
                      </h4>
                      <div className="mb-3">
                        <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5 flex items-center gap-1">
                          <i className="fa-solid fa-lightbulb text-[8px]" /> Analysis Insights
                        </p>
                        <p className="text-xs text-gray-700 dark:text-slate-300 leading-relaxed">
                          {selectedStep.sub}
                        </p>
                      </div>
                      <div className="mb-3">
                        <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5 flex items-center gap-1">
                          <i className="fa-solid fa-chart-line text-[8px]" /> Key Metrics
                        </p>
                        <div className="grid grid-cols-2 gap-1.5">
                          {getStepMetrics(selectedStep.type).map((m, i) => (
                            <div key={i} className="p-2 rounded-lg border border-gray-100 dark:border-slate-800 bg-gray-50/40 dark:bg-slate-900/30">
                              <p className="text-[9px] text-gray-400 dark:text-slate-500 mb-0.5">{m.label}</p>
                              <p className={`text-sm font-bold ${m.color}`}>{m.value}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5 flex items-center gap-1">
                          <i className="fa-solid fa-circle-check text-[8px]" /> Expected Outcomes
                        </p>
                        <ul className="space-y-1.5">
                          {getStepOutcomes(selectedStep.type).map((outcome, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-gray-700 dark:text-slate-300 leading-relaxed">
                              <span className="mt-1 w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                              {outcome}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Implementation Plan — contextual based on selected step */}
              <div>
                <h5 className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-2 flex items-center gap-2">
                  <i className="fa-solid fa-rocket" /> IMPLEMENTATION PLAN
                </h5>
                <div className="bg-green-50/40 dark:bg-green-900/10 rounded-xl p-4 border border-green-100/60 dark:border-green-900/30">
                  <p className="text-sm text-green-900 dark:text-green-300 leading-relaxed">
                    {getImplementationPlan(selectedStep)}
                  </p>
                </div>
              </div>

              {/* Guardrails & Risks — contextual based on selected step */}
              <div>
                <h5 className="text-[10px] font-bold text-orange-500 dark:text-orange-400 tracking-widest mb-2 flex items-center gap-2">
                  <i className="fa-solid fa-shield-halved" /> GUARDRAILS &amp; RISKS
                </h5>
                <div className="bg-orange-50/30 dark:bg-orange-900/10 rounded-xl p-4 border border-orange-100/50 dark:border-orange-900/20">
                  <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed italic">
                    {getGuardrails(selectedStep)}
                  </p>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Right: Execute / Simulate panel */}
        <aside className="hidden lg:flex flex-col w-64 shrink-0 mt-6 sticky top-6 gap-3">
          {/* Primary CTA card */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-4 flex flex-col gap-3">
            {stateData?.executed ? (
              <>
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/40">
                  <i className="fa-solid fa-circle-check text-green-500 text-sm" />
                  <div>
                    <p className="text-xs font-bold text-green-700 dark:text-green-400">Executed</p>
                    {stateData?.executedAt && <p className="text-[10px] text-green-600/70 dark:text-green-500/70">{stateData.executedAt}</p>}
                  </div>
                </div>
                <button
                  onClick={() => navigate(ROUTES.WORKSPACE_ROLLBACK, {
                    state: {
                      insight,
                      domain: stateDomain,
                      executedAt: stateData?.executedAt,
                      backState: location.state,
                    },
                  })}
                  className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-bold text-sm transition-all active:scale-[0.98] flex items-center justify-center gap-2 shadow"
                >
                  <i className="fa-solid fa-rotate-left text-[11px]" /> Roll Back
                </button>
              </>
            ) : (
              <>
                {getInsightActionButtons(selectedStep || insight).map((btn, i) => (
                  <button
                    key={i}
                    className={`w-full py-3 rounded-xl font-bold text-sm transition-all active:scale-[0.98] flex items-center justify-center gap-2 shadow ${
                      btn.primary
                        ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 hover:opacity-90'
                        : 'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <i className="fa-solid fa-bolt text-[11px]" /> {btn.label}
                  </button>
                ))}
                <button
                  onClick={() => {
                    setSimulateSku(insight.sku || 'AFWCLEANER0004');
                    setIsSimulateModalOpen(true);
                  }}
                  className="w-full py-3 bg-gray-50 dark:bg-slate-800 text-gray-700 dark:text-slate-200 rounded-xl font-bold text-sm border border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-700 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                >
                  <i className="fa-solid fa-flask-vial text-[11px]" /> Simulate
                </button>
              </>
            )}
          </div>

          {/* Other insights quick-access list */}
          {stateInsights.filter((_, i) => i !== currentIndex).length > 0 && (
            <div>
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2 px-1 flex items-center gap-1.5">
                <i className="fa-solid fa-list text-[9px]" /> Other Insights
              </p>
              <div className="flex flex-col divide-y divide-gray-200 dark:divide-slate-700/60">
                {stateInsights
                  .map((ins, i) => ({ ins, i }))
                  .filter(({ i }) => i !== currentIndex)
                  .map(({ ins, i }, listIdx) => (
                    <button
                      key={i}
                      onClick={() => navigate(insightPath(stateDomain, i), { state: { ...stateData, currentIndex: i } })}
                      className="text-left w-full px-2 py-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800/60 transition-colors group flex items-start gap-2"
                    >
                      <span className="flex-shrink-0 text-[10px] font-semibold text-gray-400 dark:text-slate-500 mt-0.5 w-3.5">{listIdx + 1}.</span>
                      <span className="text-[13px] font-medium text-gray-700 dark:text-slate-300 leading-snug group-hover:text-gray-900 dark:group-hover:text-slate-100 truncate">
                        {ins.heading}
                      </span>
                    </button>
                  ))}
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* MOBILE: Execute/Simulate + Other Insights — shown at the bottom of the page; desktop keeps the sticky sidebar above */}
      <div className="lg:hidden flex flex-col gap-3 mt-4">
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-4 flex flex-col gap-3">
          {stateData?.executed ? (
            <>
              <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/40">
                <i className="fa-solid fa-circle-check text-green-500 text-sm" />
                <div>
                  <p className="text-xs font-bold text-green-700 dark:text-green-400">Executed</p>
                  {stateData?.executedAt && <p className="text-[10px] text-green-600/70 dark:text-green-500/70">{stateData.executedAt}</p>}
                </div>
              </div>
              <button
                onClick={() => navigate(ROUTES.WORKSPACE_ROLLBACK, {
                  state: {
                    insight,
                    domain: stateDomain,
                    executedAt: stateData?.executedAt,
                    backState: location.state,
                  },
                })}
                className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-bold text-sm transition-all active:scale-[0.98] flex items-center justify-center gap-2 shadow"
              >
                <i className="fa-solid fa-rotate-left text-[11px]" /> Roll Back
              </button>
            </>
          ) : (
            <>
              {getInsightActionButtons(selectedStep || insight).map((btn, i) => (
                <button
                  key={i}
                  className={`w-full py-3 rounded-xl font-bold text-sm transition-all active:scale-[0.98] flex items-center justify-center gap-2 shadow ${
                    btn.primary
                      ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 hover:opacity-90'
                      : 'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                  }`}
                >
                  <i className="fa-solid fa-bolt text-[11px]" /> {btn.label}
                </button>
              ))}
              <button
                onClick={() => {
                  setSimulateSku(insight.sku || 'AFWCLEANER0004');
                  setIsSimulateModalOpen(true);
                }}
                className="w-full py-3 bg-gray-50 dark:bg-slate-800 text-gray-700 dark:text-slate-200 rounded-xl font-bold text-sm border border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-700 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
              >
                <i className="fa-solid fa-flask-vial text-[11px]" /> Simulate
              </button>
            </>
          )}
        </div>

        {stateInsights.filter((_, i) => i !== currentIndex).length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2 px-1 flex items-center gap-1.5">
              <i className="fa-solid fa-list text-[9px]" /> Other Insights
            </p>
            <div className="flex flex-col divide-y divide-gray-200 dark:divide-slate-700/60 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl px-2">
              {stateInsights
                .map((ins, i) => ({ ins, i }))
                .filter(({ i }) => i !== currentIndex)
                .map(({ ins, i }, listIdx) => (
                  // <button
                  //   key={i}
                  //   onClick={() => navigate(insightPath(stateDomain, i), { state: { ...stateData, currentIndex: i } })}
                  //   className="text-left w-full px-2 py-2.5 hover:bg-gray-100 dark:hover:bg-slate-800/60 transition-colors group flex items-start gap-2"
                  // >
                  <button
                    key={i}
                    onClick={() => {
                      navigate(insightPath(stateDomain, i), { state: { ...stateData, currentIndex: i } });
                      topRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }}
                    className="text-left w-full px-2 py-2.5 hover:bg-gray-100 dark:hover:bg-slate-800/60 transition-colors group flex items-start gap-2"
                  >
                    <span className="flex-shrink-0 text-[10px] font-semibold text-gray-400 dark:text-slate-500 mt-0.5 w-3.5">{listIdx + 1}.</span>
                    <span className="text-[13px] font-medium text-gray-700 dark:text-slate-300 leading-snug group-hover:text-gray-900 dark:group-hover:text-slate-100 truncate">
                      {ins.heading}
                    </span>
                  </button>
                ))}
            </div>
          </div>
        )}
      </div>

      <CustomActionModal isOpen={isCustomActionOpen} onClose={() => setIsCustomActionOpen(false)} />
      <SimulateModal isOpen={isSimulateModalOpen} onClose={() => setIsSimulateModalOpen(false)} sku={simulateSku} />
    </DashboardLayout>
  );
};

export default IntelV2InsightDetailPage;
