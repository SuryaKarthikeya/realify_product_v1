import React, { useState } from 'react';
import { useAIStore } from '@/store/useAIStore';
import {
  liveAgentPanel,
  LIVE_PANEL_TABS,
  IMPACT_TREND,
  FREQUENCY_BARS,
} from '@/features/agents/data/agentDetailData';

/** Inline sparkline for the Impact tile. */
const MiniLine = ({ series }) => {
  const min = Math.min(...series);
  const max = Math.max(...series);
  const span = max - min || 1;
  const points = series
    .map((v, i) => `${(i / (series.length - 1)) * 100},${(24 - ((v - min) / span) * 20).toFixed(1)}`)
    .join(' ');

  return (
    <svg viewBox="0 0 100 26" preserveAspectRatio="none" className="w-full h-6" aria-hidden="true">
      <polyline
        points={points}
        fill="none"
        stroke="#22c55e"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};

/** Bar chart for the Frequency tile. */
const MiniBars = ({ series }) => {
  const max = Math.max(...series) || 1;
  return (
    <div className="flex items-end gap-[3px] h-6" aria-hidden="true">
      {series.map((v, i) => (
        <span
          key={i}
          className="flex-1 rounded-sm bg-indigo-500"
          style={{ height: `${Math.max(15, (v / max) * 100)}%` }}
        />
      ))}
    </div>
  );
};

/**
 * Ring gauge for Confidence.
 *
 * Drawn with `stroke-dasharray` on a circle rather than a library — the arc
 * length is the circumference, so the fill is exact at any percentage.
 */
const MiniRing = ({ value }) => {
  const r = 15;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative w-[38px] h-[38px] mx-auto">
      <svg viewBox="0 0 38 38" className="w-full h-full -rotate-90">
        <circle cx="19" cy="19" r={r} fill="none" stroke="currentColor" strokeWidth="3.5" className="text-indigo-100 dark:text-indigo-950" />
        <circle
          cx="19"
          cy="19"
          r={r}
          fill="none"
          stroke="#4f46e5"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeDasharray={`${(value / 100) * c} ${c}`}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-indigo-600 dark:text-indigo-400">
        {value}%
      </span>
    </div>
  );
};

const SectionLabel = ({ children }) => (
  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2.5">
    {children}
  </p>
);

/**
 * Right-hand panel for a specialist that is **live** — graduated and running.
 *
 * A live agent is reported on differently from one still in Shadow: the ramp bar
 * and graduation gates no longer apply, so this shows its goal, focus areas, key
 * metrics and what it has actually done. Agents still in Shadow get
 * `AgentDetailPanel` instead.
 *
 * No internal scroller: the panel grows with its content and the page scrolls.
 */
