import React, { useState } from 'react';
import { useWorkspaceFilterStore } from '@/store/useWorkspaceFilterStore';
import { useScrollIntoViewOnChange } from '@/hooks/useScrollIntoViewOnChange';
import { getSimulation } from '@/data/simulationData';

/* Clears the sticky compact KPI ribbon, which pins over the top of the scroll
   area — scrolling the panel flush to the top would tuck its title under it. */
const STICKY_HEADER_OFFSET = 76;

/**
 * The wizard's four steps, in order. Declared once so the header stepper, the
 * footer's "Step N of 4" line and the Back/Continue targets can never disagree
 * about the sequence.
 */
const STEPS = [
  { id: 'reasons', num: 1, label: 'Reason' },
  { id: 'analysis', num: 2, label: 'Analyze' },
  { id: 'decision', num: 3, label: 'Decide' },
  { id: 'confirm', num: 4, label: 'Confirm' },
];

/**
 * Level 2: the Simulation panel for a single Action.
 *
 * Four steps in one container — Reason → Analyze → Decide → Confirm — with the
 * inactive steps unmounted rather than hidden. Every value it renders comes from
 * `getSimulation(insight)`, so the panel is pure presentation and the copy for
 * each action lives in src/data/simulationData.js.
 */
const InsightDetailsPanel = ({
  insight,
  activePanelTab = 'reasons',
  onTabChange,
  onClose,
}) => {
  const [internalTab, setInternalTab] = useState('reasons');
  const [isApplyingAction, setIsApplyingAction] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(false);
  const [isAgentTraceOpen, setIsAgentTraceOpen] = useState(false);
  const [openSimulationAccordion, setOpenSimulationAccordion] = useState(0);
  const markSignalExecuted = useWorkspaceFilterStore((state) => state.markSignalExecuted);

  /* Each step is a different height, so advancing from a tall one leaves the
     page scrolled past this panel's title — the user lands mid-step with no
     idea which step they are on. Keyed on the tab so it re-runs per step.
     Declared before the early return: hook order has to be stable. */
  const panelRef = useScrollIntoViewOnChange(activePanelTab, { offset: STICKY_HEADER_OFFSET });

  if (!insight) return null;

  // Every piece of copy and every number in this panel belongs to the action the
  // row opened — see src/data/simulationData.js.
  const sim = getSimulation(insight);

  // Use controlled activePanelTab if passed, else internalTab
  const activeTab = activePanelTab || internalTab;

  // Position in the wizard, derived once and used by the footer.
  const stepIndex = Math.max(0, STEPS.findIndex((s) => s.id === activeTab));
  const isFirstStep = stepIndex === 0;
  const isLastStep = stepIndex === STEPS.length - 1;

  const handleSwitchTab = (tab) => {
    if (onTabChange) onTabChange(tab);
    setInternalTab(tab);
  };

  /**
   * Confirm & execute.
   *
   * The success screen is terminal: it carries the reference code the user needs
   * to quote, so it stays up until they close the panel. It used to revert to
   * the Confirm step after 1.2s, which both stole the reference code and made it
   * look like the action had not gone through.
   */
  const handleConfirmInlineAction = () => {
    setIsApplyingAction(true);
    if (insight?.id) markSignalExecuted(insight.id);
    setTimeout(() => {
      setIsApplyingAction(false);
      setActionSuccess(true);
    }, 600);
  };

  return (
    <div ref={panelRef} className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-card dark:shadow-none font-sans">

      {/* ── 1. TOP HEADER & STEPPER ── */}
      <div className="bg-white dark:bg-slate-900 flex flex-col flex-shrink-0">
        <div className="px-6 pt-5 pb-3 flex items-start justify-between gap-4">
          <h3 className="text-[18px] font-bold text-gray-900 dark:text-white tracking-tight leading-snug">
            {sim.title.prefix}{' '}
            {sim.title.highlight && <span className="text-red-500">{sim.title.highlight}</span>}
          </h3>
          {onClose && (
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0 mt-0.5 ml-auto">
              <i className="fa-solid fa-xmark text-[16px]" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 mb-4 pl-6 flex-wrap">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${sim.chips.channel.className}`}>
            <i className={`${sim.chips.channel.icon} text-[11px]`} />
            {sim.chips.channel.label}
          </span>
          {[sim.chips.category, sim.chips.sku].filter(Boolean).map((chip) => (
            <span key={chip} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300">
              {chip}
            </span>
          ))}
        </div>

        <div className="px-6 border-b border-gray-100 dark:border-slate-800">
          <div className="flex items-center justify-between max-w-lg mx-auto relative">
            <div className="absolute top-[10px] left-[8%] right-[8%] h-[1px] bg-gray-200 dark:bg-slate-700 z-0"></div>

            {/* Read-only progress indicator. Navigation is the footer's job only —
                jumping straight to Confirm from here let the user approve an
                action without ever seeing the analysis it rests on. */}
            {STEPS.map(step => {
              const isActive = activeTab === step.id;
              return (
                <div key={step.id} className="flex flex-col items-center gap-2 z-10 relative select-none">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[12px] font-bold ${isActive ? 'bg-blue-600 text-white' : 'bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-600 text-gray-400 dark:text-slate-400'}`}>
                    {step.num}
                  </div>
                  {/* The active step is underlined on the word itself, so the
                      rule is as wide as the label — a positioned bar spanned the
                      whole step column and sat detached below it. */}
                  <span className={`text-[10px] font-bold ${isActive ? 'text-blue-600 underline decoration-2 underline-offset-4' : 'text-gray-400 dark:text-slate-400'}`}>{step.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── PANEL BODY ──
          No internal scroller: the panel grows with its content and the page
          scrolls, so the toolbar at the end is reached by normal page scroll. */}
      <div className="p-5 bg-white dark:bg-slate-900 text-xs pt-4">

        {/* ── A. REASONS TAB CONTENT ── */}
        {activeTab === 'reasons' && (
          <div className="space-y-4">

            {/* 3 Stats Blocks — label and value share one line, so the whole
                strip is a single row. The `pct` meters are dropped: they read
                as precision the numbers beside them do not actually carry. */}
            <div className="grid grid-cols-3 divide-x divide-gray-100 dark:divide-slate-800 py-2.5">
              {[
                { key: 'CONFIDENCE', stat: sim.reason.confidence, valueClass: 'text-emerald-600' },
                { key: 'AGENTS', stat: sim.reason.agents, valueClass: 'text-gray-900 dark:text-white' },
                { key: 'AT RISK', stat: sim.reason.atRisk, valueClass: 'text-red-600' },
              ].map(({ key, stat, valueClass }) => (
                <div key={key} className="flex items-center justify-center gap-2 px-2 min-w-0">
                  <span className="text-[9px] font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest whitespace-nowrap">{key}</span>
                  <span className={`text-[13px] font-bold leading-none truncate ${valueClass}`}>{stat.value}</span>
                </div>
              ))}
            </div>

            {/* Checklist Box — why this action fired */}
            <div className="bg-[#f9fbff] dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700/50 rounded-[20px] p-5 space-y-4">
              {sim.reason.checklist.map((item, idx) => (
                <div key={idx} className="flex items-start gap-3.5">
                  <p className="text-[12.5px] font-medium text-slate-700 dark:text-slate-300 leading-snug">{item}</p>
                </div>
              ))}
            </div>

            {/* Agent Trace Box */}
            <div className="border border-gray-100 dark:border-slate-800 rounded-[24px] p-5 bg-white dark:bg-slate-900">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">AGENT TRACE</span>

              <div className={`flex items-center justify-between ${isAgentTraceOpen ? 'mb-4 border-b border-gray-100 dark:border-slate-800' : ''}`}>
                <button onClick={() => setIsAgentTraceOpen(!isAgentTraceOpen)} className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-bold text-[15px] focus:outline-none">
                  {sim.reason.agentTrace.count} agents contributed <i className={`fa-solid ${isAgentTraceOpen ? 'fa-caret-up' : 'fa-caret-down'} text-[12px]`}></i>
                </button>
                <div className="flex items-center gap-1.5">
                  {sim.reason.agentTrace.badges.map((badge) => (
                    <div key={badge.code} className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-[11px] ${badge.className}`}>
                      {badge.code}
                    </div>
                  ))}
                </div>
              </div>

              {isAgentTraceOpen && (
                <div className="space-y-3 pt-1 text-[12.5px] text-gray-700 dark:text-slate-300 animate-in slide-in-from-top-2 fade-in duration-200">
                  {sim.reason.agentTrace.lines.map((line) => (
                    <p key={line.code}>
                      <span className="font-bold text-gray-900 dark:text-white">{line.code}</span> — {line.text}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── B. ANALYSIS TAB CONTENT ── */}
        {activeTab === 'analysis' && (
          <div className="space-y-6">
            <div>
              <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
                {sim.analyze.metricsTitle}
              </h4>
              <div className="space-y-3">
                {sim.analyze.metrics.map((metric, idx) => (
                  <div key={idx} className="flex items-center justify-between text-[13px]">
                    <div className="flex items-center gap-3 text-gray-600 dark:text-slate-400">
                      <i className={`fa-solid ${metric.icon} w-4 text-center`}></i> {metric.label}
                    </div>
                    <div className={`font-bold ${metric.highlightColor || 'text-gray-900 dark:text-white'}`}>{metric.value}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">
                {sim.analyze.simulationsTitle}
              </h4>

              <div className="space-y-3">
                {sim.analyze.simulations.map((scenario, idx) => {
                  const isOpen = openSimulationAccordion === idx;
                  return (
                    <div
                      key={scenario.id}
                      className={`border ${isOpen ? 'border-gray-100 dark:border-slate-800 shadow-sm' : 'border-gray-100 dark:border-slate-800'} bg-[#f8f9fc] dark:bg-slate-900 rounded-2xl overflow-hidden transition-all duration-200`}
                    >
                      <button
                        onClick={() => setOpenSimulationAccordion(isOpen ? -1 : idx)}
                        className="w-full flex items-center justify-between p-4 bg-[#f8f9fc] dark:bg-slate-900 hover:bg-[#f1f3f9] dark:hover:bg-slate-800 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-[14px] font-medium text-[#1e293b] dark:text-slate-300">{scenario.number}</span>
                          <span className="text-[14.5px] font-bold text-[#1e293b] dark:text-white text-left">{scenario.title}</span>
                        </div>
                        <i className={`fa-solid fa-caret-${isOpen ? 'up' : 'down'} text-[#94a3b8] dark:text-slate-500 text-[12px] flex-shrink-0 ml-2`}></i>
                      </button>

                      {isOpen && (
                        <div className="px-5 pb-5 pt-1 bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800/50">

                          {/* Tabs (only if provided, e.g. for Delay) */}
                          {scenario.tabs && (
                            <div className="flex items-center gap-2 mb-5 mt-4">
                              {scenario.tabs.map((t, tIdx) => (
                                <div key={tIdx} className={`flex-1 text-center py-2 rounded-lg text-[13px] font-bold cursor-pointer transition-colors ${t === scenario.activeTab ? 'bg-[#1e293b] dark:bg-slate-700 text-white shadow-sm' : 'bg-[#f1f5f9] dark:bg-slate-800 text-[#64748b] dark:text-slate-400 hover:bg-[#e2e8f0] dark:hover:bg-slate-700'}`}>
                                  {t}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Scenario setup reads before its numbers; the "act now"
                              case reads after, because the numbers are the point. */}
                          {scenario.description && scenario.descriptionPlacement !== 'after' && (
                            <p className="text-[13px] text-[#64748b] dark:text-slate-400 leading-relaxed mt-4 mb-4 font-medium">
                              {scenario.description}
                            </p>
                          )}

                          {/* Dynamic Cards Layout */}
                          <div className={`flex gap-3 mt-4 ${scenario.cards.length === 1 ? 'max-w-[50%]' : ''}`}>
                            {scenario.cards.map((card, cIdx) => (
                              <div key={cIdx} className="flex-1 bg-[#f8fafc] dark:bg-slate-800 rounded-xl p-3 border border-gray-100 dark:border-slate-700">
                                <div className="text-[10px] font-bold text-[#64748b] dark:text-slate-400 uppercase tracking-widest mb-1">{card.label}</div>
                                <div className={`text-[15px] font-bold ${card.valueColor} tracking-wide`}>{card.value}</div>
                              </div>
                            ))}
                          </div>

                          {scenario.description && scenario.descriptionPlacement === 'after' && (
                            <p className="text-[13px] text-[#64748b] dark:text-slate-400 leading-relaxed mt-4 font-medium">
                              {scenario.description}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ── C. DECISION TAB CONTENT ── */}
        {activeTab === 'decision' && (
          <div className="space-y-5">
            {/* Recommended Action Box */}
            <div className="bg-[#f9fbff] dark:bg-slate-800/30 border border-blue-100/50 dark:border-slate-700/50 rounded-[20px] p-5">
              <div className="flex gap-4 items-start mb-5">
                <div className="w-11 h-11 bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-800 flex-shrink-0 flex items-center justify-center text-blue-600 shadow-sm">
                  <i className={`fa-solid ${sim.decide.recommendedAction.icon} text-lg`}></i>
                </div>
                <div>
                  <div className="text-[9px] font-bold text-blue-600 uppercase tracking-widest mb-1.5">
                    {sim.decide.recommendedAction.label}
                  </div>
                  <h3 className="text-[15px] font-bold text-gray-900 dark:text-white leading-snug mb-1">
                    {sim.decide.recommendedAction.title}
                  </h3>
                  <p className="text-[12.5px] text-gray-500 dark:text-slate-400 font-medium">
                    {sim.decide.recommendedAction.description}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-3">
                {sim.decide.recommendedAction.metrics.map((metric, idx) => (
                  <div key={idx} className="bg-white dark:bg-slate-900 rounded-xl p-3 border border-gray-100 dark:border-slate-800 flex flex-col items-start justify-center shadow-[0_2px_8px_rgb(0,0,0,0.02)] dark:shadow-none">
                    <i className={`fa-solid ${metric.icon} text-gray-400 dark:text-slate-500 text-[13px] mb-2`}></i>
                    <div className="text-[9px] text-gray-500 dark:text-slate-400 leading-tight mb-2 font-medium">{metric.label}</div>
                    <div className={`text-[13px] font-bold ${metric.color}`}>{metric.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* What happens after approval */}
            <div>
              <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">
                {sim.decide.approvalStepsTitle}
              </h4>
              <div className="space-y-3">
                {sim.decide.approvalSteps.map((item, idx) => (
                  <div key={idx} className="flex-1 bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-[14px] p-2.5 flex items-center gap-3 shadow-sm">
                    <div className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 flex-shrink-0 font-bold text-[12px]">
                      {item.step}
                    </div>
                    <div className="text-[12.5px] text-gray-600 dark:text-slate-300 font-medium">{item.text}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Decision Confidence */}
            <div>
              <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">
                {sim.decide.confidenceTitle}
              </h4>
              <div className="bg-[#f9fafb] dark:bg-slate-800/30 rounded-[20px] p-5 border border-gray-100 dark:border-slate-800">
                <div className="flex items-center gap-5">
                  <div className="w-[68px] h-[68px] rounded-full border-[5px] border-emerald-500 flex items-center justify-center flex-shrink-0 shadow-sm bg-white dark:bg-slate-900">
                    <span className="text-[17px] font-bold text-gray-900 dark:text-white">
                      {sim.decide.confidenceScore}
                    </span>
                  </div>
                  <div>
                    <h5 className="font-bold text-gray-900 dark:text-white text-[14px] mb-1">
                      {sim.decide.confidenceLevel}
                    </h5>
                    <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed mb-3 font-medium">
                      {sim.decide.confidenceDescription}
                    </p>
                    <div className="grid grid-cols-2 gap-y-2.5 gap-x-4">
                      {sim.decide.confidenceFactors.map((factor, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-[11px] text-gray-600 dark:text-slate-300 font-medium">
                          <i className="fa-solid fa-check text-emerald-500 text-[10px]"></i> {factor}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 text-[11.5px] text-gray-500 dark:text-slate-400 mt-3 pl-2 font-medium">
                <i className="fa-regular fa-clock"></i> {sim.decide.confidenceDisclaimer}
              </div>
            </div>

          </div>
        )}

        {/* ── D. CONFIRM TAB CONTENT ── */}
        {activeTab === 'confirm' && (
          /* No `h-full` here: it forced this wrapper to one body-height, the
             taller content spilled out of it, and the toolbar — the next sibling
             — landed mid-content with the overflow painting underneath. */
          <div>
            {actionSuccess ? (
              <div className="min-h-[420px] flex flex-col items-center justify-center text-center animate-in fade-in zoom-in-95 duration-300 pb-6 pt-8">
                <div className="w-20 h-20 rounded-full bg-[#e8fbf0] dark:bg-emerald-900/30 flex items-center justify-center mb-6">
                  <i className="fa-solid fa-check text-[#38a169] dark:text-emerald-400 text-3xl"></i>
                </div>
                <h2 className="text-[22px] font-bold text-[#0f172a] dark:text-white mb-4 tracking-tight">
                  {sim.success.title}
                </h2>
                <p className="text-[14px] text-slate-500 dark:text-slate-400 max-w-[320px] leading-relaxed mx-auto">
                  {sim.success.description}
                </p>
                <div className="mt-5 text-[11px] font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                  {sim.success.referenceCode}
                </div>
              </div>
            ) : (
              <div className="space-y-5 pb-6">
                {/* Action Summary */}
                <div>
                  <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">
                    {sim.confirm.actionSummaryTitle}
                  </h4>
                  <div className="border border-gray-100 dark:border-slate-800 rounded-[20px] bg-white dark:bg-slate-900 shadow-[0_2px_8px_rgb(0,0,0,0.02)] dark:shadow-none overflow-hidden divide-y divide-gray-50 dark:divide-slate-800/50">
                    {sim.confirm.actionSummary.map((row, idx) => (
                      <div key={idx} className="flex justify-between items-center px-6 py-3 text-[13px]">
                        <div className="text-gray-500 dark:text-slate-400 font-medium">{row.label}</div>
                        <div className={`${row.isBold ? 'font-bold' : 'font-medium'} ${row.valueColor || 'text-gray-900 dark:text-white'}`}>{row.value}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Simulation Summary */}
                <div>
                  <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">
                    {sim.confirm.simulationSummaryTitle}
                  </h4>
                  <div className="grid grid-cols-3 gap-3">
                    {sim.confirm.simulationCards.map((card, idx) => {
                      let colors = {};
                      if (card.type === 'worst') {
                        colors = { bg: 'bg-[#fff5f6] dark:bg-red-950/20', border: 'border-[#ffe4e6] dark:border-red-900/30', text: 'text-[#e11d48] dark:text-red-400', divider: 'border-[#ffe4e6] dark:border-red-900/30' };
                      } else if (card.type === 'expected') {
                        colors = { bg: 'bg-[#f4f8ff] dark:bg-blue-950/20', border: 'border-[#e0e7ff] dark:border-blue-900/30', text: 'text-[#2563eb] dark:text-blue-400', divider: 'border-[#e0e7ff] dark:border-blue-900/30' };
                      } else {
                        colors = { bg: 'bg-[#f0fdf4] dark:bg-emerald-950/20', border: 'border-[#dcfce7] dark:border-emerald-900/30', text: 'text-[#16a34a] dark:text-emerald-400', divider: 'border-[#dcfce7] dark:border-emerald-900/30' };
                      }

                      return (
                        <div key={idx} className={`${colors.bg} ${colors.border} border rounded-[20px] p-5 flex flex-col justify-between shadow-[0_2px_8px_rgb(0,0,0,0.01)] dark:shadow-none`}>
                          <div className={`text-[10px] font-bold ${colors.text} mb-3`}>{card.title}</div>
                          <div className={`text-[24px] font-bold ${colors.text} mb-5 tracking-tight`}>{card.value}</div>
                          <div className={`border-t ${colors.divider} pt-3 text-[11px] text-gray-500 dark:text-slate-400 font-medium`}>{card.subtitle}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Final Checklist */}
                <div>
                  <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">
                    {sim.confirm.checklistTitle}
                  </h4>
                  <div className="border border-gray-100 dark:border-slate-800 rounded-[20px] bg-white dark:bg-slate-900 shadow-[0_2px_8px_rgb(0,0,0,0.02)] dark:shadow-none overflow-hidden divide-y divide-gray-50 dark:divide-slate-800/50">
                    {sim.confirm.checklist.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-4 px-6 py-3">
                        <div className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center flex-shrink-0">
                          <i className="fa-solid fa-check text-[10px]"></i>
                        </div>
                        <div className="text-[13px] text-gray-700 dark:text-slate-300 font-medium">{item}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── 3. BOTTOM TOOLBAR ──
            Sits inside the scroll area rather than pinned to the panel: a fixed
            footer permanently cost the body ~85px of height. The negative inline
            margin lets the divider span the panel edge-to-edge while the buttons
            stay aligned with the content above. */}
        <div className="relative mt-3 -mx-5 px-2 pt-3 pb-1 border-t border-gray-100 dark:border-slate-800">
          {actionSuccess ? (
            <div className="flex items-center justify-center h-[40px] animate-in fade-in duration-300">
              <span className="text-[13px] font-medium text-slate-400">Completed</span>
            </div>
          ) : (
            /* One flow row: progress on the left, actions grouped on the right.
               The step line used to be absolutely centred over the whole bar, so
               it collided with the primary button — it is in the layout now and
               cannot overlap. */
            <div className="flex items-center justify-between gap-4">
              <span className="text-[11px] font-medium text-gray-400 dark:text-slate-500 whitespace-nowrap">
                Step {stepIndex + 1} of {STEPS.length} — {STEPS[stepIndex].label}
              </span>

              <div className="flex items-center gap-2.5">
                {/* Step 1 has nowhere to go back to, so Back is absent rather
                    than present-but-greyed. */}
                {!isFirstStep && (
                  <button
                    onClick={() => handleSwitchTab(STEPS[stepIndex - 1].id)}
                    disabled={isApplyingAction}
                    className="px-5 py-2.5 rounded-lg text-[13px] font-bold border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
                  >
                    <i className="fa-solid fa-arrow-left text-[11px]" /> Back
                  </button>
                )}

                <button
                  onClick={() => {
                    if (isLastStep) handleConfirmInlineAction();
                    else handleSwitchTab(STEPS[stepIndex + 1].id);
                  }}
                  disabled={isApplyingAction}
                  className="px-6 py-2.5 bg-[#0f172a] dark:bg-white hover:bg-gray-900 dark:hover:bg-gray-100 text-white dark:text-gray-900 rounded-lg text-[13px] font-bold transition-colors shadow-[0_2px_8px_rgb(0,0,0,0.1)] dark:shadow-none flex items-center gap-2 whitespace-nowrap"
                >
                  {isApplyingAction ? (
                    <>Applying... <i className="fa-solid fa-spinner fa-spin text-[11px]" /></>
                  ) : (
                    <>
                      {isLastStep ? 'Confirm & Execute' : `${STEPS[stepIndex + 1].label}`}
                      <i className="fa-solid fa-arrow-right text-[11px]" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(InsightDetailsPanel);