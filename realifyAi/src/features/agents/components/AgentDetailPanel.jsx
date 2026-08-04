import React from 'react';
import { useAIStore } from '@/store/useAIStore';
import {
  agentDetail,
  TRUST_RUNGS,
  GRADUATION_GATES,
} from '@/features/agents/data/agentDetailData';

/** Section heading, with the optional info affordance the design shows. */
const SectionTitle = ({ children, info }) => (
  <div className="flex items-center justify-between gap-2 mb-3">
    <h3 className="text-[12.5px] font-bold text-gray-900 dark:text-white">{children}</h3>
    {info && (
      <button
        className="text-gray-300 dark:text-slate-600 hover:text-gray-500 dark:hover:text-slate-400 transition-colors flex-shrink-0"
        aria-label="About this section"
      >
        <i className="fa-regular fa-circle-question text-[11px]" />
      </button>
    )}
  </div>
);

/** Dotted list used by Responsibilities and After Graduation. */
const DotList = ({ items, tone }) => (
  <ul className="space-y-2">
    {items.filter(Boolean).map((item, idx) => (
      <li key={idx} className="flex items-start gap-2.5">
        <span
          className={`w-1.5 h-1.5 rounded-full mt-[5px] flex-shrink-0 ${
            tone === 'emerald' ? 'bg-emerald-500' : 'bg-indigo-500'
          }`}
        />
        <span className="text-[11.5px] text-gray-600 dark:text-slate-400 leading-relaxed">
          {item}
        </span>
      </li>
    ))}
  </ul>
);

/** Marker for a task row: complete, in flight, or not started. */
const TaskMarker = ({ state }) => {
  if (state === 'done') {
    return (
      <span className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center flex-shrink-0">
        <i className="fa-solid fa-check text-[9px]" />
      </span>
    );
  }
  if (state === 'active') {
    return (
      <span className="w-5 h-5 rounded-full border-2 border-indigo-500 flex items-center justify-center flex-shrink-0">
        <span className="w-2 h-2 rounded-full bg-indigo-600" />
      </span>
    );
  }
  return (
    <span className="w-5 h-5 rounded-full border-2 border-gray-200 dark:border-slate-700 flex items-center justify-center flex-shrink-0">
      <span className="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-slate-600" />
    </span>
  );
};

const TASK_ROW_TONES = {
  done: 'bg-emerald-50/60 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/40',
  active: 'bg-indigo-50/60 dark:bg-indigo-950/20 border-indigo-100 dark:border-indigo-900/40',
  waiting: 'bg-gray-50/70 dark:bg-slate-800/40 border-gray-100 dark:border-slate-800',
};

/**
 * Right-hand detail panel for one specialist.
 *
 * Deliberately has no internal scroller — the panel grows with its content and
 * the page scrolls, so nothing here is trapped behind a second scrollbar.
 */
