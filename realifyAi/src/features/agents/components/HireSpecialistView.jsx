import React from 'react';
import {
  HIRE_STEPS,
  TRUST_LADDER,
  hireProfile,
} from '@/features/agents/data/hireSpecialistData';

/**
 * Section shell — every panel on this screen shares the frame and title row.
 *
 * Pass `onClick` to turn a panel into a control that advances the flow. It stays
 * a `div` with a button role rather than a real `<button>` so a panel carrying
 * its own kebab or trailing icon never nests one button inside another.
 */
const Panel = ({ title, titleSuffix, icon, trailingIcon, footnote, onClick, children }) => {
  const clickable = onClick
    ? {
        onClick,
        onKeyDown: (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(e); }
        },
        role: 'button',
        tabIndex: 0,
        className:
          'cursor-pointer hover:border-indigo-300 dark:hover:border-indigo-700 ' +
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ' +
          'focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900',
      }
    : { className: '' };

  return (
  <div
    {...clickable}
    className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col transition-colors ${clickable.className}`}
  >
    <div className="flex items-start justify-between gap-3 mb-5">
      <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white flex items-center gap-2">
        {icon && <i className={`fa-solid ${icon} text-[12px] text-gray-400 dark:text-slate-500`} />}
        {title}
        {titleSuffix && (
          <span className="font-semibold text-gray-400 dark:text-slate-500">{titleSuffix}</span>
        )}
      </h3>
      {trailingIcon && (
        <button className="text-gray-300 dark:text-slate-600 hover:text-gray-500 dark:hover:text-slate-400 transition-colors flex-shrink-0">
          <i className={`fa-solid ${trailingIcon} text-[12px]`} />
        </button>
      )}
    </div>

    <div className="flex-1">{children}</div>

    {footnote && (
      <p className="text-[10.5px] italic text-gray-400 dark:text-slate-500 leading-relaxed mt-4 pt-4 border-t border-gray-100 dark:border-slate-800">
        {footnote}
      </p>
    )}
  </div>
  );
};

/** Kebab used on each playbook row. */
const RowKebab = () => (
  <button className="w-5 flex-shrink-0 text-gray-300 dark:text-slate-600 hover:text-gray-500 dark:hover:text-slate-400 transition-colors">
    <i className="fa-solid fa-ellipsis-vertical text-[11px]" />
  </button>
);

/**
 * The full "Hire a specialist" screen (Step 3 of the five-step flow).
 *
 * `currentStep` is an index into HIRE_STEPS: everything before it reads as
 * complete, the index itself as active, everything after as pending — so the
 * rail advances from data alone.
 */
const HireSpecialistView = ({
  agent,
  currentStep = 2,
  onCancel,
  onContinue,
  onViewAll,
  onViewAgents,
  onEditScope,
}) => {
  // Scope and playbook belong to the specialist being hired, not to a fixture.
  const { tagline, scope, playbook } = hireProfile(agent);

  return (
  <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 space-y-5 font-sans">

    {/* ── Header ── */}
    <div className="flex justify-end">
      <button
        onClick={onViewAll}
        className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50/60 dark:hover:bg-indigo-950/30 transition-colors flex items-center gap-2 whitespace-nowrap flex-shrink-0"
      >
        <i className="fa-solid fa-users text-[12px]" /> View all specialists
      </button>
    </div>

    {/* ── Five-step rail ── */}
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-y-6 relative mt-10 mb-12">
      {/* One hairline behind the markers, inset so it never pokes past the ends */}
      <div className="hidden lg:block absolute top-[13px] left-[10%] right-[10%] h-[1px] bg-gray-200 dark:bg-slate-700" />

      {HIRE_STEPS.map((step, idx) => {
        const isDone = idx < currentStep;
        const isActive = idx === currentStep;
        return (
          <div key={step.key} className="flex flex-col items-center text-center px-3 relative z-10">
            <div
              className={`w-[26px] h-[26px] rounded-full flex items-center justify-center text-[11px] font-bold mb-2.5 flex-shrink-0 ${isDone
                ? 'bg-emerald-500 text-white'
                : isActive
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-400 dark:text-slate-500'
                }`}
            >
              {isDone ? <i className="fa-solid fa-check text-[10px]" /> : idx + 1}
            </div>

            <p
              className={`text-[12.5px] font-bold mb-1.5 ${isActive
                ? 'text-gray-900 dark:text-white'
                : isDone
                  ? 'text-gray-900 dark:text-white'
                  : 'text-gray-400 dark:text-slate-500'
                }`}
            >
              {step.label}
            </p>
            <p className="text-[10.5px] text-gray-400 dark:text-slate-500 leading-relaxed max-w-[170px]">
              {step.description}
            </p>
          </div>
        );
      })}
    </div>

    {/* ── Three detail panels ── */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

      {/* 1. Selected specialist & scope */}
      <Panel
        title="Selected Specialist & Scope"
        trailingIcon="fa-sliders"
        footnote="Scope binds every tab · tighten-only below this node"
      >
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0 text-[11px] font-bold tracking-tight">
            {agent?.initials || 'PR'}
          </div>
          <div className="min-w-0">
            <p className="text-[13.5px] font-bold text-gray-900 dark:text-white leading-snug">
              {agent?.name || 'Pricing & Margin'}
            </p>
            <p className="text-[11px] text-gray-400 dark:text-slate-500">
              {tagline}
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between mb-3">
          <p className="text-[12.5px] font-semibold text-gray-700 dark:text-slate-300">Coverage</p>
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-[10.5px] font-bold text-emerald-700 dark:text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> All channels
          </span>
        </div>

        {/* Scope tree — indent comes from `depth` so the shape is data-driven */}
        <div className="space-y-1.5">
          {scope.map((node) => (
            <div
              key={node.label}
              className="flex items-center gap-1.5"
              style={{ paddingLeft: `${node.depth * 18}px` }}
            >
              {node.isLeaf ? (
                <span className="px-3 py-1.5 rounded-r-md bg-indigo-50/70 dark:bg-indigo-950/40 border-l-2 border-indigo-500 text-[12px] font-semibold text-gray-800 dark:text-slate-200">
                  {node.label}
                </span>
              ) : (
                <>
                  <i className="fa-solid fa-chevron-down text-[8px] text-gray-400 dark:text-slate-500 w-2.5" />
                  <i className={`fa-solid ${node.icon} text-[10px] text-gray-400 dark:text-slate-500`} />
                  <span className="text-[12px] font-medium text-gray-700 dark:text-slate-300">
                    {node.label}
                  </span>
                </>
              )}
            </div>
          ))}
        </div>

        <button
          onClick={onEditScope}
          className="w-full mt-5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-[12.5px] font-semibold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center gap-2"
        >
          <i className="fa-solid fa-pencil text-[10px]" /> Edit scope
        </button>
      </Panel>

      {/* 2. Rules & playbook */}
      <Panel
        title="Rules & Playbook"
        trailingIcon="fa-sliders"
        footnote="Resolved once per run · hard gates tighten-only"
      >
        <div className="space-y-2.5">
          {playbook.map((rule) => (
            <div
              key={rule.key}
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900"
            >
              <div className="min-w-0 flex-1">
                <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug">
                  {rule.label}
                </p>
                <p className="text-[10.5px] text-gray-400 dark:text-slate-500 mt-0.5">
                  {rule.origin}
                </p>
              </div>
              <p className="text-[12px] font-semibold text-gray-800 dark:text-slate-200 whitespace-nowrap">
                {rule.value}
              </p>
              <RowKebab />
            </div>
          ))}
        </div>
      </Panel>

      {/* 3. Trust contract — a second way into the next step, since the trust
             ladder is what the coverage screen actually asks the user to set. */}
      <Panel
        title="Trust Contract"
        titleSuffix="(Step 4 Preview)"
        icon="fa-shield-halved"
        footnote="The record earns the dial — promotion is explicit; demotion is one click."
        onClick={onContinue}
      >
        <div className="relative">
          {/* Rail stops at the last marker rather than running to the container
              floor, so it reads as a ladder with a defined end. */}
          <div className="absolute left-[5.5px] top-2 bottom-3 w-[3px] rounded-full bg-indigo-100 dark:bg-indigo-950/60" />

          <div className="space-y-6">
            {TRUST_LADDER.map((rung, idx) => {
              const isReached = idx === 0;
              return (
                <div key={rung.key} className="relative pl-6">
                  <span
                    className={`absolute left-0 top-[3px] w-3.5 h-3.5 rounded-full ${isReached
                      ? 'bg-indigo-600'
                      : 'bg-white dark:bg-slate-900 border-2 border-gray-200 dark:border-slate-700'
                      }`}
                  />
                  <div className="flex items-center gap-2 flex-wrap">
                    <p
                      className={`text-[12.5px] font-bold ${isReached ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-slate-400'
                        }`}
                    >
                      {rung.label}
                    </p>
                    {rung.badge && (
                      <span className="px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-[9px] font-bold tracking-wider">
                        {rung.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-relaxed mt-1">
                    {rung.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </Panel>
    </div>

    {/* ── Deploy banner ── */}
    <div className="bg-gray-50/70 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 rounded-2xl px-5 py-4 flex flex-col lg:flex-row lg:items-start justify-between gap-4">
      <div className="flex items-start gap-3.5">
        <div className="w-8 h-8 rounded-lg bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 flex items-center justify-center flex-shrink-0 text-gray-500 dark:text-slate-400">
          <i className="fa-regular fa-clock text-[13px]" />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-bold text-gray-900 dark:text-white mb-1">
            Step {HIRE_STEPS.length} – Deploy in Shadow
          </p>
          <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed max-w-[560px]">
            The specialist goes live in Shadow Mode against yesterday's real data — first
            would-have-done proposals appear on the Feed within one loop.
          </p>
        </div>
      </div>

      <p className="text-[11.5px] text-gray-400 dark:text-slate-500 lg:text-right leading-relaxed flex-shrink-0">
        Nothing writes to a channel until the{' '}
        <span className="text-indigo-600 dark:text-indigo-400 font-semibold">record earns it</span>.
      </p>
    </div>

    {/* ── Step actions ── */}
    <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100 dark:border-slate-800">
      <button
        onClick={onCancel}
        className="px-5 py-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
      >
        Cancel
      </button>
      {/* On the last step this commits the hire rather than advancing, so the
          label says so — "Continue to next step" would promise a step that does
          not exist. */}
      <button
        onClick={onContinue}
        className="px-5 py-2.5 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center gap-2"
      >
        {currentStep >= HIRE_STEPS.length - 1 ? (
          <>Graduate specialist <i className="fa-solid fa-check text-[11px]" /></>
        ) : (
          <>Continue to next step <i className="fa-solid fa-arrow-right text-[11px]" /></>
        )}
      </button>
    </div>

    {/* ── View agents CTA ── */}
    <button
      onClick={onViewAgents}
      className="w-full rounded-2xl border-2 border-blue-600 dark:border-blue-500 bg-blue-50/30 dark:bg-blue-950/20 py-7 px-5 text-center hover:bg-blue-50/60 dark:hover:bg-blue-950/30 transition-colors"
    >
      <p className="text-[16px] font-bold text-blue-600 dark:text-blue-400 mb-1.5">View Agents</p>
      <p className="text-[12.5px] text-gray-500 dark:text-slate-400">
        There are agent templates that you can use for your work, and you can configure them as well.
      </p>
    </button>
  </div>
  );
};

export default HireSpecialistView;
