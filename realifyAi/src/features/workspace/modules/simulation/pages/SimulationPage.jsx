import React, { useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import { useSimulationStore } from '@/store/useSimulationStore';
import { ALL_CHANNELS, TIMEFRAMES, WORKSPACE_TAB_META, INPUT_CONFIG, QUICK_PROMPTS_BY_TAB, AI_SUGGESTIONS_BY_TAB, SIM_STEPS } from '@/features/workspace/modules/simulation/data/simulationConfig';
import { computeSimulation } from '@/features/workspace/modules/simulation/utils/computeSimulation';
import { DEFAULT_DOMAIN } from '@/features/workspace/workspaceRoutes';


/* ── Page ─────────────────────────────────────────────────────────────────── */
const SimulationPage = () => {
  const { state } = useLocation();
  const navigate  = useNavigate();

  const insight          = state?.insight;
  const step             = state?.step;
  const backTo           = state?.backTo;
  const backStatePayload = state?.backState;
  const domain         = state?.domain || DEFAULT_DOMAIN;

  const cfg          = INPUT_CONFIG[domain]    || INPUT_CONFIG.sales;
  const categoryMeta = WORKSPACE_TAB_META[domain]  || WORKSPACE_TAB_META.sales;
  const quickPrompts = QUICK_PROMPTS_BY_TAB[domain] || QUICK_PROMPTS_BY_TAB.sales;
  const aiSuggestions = AI_SUGGESTIONS_BY_TAB[domain] || AI_SUGGESTIONS_BY_TAB.sales;

  const handleBack = () => {
    if (backTo) navigate(backTo, { state: backStatePayload });
    else navigate(-1);
  };

  /* ── Simulation input state — hooks must appear before any conditional return ── */
  const [currentPrice,   setCurrentPrice]   = useState(cfg.val1Default);
  const [simulatedPrice, setSimulatedPrice] = useState(cfg.val2Default);
  const [channels,       setChannels]       = useState(['Amazon', 'Shopify', 'Walmart Marketplace']);
  const [channelOpen,    setChannelOpen]    = useState(false);
  const [timeframe,      setTimeframe]      = useState('4weeks');

  /* ── Committed (last-run) inputs — results only update on Run Simulation ── */
  const [committed, setCommitted] = useState({
    currentPrice:   cfg.val1Default,
    simulatedPrice: cfg.val2Default,
    channels:       ['Amazon', 'Shopify', 'Walmart Marketplace'],
  });

  /* ── AI Copilot state ── */
  const [aiGoal,         setAiGoal]         = useState('');
  const [aiGenerating,   setAiGenerating]   = useState(false);
  const [aiSuggestion,   setAiSuggestion]   = useState('');
  const [aiPreviewPrice, setAiPreviewPrice] = useState(null);

  /* ── Preview / Apply state ── */
  const [previewMode,  setPreviewMode]  = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  /* ── Edit / Execute state ── */
  const [isEditing,       setIsEditing]       = useState(false);
  const [_hasSimulated,   setHasSimulated]    = useState(false);
  const [showSimProgress, setShowSimProgress] = useState(false);
  const [simProgress,     setSimProgress]     = useState(0);

  /* ── Simulation store (global header loader) ── */
  const startSimulation   = useSimulationStore(s => s.startSimulation);
  const setGlobalProgress = useSimulationStore(s => s.setProgress);
  const endSimulation     = useSimulationStore(s => s.endSimulation);

  /* ── Computed results — useMemo must also be before the guard ── */
  const r = useMemo(() => computeSimulation(domain, committed.currentPrice, committed.simulatedPrice, committed.channels), [domain, committed]);
  const previewR = useMemo(() => {
    if (!previewMode || !aiPreviewPrice) return null;
    return computeSimulation(domain, committed.currentPrice, aiPreviewPrice, committed.channels);
  }, [domain, previewMode, aiPreviewPrice, committed]);

  if (!insight && !step) { navigate(-1); return null; }

  /* ── Derived slider values (always from real simulatedPrice) ── */
  const pricePct = Math.round((simulatedPrice - currentPrice) / currentPrice * 100);
  const sliderMin = Math.round(currentPrice * 0.5);
  const sliderMax = Math.round(currentPrice * 1.5);

  /* ── Handlers ── */
  const removeChannel = (ch) => setChannels(prev => prev.filter(c => c !== ch));
  const addChannel    = (ch) => { setChannels(prev => [...prev, ch]); setChannelOpen(false); };

  const handleRunSimulation = () => {
    setCommitted({ currentPrice, simulatedPrice, channels });
    setPreviewMode(false);
    setHasSimulated(true);
  };

  const handleReset = () => {
    setCurrentPrice(cfg.val1Default);
    setSimulatedPrice(cfg.val2Default);
    setChannels(['Amazon', 'Shopify', 'Walmart Marketplace']);
    setTimeframe('4weeks');
    setCommitted({ currentPrice: cfg.val1Default, simulatedPrice: cfg.val2Default, channels: ['Amazon', 'Shopify', 'Walmart Marketplace'] });
    setPreviewMode(false);
    setAiSuggestion('');
    setAiPreviewPrice(null);
  };

  const handleGenerate = () => {
    setAiGenerating(true);
    setAiSuggestion('');
    setAiPreviewPrice(null);
    setPreviewMode(false);
    setTimeout(() => {
      const suggestion = aiSuggestions[aiGoal] ||
        `Based on your simulation for ${categoryMeta.label} — ${step?.title || 'this action'}, the projected outcome shows meaningful improvement. Adjust the inputs above and run the simulation again to refine your estimate.`;
      const priceMatch = suggestion.match(/\$(\d{2,6})/);
      setAiSuggestion(suggestion);
      setAiPreviewPrice(priceMatch ? parseInt(priceMatch[1]) : null);
      setAiGenerating(false);
    }, 1200);
  };

  const handlePreviewImpact = () => {
    if (aiPreviewPrice) setPreviewMode(true);
  };

  const handleExitPreview = () => setPreviewMode(false);

  const handleApplySuggestion = () => {
    if (!aiPreviewPrice) return;
    const newPrice = aiPreviewPrice;
    setSimulatedPrice(newPrice);
    setCommitted({ currentPrice, simulatedPrice: newPrice, channels });
    setPreviewMode(false);
    setAiSuggestion('');
    setAiPreviewPrice(null);
    setApplySuccess(true);
    setTimeout(() => setApplySuccess(false), 3000);
  };

  const handleDismissSuggestion = () => {
    setAiSuggestion('');
    setAiPreviewPrice(null);
    setPreviewMode(false);
  };

  const _handleExecute = () => {
    setShowSimProgress(true);
    setSimProgress(0);
    startSimulation();
    const ticks = [[600,35],[1400,65],[2200,85],[3000,100]];
    ticks.forEach(([delay, val]) => {
      setTimeout(() => {
        setSimProgress(val);
        setGlobalProgress(val);
      }, delay);
    });
    setTimeout(() => endSimulation(), 5500);
  };

  /* ── Pending state: live inputs differ from last-run committed inputs ── */
  const hasPending =
    currentPrice  !== committed.currentPrice  ||
    simulatedPrice !== committed.simulatedPrice ||
    channels.join(',') !== committed.channels.join(',');

  const displayR        = previewR || r;
  const displaySimPrice = (previewMode && aiPreviewPrice) ? aiPreviewPrice : committed.simulatedPrice;

  const revImpact   = displayR.projRevenue - displayR.revenue;
  const reachImpact = displayR.projReach   - displayR.reach;
  const ltvImpact   = (displayR.projLtv   - displayR.ltv).toFixed(1);
  const convImpact  = (displayR.projConversion - displayR.conversion).toFixed(1);
  const displayPricePct = Math.round((displaySimPrice - committed.currentPrice) / committed.currentPrice * 100);

  const pct  = (proj, base) => Math.round((proj - base) / base * 100);
  const fmtN = (n) => n >= 0 ? `+${n.toLocaleString()}` : n.toLocaleString();
  const pos  = (n) => parseFloat(n) >= 0;

  const green = 'text-green-600 dark:text-green-400';
  const red   = 'text-red-500 dark:text-red-400';
  const col   = (n) => pos(n) ? green : red;
  const arr   = (n) => pos(n) ? '↑' : '↓';

  const _filterBar = null;

  const summaryCards = domain === 'inventory' ? [
    { icon: 'fa-shield-halved',  label: 'Revenue Protected', main: `$${displayR.projRevenue.toLocaleString()}`, sub: `${displayR.projRevenue > 0 ? '−' : '+'}${Math.abs(pct(displayR.projRevenue, Math.max(1, displayR.revenue)))}%`, unit: 'at-risk revenue saved', positive: displayR.projRevenue <= displayR.revenue },
    { icon: 'fa-calendar-check', label: 'Days Cover Added',  main: `${displayR.projReach}d`,  sub: `+${displayR.projReach - displayR.reach} days`, unit: 'total days of cover', positive: displayR.projReach > displayR.reach },
    { icon: 'fa-boxes-stacked',  label: 'Total Stock',       main: `${displayR.projConversion.toLocaleString()}`, sub: `+${displayR.projConversion - displayR.conversion} units`, unit: 'units after reorder', positive: true },
  ] : domain === 'ads' ? [
    { icon: 'fa-arrow-trend-up', label: 'Revenue Uplift',    main: `$${displayR.projRevenue.toLocaleString()}`, sub: `${fmtN(displayR.projRevenue - displayR.revenue)}`, unit: 'projected monthly', positive: displayR.projRevenue >= displayR.revenue },
    { icon: 'fa-bullseye',       label: 'ROAS',              main: `${displayR.projLtv}x`,  sub: `${pos(displayR.projLtv - displayR.ltv) ? '+' : ''}${(displayR.projLtv - displayR.ltv).toFixed(1)}x`, unit: 'return on ad spend', positive: displayR.projLtv >= displayR.ltv },
    { icon: 'fa-eye',            label: 'Impressions',       main: `${(displayR.projConversion / 1000).toFixed(1)}K`, sub: `${fmtN(displayR.projConversion - displayR.conversion)}`, unit: 'estimated monthly', positive: displayR.projConversion >= displayR.conversion },
  ] : domain === 'cash' ? [
    { icon: 'fa-vault',          label: 'Cash Available',    main: `$${(displayR.projRevenue / 1000).toFixed(0)}K`, sub: `+$${((displayR.projRevenue - displayR.revenue) / 1000).toFixed(0)}K`, unit: 'operating cash', positive: displayR.projRevenue >= displayR.revenue },
    { icon: 'fa-calendar-days',  label: 'Days Cover',        main: `${displayR.projReach}d`,  sub: `+${displayR.projReach - displayR.reach}d`, unit: 'cash runway', positive: displayR.projReach >= displayR.reach },
    { icon: 'fa-percent',        label: 'Interest Cost',     main: `$${displayR.projLtv.toLocaleString()}`, sub: `${displayR.projLtv < displayR.ltv ? '−' : '+'}$${Math.abs(displayR.projLtv - displayR.ltv)}`, unit: 'over extension period', positive: displayR.projLtv <= displayR.ltv },
  ] : [
    { icon: 'fa-arrow-trend-up', label: 'Revenue Impact',  main: `${fmtN(revImpact)}`,  sub: `${pct(displayR.projRevenue, displayR.revenue) >= 0 ? '+' : ''}${pct(displayR.projRevenue, displayR.revenue)}%`, unit: 'per week',           positive: revImpact >= 0 },
    { icon: 'fa-users',          label: 'Customer Growth', main: `${fmtN(reachImpact)}`, sub: `${pct(displayR.projReach, displayR.reach) >= 0 ? '+' : ''}${pct(displayR.projReach, displayR.reach)}%`,         unit: 'customers per week', positive: reachImpact >= 0 },
    { icon: 'fa-gem',            label: 'LTV Improvement', main: `${pos(ltvImpact) ? '+' : ''}${ltvImpact}x`, sub: `${pct(displayR.projLtv, displayR.ltv) >= 0 ? '+' : ''}${pct(displayR.projLtv, displayR.ltv)}%`, unit: 'LTV multiplier', positive: pos(ltvImpact) },
  ];

  const tableRows = domain === 'inventory' ? [
    { icon: 'fa-boxes-stacked',  iconColor: 'text-blue-500',    label: 'Current Stock',      current: `${committed.currentPrice} units`,   projected: `${committed.currentPrice + committed.simulatedPrice} units`, change: `+${committed.simulatedPrice}`, sub: arr(1), positive: true },
    { icon: 'fa-calendar-check', iconColor: 'text-green-500',   label: 'Days of Cover',      current: `${displayR.reach}d`,                projected: `${displayR.projReach}d`,                    change: `+${displayR.projReach - displayR.reach}d`, sub: arr(1), positive: true },
    { icon: 'fa-triangle-exclamation', iconColor: 'text-red-500',    label: 'Revenue at Risk',    current: `$${displayR.revenue.toLocaleString()}`, projected: `$${displayR.projRevenue.toLocaleString()}`, change: `−$${(displayR.revenue - displayR.projRevenue).toLocaleString()}`, sub: arr(-1), positive: displayR.projRevenue < displayR.revenue },
    { icon: 'fa-percent',        iconColor: 'text-orange-500',  label: 'OOS Probability',    current: `${displayR.ltv}%`,                  projected: `${displayR.projLtv}%`,                      change: `−${displayR.ltv - displayR.projLtv}pp`, sub: arr(-1), positive: displayR.projLtv < displayR.ltv },
    { icon: 'fa-coins',          iconColor: 'text-amber-500',   label: 'Capital Deployed',   current: '—',                                 projected: `$${(committed.simulatedPrice * 45).toLocaleString()}`, change: `$${(committed.simulatedPrice * 45).toLocaleString()}`, sub: '', positive: true },
  ] : domain === 'ads' ? [
    { icon: 'fa-bullhorn',       iconColor: 'text-blue-500',    label: 'Ad Budget',          current: `$${committed.currentPrice.toLocaleString()}/mo`,  projected: `$${committed.simulatedPrice.toLocaleString()}/mo`, change: `+$${(committed.simulatedPrice - committed.currentPrice).toLocaleString()}`, sub: arr(1), positive: true },
    { icon: 'fa-circle-dollar-to-slot', iconColor: 'text-green-500', label: 'Revenue',       current: `$${displayR.revenue.toLocaleString()}`, projected: `$${displayR.projRevenue.toLocaleString()}`, change: `${fmtN(revImpact)}`, sub: `${pct(displayR.projRevenue, displayR.revenue)}% ${arr(revImpact)}`, positive: revImpact >= 0 },
    { icon: 'fa-bullseye',       iconColor: 'text-purple-500',  label: 'ROAS',               current: `${displayR.ltv}x`,                  projected: `${displayR.projLtv}x`,                      change: `${pos(ltvImpact) ? '+' : ''}${ltvImpact}x`, sub: arr(parseFloat(ltvImpact)), positive: pos(ltvImpact) },
    { icon: 'fa-eye',            iconColor: 'text-orange-500',  label: 'Impressions',        current: `${(displayR.conversion / 1000).toFixed(1)}K`,  projected: `${(displayR.projConversion / 1000).toFixed(1)}K`, change: `+${((displayR.projConversion - displayR.conversion) / 1000).toFixed(1)}K`, sub: arr(1), positive: true },
    { icon: 'fa-percent',        iconColor: 'text-red-500',     label: 'ACoS',               current: `${Math.round(100 / displayR.ltv)}%`, projected: `${Math.round(100 / displayR.projLtv)}%`, change: `−${Math.round(100 / displayR.ltv) - Math.round(100 / displayR.projLtv)}pp`, sub: arr(-1), positive: displayR.projLtv > displayR.ltv },
  ] : domain === 'cash' ? [
    { icon: 'fa-coins',          iconColor: 'text-amber-500',   label: 'Invoice / Amount',   current: `$${committed.currentPrice.toLocaleString()}`,  projected: `$${committed.currentPrice.toLocaleString()}`, change: '—', sub: '', positive: true },
    { icon: 'fa-vault',          iconColor: 'text-green-500',   label: 'Cash Available',     current: `$${(displayR.revenue / 1000).toFixed(0)}K`,    projected: `$${(displayR.projRevenue / 1000).toFixed(0)}K`, change: `+$${((displayR.projRevenue - displayR.revenue) / 1000).toFixed(0)}K`, sub: arr(1), positive: true },
    { icon: 'fa-calendar-days',  iconColor: 'text-blue-500',    label: 'Days Cover',         current: `${displayR.reach}d`,                           projected: `${displayR.projReach}d`, change: `+${displayR.projReach - displayR.reach}d`, sub: arr(1), positive: true },
    { icon: 'fa-percent',        iconColor: 'text-orange-500',  label: 'Interest Cost',      current: `$${displayR.ltv.toLocaleString()}`,             projected: `$${displayR.projLtv.toLocaleString()}`, change: `${displayR.projLtv <= displayR.ltv ? '−' : '+'}$${Math.abs(displayR.projLtv - displayR.ltv)}`, sub: arr(displayR.ltv - displayR.projLtv), positive: displayR.projLtv <= displayR.ltv },
    { icon: 'fa-circle-dollar-to-slot', iconColor: 'text-green-500', label: 'Net Cash Benefit', current: `$${displayR.conversion.toLocaleString()}`, projected: `$${displayR.projConversion.toLocaleString()}`, change: `+$${(displayR.projConversion - displayR.conversion).toLocaleString()}`, sub: arr(1), positive: true },
  ] : [
    { icon: 'fa-tag',                   iconColor: 'text-gray-500 dark:text-slate-400',  label: 'Price',           current: `$${committed.currentPrice}`,           projected: `$${displaySimPrice}`,                              change: `${displayPricePct >= 0 ? '+' : ''}${displayPricePct}%`, sub: arr(displayPricePct),                                                        positive: displayPricePct >= 0 },
    { icon: 'fa-circle-dollar-to-slot', iconColor: 'text-green-500',   label: 'Weekly Revenue',  current: `$${displayR.revenue.toLocaleString()}`, projected: `$${displayR.projRevenue.toLocaleString()}`,         change: `${fmtN(revImpact)}`,                                    sub: `+${pct(displayR.projRevenue, displayR.revenue)}% ${arr(revImpact)}`,         positive: revImpact >= 0 },
    { icon: 'fa-users',                 iconColor: 'text-blue-500',    label: 'Customer Reach',  current: `${displayR.reach.toLocaleString()}`,    projected: `${displayR.projReach.toLocaleString()}`,            change: `${fmtN(reachImpact)}`,                                  sub: `+${pct(displayR.projReach, displayR.reach)}% ${arr(reachImpact)}`,           positive: reachImpact >= 0 },
    { icon: 'fa-gem',                   iconColor: 'text-gray-500 dark:text-slate-400',  label: 'LTV Multiplier',  current: `${displayR.ltv}x`,                     projected: `${displayR.projLtv}x`,                             change: `${pos(ltvImpact) ? '+' : ''}${ltvImpact}x`,             sub: `+${pct(displayR.projLtv, displayR.ltv)}% ${arr(ltvImpact)}`,                positive: pos(ltvImpact) },
    { icon: 'fa-arrows-rotate',         iconColor: 'text-orange-500',  label: 'Conversion Rate', current: `${displayR.conversion}%`,              projected: `${displayR.projConversion}%`,                       change: `${pos(convImpact) ? '+' : ''}${convImpact}pp`,          sub: `+${pct(displayR.projConversion, displayR.conversion)}% ${arr(convImpact)}`,  positive: pos(convImpact) },
  ];

  return (
    <>
    <DashboardLayout
      title="Insight Simulation"
      subtitle="Preview the impact of this insight before implementing"
      showTabs={false}
      showAIPrompt={false}
    >
      {/* Back button — same style as insight detail page */}
      <div className="flex items-center -mt-2 pb-4">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors"
        >
          <i className="fa-solid fa-arrow-left text-sm" />
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 min-h-0">

        {/* ── Left: Simulation Input ────────────────────────────────────────── */}
        <div className="w-full sm:w-[255px] sm:flex-shrink-0">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col sm:h-full">

            <div className="space-y-3.5 sm:flex-1 sm:overflow-y-auto">

              {/* INSIGHT — static label from the step that triggered the simulation */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Insight</label>
                  <button
                    onClick={() => setIsEditing(v => !v)}
                    title={isEditing ? 'Lock inputs' : 'Edit inputs'}
                    className={`w-5 h-5 flex items-center justify-center rounded transition-colors ${
                      isEditing
                        ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                        : 'bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-300 dark:hover:bg-slate-600'
                    }`}
                  >
                    <i className="fa-solid fa-pen text-[9px]" />
                  </button>
                </div>
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800/60">
                  <span className="text-xs font-semibold text-gray-800 dark:text-slate-200 truncate">
                    {step?.title || categoryMeta.label + ' Optimisation'}
                  </span>
                </div>
              </div>

              {/* Inputs — disabled until user activates edit */}
              <div className={`space-y-3.5 transition-opacity duration-200 ${!isEditing ? 'opacity-50 pointer-events-none select-none' : ''}`}>

              {/* VAL1 — current value input */}
              <div>
                <label className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider block mb-1.5">{cfg.val1Label}</label>
                <div className="relative">
                  {cfg.val1Prefix && <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-slate-400 text-sm font-medium pointer-events-none">{cfg.val1Prefix}</span>}
                  <input type="number" value={currentPrice} min={1}
                    readOnly
                    className="w-full pl-7 pr-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-100 dark:bg-slate-800 text-sm font-semibold text-gray-900 dark:text-slate-100 cursor-not-allowed" />
                </div>
              </div>

              {/* VAL2 — simulated/target value input */}
              <div>
                <label className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider block mb-1.5">{cfg.val2Label}</label>
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="relative flex-1">
                    {cfg.val2Prefix && <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-slate-400 text-sm font-medium pointer-events-none">{cfg.val2Prefix}</span>}
                    <input type="number" value={simulatedPrice} min={1}
                      onChange={e => setSimulatedPrice(Math.max(1, +e.target.value))}
                      className={`w-full ${cfg.val2Prefix ? 'pl-7' : 'pl-3'} pr-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-semibold text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-gray-300`} />
                  </div>
                  {cfg.val2Unit ? (
                    <span className="text-xs font-medium text-gray-500 dark:text-slate-400 flex-shrink-0">{cfg.val2Unit}</span>
                  ) : (
                    <span className={`text-xs font-bold px-2 py-1 rounded-lg flex-shrink-0 ${pricePct < 0 ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400' : 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400'}`}>
                      {pricePct >= 0 ? '+' : ''}{pricePct}%
                    </span>
                  )}
                </div>
                <input type="range" min={sliderMin} max={sliderMax} step={1} value={simulatedPrice}
                  onChange={e => setSimulatedPrice(+e.target.value)}
                  className="w-full accent-gray-700 dark:accent-slate-300 cursor-pointer" />
                <div className="flex justify-between text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">
                  <span>{cfg.val2Prefix}{sliderMin}{cfg.val2Unit ? ` ${cfg.val2Unit}` : ''}</span>
                  <span>{cfg.val2Prefix}{sliderMax}{cfg.val2Unit ? ` ${cfg.val2Unit}` : ''}</span>
                </div>
              </div>

              {/* TARGET CHANNELS — only for tabs that support it */}
              {cfg.showChannels && <div>
                <label className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider block mb-1.5">Target Channels</label>
                <div className="flex flex-wrap gap-1.5">
                  {channels.map(ch => (
                    <span key={ch} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 text-xs font-medium rounded-lg border border-gray-200 dark:border-slate-700">
                      {ch}
                      <button onClick={() => removeChannel(ch)} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 ml-0.5">
                        <i className="fa-solid fa-xmark text-[9px]" />
                      </button>
                    </span>
                  ))}
                  <div className="relative">
                    <button onClick={() => setChannelOpen(o => !o)}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-white dark:bg-slate-900 border border-dashed border-gray-300 dark:border-slate-600 text-gray-400 dark:text-slate-500 text-xs rounded-lg hover:border-gray-400 transition-colors">
                      <i className="fa-solid fa-plus text-[9px]" /> Add
                    </button>
                    {channelOpen && (
                      <div className="absolute top-full left-0 mt-1 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg z-30 min-w-[160px] overflow-hidden">
                        {ALL_CHANNELS.filter(c => !channels.includes(c)).map(ch => (
                          <button key={ch} onClick={() => addChannel(ch)}
                            className="block w-full text-left px-3 py-2 text-xs text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors">
                            {ch}
                          </button>
                        ))}
                        {ALL_CHANNELS.every(c => channels.includes(c)) && (
                          <div className="px-3 py-2 text-xs text-gray-400 dark:text-slate-500">All channels added</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>}

              {/* TIMEFRAME */}
              <div>
                <label className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider block mb-1.5">Timeframe</label>
                <div className="relative">
                  <i className="fa-regular fa-calendar absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 text-[10px] pointer-events-none" />
                  <select value={timeframe} onChange={e => setTimeframe(e.target.value)}
                    className="w-full pl-7 pr-6 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-gray-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-gray-300 appearance-none">
                    {TIMEFRAMES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <i className="fa-solid fa-chevron-down absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-[9px] pointer-events-none" />
                </div>
              </div>

              </div>{/* /inputs wrapper */}
            </div>

            {/* Buttons */}
            <div className="flex gap-2 mt-4 pt-3.5 border-t border-gray-100 dark:border-slate-800 flex-shrink-0">
              <button onClick={handleRunSimulation}
                disabled={!isEditing}
                className={`flex-1 px-4 py-2.5 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-xl text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none ${
                  isEditing && hasPending ? 'ring-2 ring-offset-1 ring-amber-400 dark:ring-amber-500' : ''
                }`}>
                {isEditing && hasPending && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse flex-shrink-0" />}
                <i className="fa-solid fa-play text-[9px]" /> Run Simulation
              </button>
              <button onClick={handleReset}
                className="px-3 py-2.5 bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300 rounded-xl text-xs font-medium hover:bg-gray-200 dark:hover:bg-slate-700 transition">
                <i className="fa-solid fa-rotate-left text-[9px]" />
              </button>
            </div>

          </div>
        </div>

        {/* ── Center: Simulation Results ────────────────────────────────────── */}
        <div className="w-full sm:flex-1 sm:min-w-0">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 sm:h-full flex flex-col">

            {/* Header */}
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100">Simulation Results</h3>
              {previewMode ? (
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-50 dark:bg-slate-800 rounded-full text-[10px] font-semibold text-gray-600 dark:text-slate-300">
                  <i className="fa-solid fa-wand-magic-sparkles text-[10px]" />
                  AI Preview
                </span>
              ) : hasPending ? (
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 dark:bg-amber-900/20 rounded-full text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse inline-block" />
                  Changes Pending
                </span>
              ) : (
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-green-50 dark:bg-green-900/20 rounded-full text-[10px] font-semibold text-green-600 dark:text-green-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse inline-block" />
                  Updated just now
                </span>
              )}
            </div>

            {/* Previewing AI Scenario banner */}
            {previewMode && (
              <div className="mb-4 flex items-center justify-between px-4 py-3 rounded-xl bg-gray-50 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-wand-magic-sparkles text-gray-600 dark:text-slate-300 text-xs" />
                  <span className="text-xs font-semibold text-gray-700 dark:text-slate-200">Previewing AI Scenario</span>
                  <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-slate-300">
                    <span className="font-medium">${currentPrice}</span>
                    <i className="fa-solid fa-arrow-right text-[9px]" />
                    <span className="font-bold">${aiPreviewPrice}</span>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={handleApplySuggestion}
                    className="px-3 py-1 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-lg text-[11px] font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition">
                    Apply Suggestion
                  </button>
                  <button onClick={handleExitPreview}
                    className="px-3 py-1 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-300 rounded-lg text-[11px] font-medium hover:bg-gray-50 dark:hover:bg-slate-700 transition">
                    Exit Preview
                  </button>
                </div>
              </div>
            )}

            {/* Changes Pending banner */}
            {hasPending && !previewMode && (
              <div className="mb-4 flex items-center justify-between px-4 py-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-circle-exclamation text-amber-500 dark:text-amber-400 text-xs" />
                  <span className="text-xs font-semibold text-amber-700 dark:text-amber-300">Changes Pending</span>
                  <span className="text-xs text-amber-600 dark:text-amber-400">Run Simulation to update results.</span>
                </div>
                <button onClick={handleRunSimulation}
                  className="px-3 py-1 bg-amber-500 text-white rounded-lg text-[11px] font-bold hover:bg-amber-600 transition flex-shrink-0">
                  Run Now
                </button>
              </div>
            )}

            {/* Apply success banner */}
            {applySuccess && (
              <div className="mb-4 flex items-center gap-3 px-4 py-3 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/30 flex-shrink-0">
                <i className="fa-solid fa-circle-check text-green-600 dark:text-green-400 text-sm flex-shrink-0" />
                <span className="text-xs font-semibold text-green-700 dark:text-green-300">
                  AI Suggestion Applied! Simulation updated to ${simulatedPrice}.
                </span>
              </div>
            )}

            {/* Summary cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4 flex-shrink-0">
              {summaryCards.map(card => (
                <div key={card.label} className={`p-3 border rounded-xl transition-colors ${
                  card.positive
                    ? 'border-green-100 dark:border-green-900/30 bg-green-50/40 dark:bg-green-900/10'
                    : 'border-red-100 dark:border-red-900/30 bg-red-50/30 dark:bg-red-900/10'
                }`}>
                  <div className="flex items-start gap-2">
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      card.positive ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
                    }`}>
                      <i className={`fa-solid ${card.icon} text-xs ${
                        card.positive ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'
                      }`} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[10px] text-gray-500 dark:text-slate-400 font-medium truncate">{card.label}</p>
                      <div className="flex items-baseline gap-1 mt-0.5 flex-wrap">
                        <span className="text-base font-bold text-gray-900 dark:text-slate-100 leading-none">{card.main}</span>
                        <span className={`text-[11px] font-bold ${card.positive ? green : red}`}>{card.sub}</span>
                      </div>
                      <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">{card.unit}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Comparison table */}
            <div className="sm:flex-1 border border-gray-100 dark:border-slate-800 rounded-xl overflow-hidden sm:min-h-0">
              <div className="overflow-auto sm:h-full">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-slate-800/60 border-b border-gray-100 dark:border-slate-800">
                      <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-gray-500 dark:text-slate-400">Metric</th>
                      <th className="px-3 py-2.5 text-center text-[11px] font-semibold text-gray-500 dark:text-slate-400">
                        Current
                        <div className="text-[10px] font-normal text-gray-400 dark:text-slate-500">{cfg.val1Prefix}{committed.currentPrice}{cfg.val2Unit ? ` ${cfg.val2Unit}` : ''}</div>
                      </th>
                      <th className="px-3 py-2.5 text-center text-[11px] font-semibold text-gray-500 dark:text-slate-400">
                        {previewMode ? 'AI Scenario' : 'Projected'}
                        <div className="text-[10px] font-normal text-gray-400 dark:text-slate-500">{cfg.val2Prefix}{displaySimPrice}{cfg.val2Unit ? ` ${cfg.val2Unit}` : ''}</div>
                      </th>
                      <th className="px-3 py-2.5 text-center text-[11px] font-semibold text-gray-500 dark:text-slate-400">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row, i) => (
                      <tr key={row.label} className={`border-b border-gray-50 dark:border-slate-800/50 ${i % 2 === 1 ? 'bg-gray-50/50 dark:bg-slate-800/20' : ''}`}>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-lg bg-gray-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                              <i className={`fa-solid ${row.icon} ${row.iconColor} text-[10px]`} />
                            </div>
                            <span className="text-xs font-medium text-gray-800 dark:text-slate-200">{row.label}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5 text-center text-xs text-gray-600 dark:text-slate-400 font-medium">{row.current}</td>
                        <td className={`px-3 py-2.5 text-center text-xs font-bold ${col(row.positive ? 1 : -1)}`}>{row.projected}</td>
                        <td className="px-3 py-2.5 text-center">
                          <span className={`text-xs font-bold ${col(row.positive ? 1 : -1)}`}>{row.change}</span>
                          <div className={`text-[10px] font-medium ${col(row.positive ? 1 : -1)}`}>{row.sub}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Execute — disabled on simulation page */}
            <button
              disabled
              className="mt-3 w-full py-3 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-xl text-sm font-bold flex-shrink-0 tracking-wide opacity-40 cursor-not-allowed pointer-events-none"
            >
              Execute
            </button>

          </div>
        </div>

        {/* ── Right: AI Copilot ─────────────────────────────────────────────── */}
        <div className="w-full sm:w-[255px] sm:flex-shrink-0">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col sm:h-full">

            <div className="sm:flex-1 sm:overflow-y-auto space-y-4 sm:min-h-0">

            {/* Context breadcrumb */}
              <div className="bg-gray-50 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700 rounded-xl p-3">
                <p className="text-[10px] text-gray-400 dark:text-slate-500 font-medium mb-2">Simulating action for</p>
                <div className="flex items-center gap-1 flex-wrap">
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-gray-500 dark:text-slate-400">
                    <i className={`fa-solid ${categoryMeta.icon} text-[9px]`} />
                    {categoryMeta.label}
                  </span>
                  <i className="fa-solid fa-chevron-right text-[8px] text-gray-300 dark:text-slate-600" />
                  <span className="text-[11px] font-semibold text-gray-500 dark:text-slate-400 truncate max-w-[100px]" title={insight?.heading}>
                  </span>
                  <span className="text-[11px] font-bold text-gray-900 dark:text-slate-100 truncate" title={step?.title}>
                    {step?.title || '—'}
                  </span>
                </div>
              </div>

              {/* Ask AI */}
              <div>
                <p className="text-[10px] text-gray-400 dark:text-slate-500 mb-2">Tell AI what outcome you want to achieve.</p>
                <textarea
                  value={aiGoal}
                  onChange={e => setAiGoal(e.target.value)}
                  placeholder="e.g., Increase sales while maintaining minimum 20% margin"
                  rows={3}
                  className="w-full text-xs text-gray-800 dark:text-slate-200 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl px-3 py-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-gray-300 dark:focus:ring-slate-600 placeholder-gray-300 dark:placeholder-slate-600"
                />
            </div>

              {/* Quick Prompts */}
                    <div>
                <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">Quick Prompts</p>
                <div className="flex flex-wrap gap-1.5">
                  {quickPrompts.map(p => (
                    <button key={p}
                      onClick={() => setAiGoal(p)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${aiGoal === p ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100' : 'bg-white dark:bg-slate-800 text-gray-600 dark:text-slate-300 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600 hover:text-gray-800 dark:hover:text-slate-200'}`}>
                      {p}
                    </button>
                  ))}
                </div>
                    </div>

              {/* AI Suggestion with action buttons */}
              {aiSuggestion && (
                <div className="bg-gray-50 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-2">
                    <span className="text-[10px] font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wide">Suggestion</span>
                  </div>
                  <p className="text-xs text-gray-700 dark:text-slate-300 leading-relaxed mb-3">{aiSuggestion}</p>

                  <div className="flex flex-col gap-1.5">
                    {previewMode ? (
                      <button onClick={handleExitPreview}
                        className="w-full py-2 rounded-lg text-[11px] font-bold border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700 transition flex items-center justify-center gap-1.5">
                        <i className="fa-solid fa-eye-slash text-[10px]" /> Exit Preview
                      </button>
                    ) : (
                      <button onClick={handlePreviewImpact} disabled={!aiPreviewPrice}
                        className="w-full py-2 rounded-lg text-[11px] font-bold bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 hover:bg-gray-700 dark:hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-1.5">
                        <i className="fa-solid fa-eye text-[10px]" /> Preview Impact
                      </button>
                    )}
                    <button onClick={handleApplySuggestion} disabled={!aiPreviewPrice}
                      className="w-full py-2 rounded-lg text-[11px] font-bold bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 hover:bg-gray-700 dark:hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-1.5">
                      <i className="fa-solid fa-check text-[10px]" /> Apply Suggestion
                    </button>
                    <button onClick={handleDismissSuggestion}
                      className="w-full py-1.5 rounded-lg text-[11px] font-medium text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition text-center">
                      Dismiss
                    </button>
                  </div>
                </div>
              )}

            </div>

            {/* Generate / Regenerate button */}
            <div className="mt-4 pt-3.5 border-t border-gray-100 dark:border-slate-800 flex-shrink-0 space-y-2">
              <button
                onClick={handleGenerate}
                disabled={aiGenerating}
                className="w-full py-2.5 rounded-xl text-xs font-bold bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 hover:bg-gray-700 dark:hover:bg-slate-200 disabled:opacity-60 transition flex items-center justify-center gap-1.5 shadow-sm"
              >
                {aiGenerating
                  ? <><i className="fa-solid fa-spinner fa-spin text-[10px]" /> Generating...</>
                  : aiSuggestion
                  ? <><i className="fa-solid fa-rotate text-[10px]" /> Regenerate</>
                  : <> Generate</>
                }
              </button>
              <p className="text-[10px] text-gray-400 dark:text-slate-500 text-center leading-relaxed">
                Suggestions are based on your store data and market trends.
              </p>
            </div>

          </div>
        </div>

      </div>
    </DashboardLayout>

    {/* ── Bottom-right: execution progress popup ── */}
    {showSimProgress && (
      <div className="fixed bottom-6 right-6 w-[280px] bg-slate-800/85 dark:bg-slate-900 border border-slate-400 dark:border-slate-800 rounded-2xl shadow-2xl shadow-gray-900/10 z-[99999] opacity-80 text-white">
        <div className="flex items-start justify-between px-4 pt-4 pb-1">
          <div>
            <p className="text-[10px] font-bold text-white-400 dark:text-slate-500 uppercase tracking-widest mb-0.5">System Status</p>
            <p className="text-sm font-bold text-white-900 dark:text-slate-100">Simulation in process</p>
          </div>
          <button
            onClick={() => setShowSimProgress(false)}
            className="w-6 h-6 flex items-center justify-center text-white-400 hover:text-white-600 dark:hover:text-slate-300 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors flex-shrink-0 mt-0.5"
          >
            <i className="fa-solid fa-xmark text-xs" />
          </button>
        </div>
        <div className="px-4 pt-2 pb-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-white-500 dark:text-slate-400">Overall Progress</span>
            <span className="text-xs font-bold text-white-700 dark:text-slate-300">{simProgress}%</span>
          </div>
          <div className="h-2 w-full bg-gray-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gray-900 dark:bg-slate-200 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${simProgress}%` }}
            />
          </div>
        </div>
        <div className="px-4 pb-3 space-y-2.5">
          {SIM_STEPS.map((s, i) => {
            const done = simProgress >= s.threshold;
            const prev = i === 0 ? 0 : SIM_STEPS[i - 1].threshold;
            const current = !done && simProgress >= prev;
            return (
              <div key={s.label} className="flex items-center gap-2.5">
                {done ? (
                  <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
                    <i className="fa-solid fa-check text-white text-[7px]" />
                  </div>
                ) : current ? (
                  <i className="fa-solid fa-circle-notch fa-spin text-white-400 dark:text-slate-500 text-sm flex-shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-white-200 dark:border-slate-700 flex-shrink-0" />
                )}
                <span className={`text-xs leading-snug ${done ? 'text-white-700 dark:text-slate-300' : current ? 'text-white-500 dark:text-slate-400' : 'text-white-300 dark:text-slate-600'}`}>
                  {s.label}{current && <span className="ml-0.5 text-white-400 dark:text-slate-500"> ●●●</span>}
                </span>
              </div>
            );
          })}
        </div>
        <div className="border-t border-gray-100 dark:border-slate-800 px-4 py-2.5 flex justify-end">
          <button className="text-[11px] font-bold text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 uppercase tracking-wide transition-colors">
            View Details
          </button>
        </div>
      </div>
    )}
    </>
  );
};

export default SimulationPage;
