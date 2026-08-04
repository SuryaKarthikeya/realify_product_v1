import React from 'react';
import {
  agentTriggers,
  SIGNAL_DOMAIN_TONES,
  HARD_GATES,
} from '@/features/agents/data/agentProfileData';

/**
 * The Triggers tab — the signal engine behind a specialist.
 *
 * Each card reads left to right as source → trigger → role-steered response →
 * auto / human line, which is the caption in the header. The `handoff` line is
 * always rendered: a signal the agent can act on with no escalation boundary
 * would be a gap in the trust contract, not a tidier card.
 */
const TriggersTab = ({ agent }) => {
  const signals = agentTriggers(agent);

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
        <h2 className="text-[16px] font-bold text-gray-900 dark:text-white tracking-tight">
          The {signals.length}-signal engine
        </h2>
        <p className="text-[11.5px] text-gray-400 dark:text-slate-500">
          Source → trigger → role-steered response → auto / human line
        </p>
      </div>

      <div className="space-y-3">
        {signals.map((signal, idx) => (
          <button
            key={signal.key}
            className="w-full text-left rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-5 py-4 flex items-start gap-4 hover:border-gray-300 dark:hover:border-slate-700 transition-colors"
          >
            <span className="text-[12px] font-medium text-gray-400 dark:text-slate-500 w-4 pt-4 flex-shrink-0 tabular">
              {idx + 1}
            </span>

            <span className="w-10 h-10 rounded-xl bg-gray-50 dark:bg-slate-800 text-gray-500 dark:text-slate-400 flex items-center justify-center flex-shrink-0 mt-0.5">
              <i className={`fa-solid ${signal.icon} text-[13px]`} />
            </span>

            <span className="min-w-0 flex-1">
              <span className="flex items-start justify-between gap-3">
                <span className="block text-[13.5px] font-bold text-gray-900 dark:text-white leading-snug">
                  {signal.title}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[9.5px] font-bold whitespace-nowrap flex-shrink-0 ${
                    SIGNAL_DOMAIN_TONES[signal.domain] || SIGNAL_DOMAIN_TONES.Sales
                  }`}
                >
                  {signal.domain}
                </span>
              </span>

              <span className="block text-[12px] text-gray-400 dark:text-slate-500 leading-relaxed mt-1">
                Source — {signal.source}
                <span className="mx-2 text-gray-200 dark:text-slate-700">|</span>
                Trigger — {signal.trigger}
              </span>

              <span className="block text-[12.5px] font-bold text-gray-800 dark:text-slate-200 leading-snug mt-2">
                Response — {signal.response}
              </span>

              <span className="flex items-baseline gap-x-4 gap-y-1 flex-wrap mt-1.5">
                <span className="text-[11.5px] text-gray-600 dark:text-slate-400">
                  <span className="font-bold text-gray-800 dark:text-slate-200">Auto:</span>{' '}
                  {signal.auto}
                </span>
                <span className="w-4 h-[1px] bg-gray-200 dark:bg-slate-700 hidden sm:block" />
                <span className="text-[11.5px] text-gray-600 dark:text-slate-400">
                  <span className="font-bold text-gray-800 dark:text-slate-200">Handoff:</span>{' '}
                  {signal.handoff}
                </span>
              </span>
            </span>

            <i className="fa-solid fa-chevron-right text-[10px] text-gray-300 dark:text-slate-600 flex-shrink-0 mt-4" />
          </button>
        ))}
      </div>

      {/* Hard gates hold at every autonomy level, including Act */}
      <div className="rounded-2xl bg-gray-50/70 dark:bg-slate-800/30 border border-gray-100 dark:border-slate-800 px-5 py-4">
        <p className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-3.5">
          Hard gates — server-side, autonomy-independent:
        </p>
        <div className="flex flex-wrap gap-x-7 gap-y-2.5">
          {HARD_GATES.map((gate) => (
            <span key={gate} className="flex items-center gap-2">
              <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-slate-600 flex-shrink-0" />
              <span className="text-[12.5px] font-semibold text-gray-800 dark:text-slate-200">
                {gate}
              </span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TriggersTab;