const LiveAgentPanel = ({ agent, onClose, onAssign, onViewProfile }) => {
  const [tab, setTab] = useState('Overview');
  const addAiReference = useAIStore((s) => s.addAiReference);
  const setAiPromptValue = useAIStore((s) => s.setAiPromptValue);

  const panel = liveAgentPanel(agent);
  if (!panel) return null;

  /* Same behaviour as the Shadow panel's "Chat with" — attach this specialist to
     the prompt box as context, then focus it. */
  const handleChat = () => {
    addAiReference({
      title: `${agent.name} · live`,
      value: [
        `Specialist: ${agent.name} (${agent.initials}) — live`,
        `Scope: ${agent.meta}`,
        `Goal: ${panel.goal}`,
        `Focus areas: ${panel.focusAreas.join(', ')}`,
        `Impact ${panel.impact} · ${panel.frequency} · ${panel.confidence}% confidence`,
        `Recent: ${panel.recentActions.map((a) => a.label).join('; ')}`,
      ].join('\n'),
    });
    setAiPromptValue(`Ask ${agent.initials} about `);
    const input = document.querySelector('.ai-prompt-input');
    if (input) {
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-card dark:shadow-none font-sans">

      {/* ── Header ── */}
      <div className="p-4 flex items-start gap-3.5">
        <span className="w-11 h-11 rounded-xl bg-indigo-600 flex-shrink-0 flex items-center justify-center text-white text-[12px] font-bold">
          {agent.initials}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h2 className="text-[17px] font-bold text-gray-900 dark:text-white tracking-tight">
              {agent.name}
            </h2>
            <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 text-[9px] font-bold uppercase tracking-wider">
              Active
            </span>
          </div>
          <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-0.5">
            {agent.hireTagline || 'Runs like a GM'}
          </p>
        </div>

        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 transition-colors flex-shrink-0"
          aria-label="Close agent details"
        >
          <i className="fa-solid fa-xmark text-[15px]" />
        </button>
      </div>

      {/* ── Tabs ── */}
      <div className="px-5 border-b border-gray-100 dark:border-slate-800">
        <div className="flex items-center gap-6 overflow-x-auto scrollbar-hide">
          {LIVE_PANEL_TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-2.5 text-[12.5px] font-semibold whitespace-nowrap transition-colors relative ${
                tab === t
                  ? 'text-indigo-600 dark:text-indigo-400'
                  : 'text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200'
              }`}
            >
              {t}
              {tab === t && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-indigo-600 dark:bg-indigo-400 rounded-t-sm" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4">
        {/* ── Overview ── */}
        {tab === 'Overview' && (
          <>
            <SectionLabel>Overview</SectionLabel>

            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[11px] text-gray-400 dark:text-slate-500 mb-1">Goal</p>
                <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug">
                  {panel.goal}
                </p>
              </div>
              <span className="w-6 h-6 rounded-md bg-indigo-50 dark:bg-indigo-950/40 flex-shrink-0" />
            </div>

            <div className="mt-4">
              <p className="text-[11px] text-gray-400 dark:text-slate-500 mb-2">Focus Areas</p>
              <div className="flex flex-wrap gap-2">
                {panel.focusAreas.map((area) => (
                  <span
                    key={area}
                    className="px-2.5 py-1 rounded-md bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 text-[11px] font-medium"
                  >
                    {area}
                  </span>
                ))}
              </div>
            </div>

            {/* Key metrics */}
            <div className="mt-4">
              <SectionLabel>Key metrics</SectionLabel>
              <div className="grid grid-cols-3 gap-2.5">
                <div className="rounded-xl border border-gray-100 dark:border-slate-800 p-3">
                  <p className="text-[9.5px] text-gray-400 dark:text-slate-500 mb-1">Impact</p>
                  <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-2.5">
                    {panel.impact}
                  </p>
                  <MiniLine series={IMPACT_TREND} />
                </div>

                <div className="rounded-xl border border-gray-100 dark:border-slate-800 p-3">
                  <p className="text-[9.5px] text-gray-400 dark:text-slate-500 mb-1">Frequency</p>
                  <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-2.5">
                    {panel.frequency}
                  </p>
                  <MiniBars series={FREQUENCY_BARS} />
                </div>

                <div className="rounded-xl border border-gray-100 dark:border-slate-800 p-3">
                  <p className="text-[9.5px] text-gray-400 dark:text-slate-500 mb-1">Confidence</p>
                  <div className="mt-2">
                    <MiniRing value={panel.confidence} />
                  </div>
                </div>
              </div>
            </div>

            {/* Recent actions */}
            <div className="mt-4">
              <SectionLabel>Recent actions</SectionLabel>
              <div className="space-y-3">
                {panel.recentActions.map((action) => (
                  <div key={action.label} className="flex items-start gap-3">
                    <span className="w-5 h-5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0 mt-[1px]">
                      <i className={`fa-solid ${action.icon} text-[8px]`} />
                    </span>
                    <div className="min-w-0">
                      <p className="text-[11.5px] font-medium text-gray-800 dark:text-slate-200 leading-snug">
                        {action.label}
                      </p>
                      <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">
                        {action.when}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* ── Goals ── */}
        {tab === 'Goals' && (
          <>
            <SectionLabel>Goal</SectionLabel>
            <p className="text-[13px] font-bold text-gray-900 dark:text-white leading-snug">
              {panel.goal}
            </p>
            <div className="mt-4">
              <SectionLabel>Focus areas</SectionLabel>
              <ul className="space-y-2">
                {panel.focusAreas.map((area) => (
                  <li key={area} className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-[6px] flex-shrink-0" />
                    <span className="text-[11.5px] text-gray-600 dark:text-slate-400">{area}</span>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        {/* ── Metrics ── */}
        {tab === 'Metrics' && (
          <>
            <SectionLabel>Key metrics</SectionLabel>
            <div className="space-y-3">
              {[
                { label: 'Impact', value: panel.impact },
                { label: 'Frequency', value: panel.frequency },
                { label: 'Confidence', value: `${panel.confidence}%` },
              ].map((m) => (
                <div
                  key={m.label}
                  className="flex items-center justify-between gap-3 rounded-xl border border-gray-100 dark:border-slate-800 px-4 py-3"
                >
                  <span className="text-[12px] text-gray-600 dark:text-slate-400">{m.label}</span>
                  <span className="text-[12.5px] font-bold text-gray-900 dark:text-white">
                    {m.value}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* ── Activity ── */}
        {tab === 'Activity' && (
          <>
            <SectionLabel>Recent actions</SectionLabel>
            <div className="space-y-3">
              {panel.recentActions.map((action) => (
                <div key={action.label} className="flex items-start gap-3">
                  <span className="w-5 h-5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0 mt-[1px]">
                    <i className={`fa-solid ${action.icon} text-[8px]`} />
                  </span>
                  <div className="min-w-0">
                    <p className="text-[11.5px] font-medium text-gray-800 dark:text-slate-200 leading-snug">
                      {action.label}
                    </p>
                    <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">
                      {action.when}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={handleChat}
              className="w-full mt-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-[12px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center gap-2"
            >
              <i className="fa-regular fa-comment text-[10px]" /> Chat with {agent.initials}
            </button>
          </>
        )}
      </div>

      {/* ── Commit actions ── */}
      <div className="px-4 pb-4 pt-4 border-t border-gray-100 dark:border-slate-800 space-y-2.5">
        <button
          onClick={onAssign}
          className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-[13px] font-bold transition-colors"
        >
          Assign to workspace
        </button>
        <button
          onClick={onViewProfile}
          className="w-full py-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center gap-2"
        >
          View full profile <i className="fa-solid fa-arrow-up-right-from-square text-[10px]" />
        </button>
      </div>
    </div>
  );
};

export default LiveAgentPanel;
