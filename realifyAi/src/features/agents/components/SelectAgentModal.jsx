import React, { useEffect, useMemo, useState } from 'react';
import AgentCard from '@/features/agents/components/AgentCard';
import { AGENTS_ROSTER, AGENT_GROUPS } from '@/features/agents/data/agentsData';

/** Shared heading — identical in the prompt and the picker, so it lives once. */
const PromptHeading = () => (
  <div className="flex items-start gap-4">
    <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900/50 flex-shrink-0" />
    <div className="min-w-0">
      <h2 className="text-[17px] font-semibold text-gray-900 dark:text-white leading-snug">
        Select an agent to proceed with the hiring steps.
      </h2>
      <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-1.5">
        There are templates of agents!
      </p>
      <p className="text-[11.5px] text-gray-500 dark:text-slate-400">
        If you want to create an agent yourself{' '}
        <button className="font-bold text-blue-600 dark:text-blue-400 underline underline-offset-2 hover:text-blue-700">
          upgrade to premium
        </button>
        .
      </p>
    </div>
  </div>
);

/**
 * Backdrop shared by both steps: blurs the Hire screen behind the dialog rather
 * than covering it, so the user keeps the context they are about to fill in.
 */
const Backdrop = ({ children, onClose, wide }) => {
  // Escape closes, and the body cannot scroll behind the dialog.
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-white/40 dark:bg-black/50 backdrop-blur-[5px] animate-in fade-in duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className={`w-full bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-800 animate-in fade-in zoom-in-95 duration-200 ${
          wide ? 'max-w-[960px] max-h-[86vh] flex flex-col' : 'max-w-[400px]'
        }`}
      >
        {children}
      </div>
    </div>
  );
};

/** Step 1 — the small prompt: pick from templates, or create your own. */
export const SelectAgentPrompt = ({ onSelectAgent, onCreateAgent, onClose }) => (
  <Backdrop onClose={onClose}>
    <div className="p-5">
      <div className="flex flex-col items-center text-center">
        <div className="w-11 h-11 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900/50 mb-5" />
        <h2 className="text-[17px] font-semibold text-gray-900 dark:text-white leading-snug mb-3">
          Select an agent to proceed with the hiring steps.
        </h2>
        <p className="text-[11.5px] text-gray-500 dark:text-slate-400">
          There are templates of agents!
        </p>
        <p className="text-[11.5px] text-gray-500 dark:text-slate-400">
          If you want to create an agent yourself{' '}
          <button className="font-bold text-blue-600 dark:text-blue-400 underline underline-offset-2 hover:text-blue-700">
            upgrade to premium
          </button>
          .
        </p>
      </div>

      <div className="flex items-center gap-3 mt-4 pt-4 border-t border-gray-100 dark:border-slate-800">
        <button
          onClick={onSelectAgent}
          className="flex-1 py-2.5 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
        >
          Select agent <i className="fa-solid fa-arrow-right text-[11px]" />
        </button>
        <button
          onClick={onCreateAgent}
          className="flex-1 py-2.5 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
        >
          Create agent <i className="fa-solid fa-plus text-[11px]" />
        </button>
      </div>
    </div>
  </Backdrop>
);

/**
 * Step 2 — the picker. Reuses `AgentCard` and the same group/sort/view controls
 * as the Agents page, so a card looks identical in both places.
 */
export const SelectAgentPicker = ({ onPick, onCreateAgent, onClose }) => {
  const [group, setGroup] = useState('All');
  const [view, setView] = useState('grid');
  const [sortAsc, setSortAsc] = useState(true);

  const visible = useMemo(() => {
    const rows = group === 'All' ? AGENTS_ROSTER : AGENTS_ROSTER.filter((a) => a.group === group);
    return [...rows].sort((a, b) =>
      sortAsc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name)
    );
  }, [group, sortAsc]);

  return (
    <Backdrop onClose={onClose} wide>
      {/* Header stays put while the roster scrolls under it */}
      <div className="p-5 pb-4 border-b border-gray-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-start justify-between gap-4 flex-shrink-0">
        <PromptHeading />
        <button
          onClick={onCreateAgent}
          className="px-4 py-2.5 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center gap-2 whitespace-nowrap flex-shrink-0"
        >
          Create agent <i className="fa-solid fa-plus text-[11px]" />
        </button>
      </div>

      <div className="px-5 py-4 flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
          {AGENT_GROUPS.map((g) => (
            <button
              key={g}
              onClick={() => setGroup(g)}
              className={`px-3.5 py-1.5 rounded-lg text-[13px] font-semibold whitespace-nowrap transition-colors ${
                group === g
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800'
              }`}
            >
              {g}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            onClick={() => setSortAsc((v) => !v)}
            className="text-[12.5px] font-medium text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors whitespace-nowrap"
          >
            Sort: {sortAsc ? 'A to Z' : 'Z to A'}
          </button>

          <div className="flex items-center rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
            {[
              { key: 'list', icon: 'fa-list' },
              { key: 'grid', icon: 'fa-table-cells-large' },
            ].map((opt) => (
              <button
                key={opt.key}
                onClick={() => setView(opt.key)}
                aria-label={`${opt.key} view`}
                aria-pressed={view === opt.key}
                className={`w-8 h-7 flex items-center justify-center transition-colors ${
                  view === opt.key
                    ? 'bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-200'
                    : 'text-gray-400 dark:text-slate-500 hover:bg-gray-50 dark:hover:bg-slate-800/60'
                }`}
              >
                <i className={`fa-solid ${opt.icon} text-[11px]`} />
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="px-5 pb-5 overflow-y-auto custom-scrollbar flex-1 min-h-0">
        <div className={view === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 gap-4' : 'space-y-3'}>
          {/* The whole card is the hit target — picking one is the only action
              this dialog exists for. */}
          {visible.map((agent) => (
            <AgentCard key={agent.id} agent={agent} view={view} onSelect={onPick} />
          ))}
        </div>
      </div>
    </Backdrop>
  );
};