const AgentDetailPanel = ({ agent, onClose, onAssign, onViewProfile, onViewDecisions }) => {
  const addAiReference = useAIStore((s) => s.addAiReference);
  const setAiPromptValue = useAIStore((s) => s.setAiPromptValue);

  const detail = agentDetail(agent);
  if (!detail) return null;

  const rampPct = Math.round((detail.rampDay / detail.rampTotal) * 100);

  /**
   * "Chat with X" — attach this specialist to the prompt box at the bottom of
   * the page as a context chip, then focus it so the user can type straight
   * away. The chip carries the agent's live state, not just its name, so the
   * question is answered against where the specialist actually is.
   */
  const handleChat = () => {
    addAiReference({
      title: `${agent.name} · ${detail.phase} day ${detail.rampDay}/${detail.rampTotal}`,
      value: [
        `Specialist: ${agent.name} (${agent.initials})`,
        `Scope: ${agent.meta}`,
        `Group: ${agent.group}`,
        `Phase: ${detail.phase} — day ${detail.rampDay} of ${detail.rampTotal}`,
        `This week: ${detail.weekly.proposed} proposed, ${detail.weekly.accepted} accepted, ${detail.weekly.approval} approval`,
        `Working on: ${detail.workingOn.map((t) => t.label).join('; ')}`,
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
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 font-sans">

      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-3">
        <span className="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-[9px] font-bold uppercase tracking-wider">
          Agent
        </span>
        <div className="flex items-center gap-2.5 flex-shrink-0">
          <span className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider whitespace-nowrap">
            Hired {detail.hiredOn}
          </span>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
            aria-label="Close agent details"
          >
            <i className="fa-solid fa-xmark text-[13px]" />
          </button>
        </div>
      </div>

      <h2 className="text-[19px] font-bold text-gray-900 dark:text-white tracking-tight mt-3">
        {agent.name}
      </h2>

      <div className="flex items-center gap-2 flex-wrap mt-2.5">
        <span className="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-[10px] font-bold">
          {agent.initials}
        </span>
        {agent.meta.split(' • ').map((part) => (
          <span
            key={part}
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300 text-[10.5px] font-medium"
          >
            <i className="fa-solid fa-layer-group text-[8px] opacity-60" />
            {part}
          </span>
        ))}
      </div>

      {/* ── Ramp progress ── */}
      <div className="mt-4 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 px-3.5 py-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="w-5 h-5 rounded-md bg-indigo-600 text-white flex items-center justify-center flex-shrink-0">
              <i className="fa-solid fa-play text-[8px]" />
            </span>
            <span className="text-[11px] font-bold text-gray-900 dark:text-white uppercase tracking-wider">
              {detail.phase}
            </span>
          </div>
          <span className="text-[10.5px] font-medium text-gray-500 dark:text-slate-400 whitespace-nowrap">
            Day {detail.rampDay} of {detail.rampTotal}
          </span>
        </div>
        <div className="mt-2.5 h-1.5 rounded-full bg-indigo-100 dark:bg-indigo-900/60 overflow-hidden">
          <div className="h-full rounded-full bg-indigo-600" style={{ width: `${rampPct}%` }} />
        </div>
      </div>

      {/* ── Weekly performance ── */}
      <div className="mt-4">
        <SectionTitle info>Weekly Performance</SectionTitle>
        <div className="grid grid-cols-3 gap-2">
          {[
            { value: detail.weekly.proposed, label: 'Suggestions proposed', cls: 'text-gray-900 dark:text-white' },
            { value: detail.weekly.accepted, label: 'Accepted this week', cls: 'text-emerald-600 dark:text-emerald-400' },
            { value: detail.weekly.approval, label: 'Approval rate accepted/prop', cls: 'text-indigo-600 dark:text-indigo-400' },
          ].map((tile) => (
            <div
              key={tile.label}
              className="rounded-xl border border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-3 text-center"
            >
              <p className={`text-[19px] font-bold leading-none ${tile.cls}`}>{tile.value}</p>
              <p className="text-[8px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider leading-tight mt-2">
                {tile.label}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Responsibilities ── */}
      <div className="mt-4">
        <SectionTitle>Responsibilities</SectionTitle>
        <DotList items={detail.responsibilities} />
      </div>

      {/* ── Currently working on ── */}
      <div className="mt-4">
        <SectionTitle>Currently Working On</SectionTitle>
        <div className="space-y-2">
          {detail.workingOn.map((task) => (
            <div
              key={task.label}
              className={`flex items-start gap-3 px-3.5 py-3 rounded-xl border ${TASK_ROW_TONES[task.state]}`}
            >
              <TaskMarker state={task.state} />
              <div className="min-w-0">
                <p className="text-[11.5px] font-bold text-gray-900 dark:text-white leading-snug">
                  {task.label}
                </p>
                <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">{task.status}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── After graduation ── */}
      <div className="mt-4">
        <SectionTitle>After Graduation</SectionTitle>
        <DotList items={detail.afterGraduation} tone="emerald" />
      </div>

      {/* ── Trust progress ── */}
      <div className="mt-4">
        <SectionTitle info>Trust Progress</SectionTitle>

        <div className="grid grid-cols-5 relative">
          {/* Hairline behind the markers, inset so it stops at the outer dots */}
          <div className="absolute top-[9px] left-[10%] right-[10%] h-[1px] bg-gray-200 dark:bg-slate-700" />

          {TRUST_RUNGS.map((rung, idx) => {
            const isDone = idx < detail.trustIndex;
            const isActive = idx === detail.trustIndex;
            return (
              <div key={rung.key} className="flex flex-col items-center text-center px-0.5 relative z-10">
                <div
                  className={`w-[19px] h-[19px] rounded-full flex items-center justify-center text-[9px] font-bold mb-2 ${
                    isDone
                      ? 'bg-emerald-500 text-white'
                      : isActive
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-400 dark:text-slate-500'
                  }`}
                >
                  {isDone ? <i className="fa-solid fa-check text-[7px]" /> : idx + 1}
                </div>
                <p
                  className={`text-[8.5px] font-bold leading-tight ${
                    isDone || isActive
                      ? 'text-gray-900 dark:text-white'
                      : 'text-gray-400 dark:text-slate-500'
                  }`}
                >
                  {rung.label}
                </p>
                <p className="text-[7.5px] text-gray-400 dark:text-slate-500 leading-tight">
                  {rung.sub}
                </p>
              </div>
            );
          })}
        </div>

        {/* Gates — once the dial reaches Graduate they have all cleared, so the
            box reports that instead of still asking for five more reviews. */}
        {detail.canGraduate ? (
          <div className="mt-4 rounded-xl border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/40 dark:bg-emerald-950/20 px-4 py-3.5">
            <p className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-2.5">
              Cleared to graduate
            </p>
            <ul className="space-y-2">
              {GRADUATION_GATES.map((gate) => (
                <li key={gate.label} className="flex items-center gap-2.5">
                  <i className="fa-solid fa-circle-check text-[10px] text-emerald-500 w-3.5 text-center flex-shrink-0" />
                  <span className="text-[11px] text-gray-600 dark:text-slate-400">{gate.label}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="mt-4 rounded-xl border border-indigo-100 dark:border-indigo-900/40 bg-indigo-50/40 dark:bg-indigo-950/20 px-4 py-3.5">
            <p className="text-[9px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-2.5">
              What's needed to graduate
            </p>
            <ul className="space-y-2">
              {GRADUATION_GATES.map((gate) => (
                <li key={gate.label} className="flex items-center gap-2.5">
                  <i className={`fa-solid ${gate.icon} text-[10px] text-gray-400 dark:text-slate-500 w-3.5 text-center flex-shrink-0`} />
                  <span className="text-[11px] text-gray-600 dark:text-slate-400">{gate.label}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex items-center gap-2.5 mt-4">
          <button
            onClick={handleChat}
            className="px-3.5 py-2 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[11.5px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap"
          >
            <i className="fa-regular fa-comment text-[10px]" /> Chat with {agent.initials}
          </button>
          <button
            onClick={onViewDecisions}
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-[11.5px] font-bold transition-colors flex items-center gap-2 whitespace-nowrap"
          >
            View decisions <i className="fa-solid fa-arrow-right text-[10px]" />
          </button>
        </div>
      </div>

      {/* ── Commit actions ── */}
      <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-800 space-y-2.5">
        {/* Locked until the trust dial reaches Graduate. A specialist still in
            Shadow only proposes for review, so there is nothing to hand over —
            and going live early is the one mistake here that costs real money. */}
        <button
          onClick={onAssign}
          disabled={!detail.canGraduate}
          title={
            detail.canGraduate
              ? `Make ${agent.name} live in your workspace`
              : `${agent.name} graduates on day ${detail.rampTotal} — day ${detail.rampDay} of ${detail.rampTotal} today`
          }
          className={`w-full py-2.5 rounded-xl text-[13px] font-bold transition-colors ${
            detail.canGraduate
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-gray-100 dark:bg-slate-800 text-gray-400 dark:text-slate-500 cursor-not-allowed'
          }`}
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

export default AgentDetailPanel;
