import React from 'react';
import { agentStatusLabel } from '@/features/agents/data/agentsData';

/**
 * One specialist. Two layouts off the same data:
 *  - grid: avatar + name/meta on one line, description, then the ramp footer
 *  - list: the same content on a single row, for the list/grid toggle
 *
 * The footer is pinned to the bottom (`mt-auto`) so the ramp line sits on one
 * baseline across a row of cards even when descriptions wrap differently.
 */
const AgentCard = ({ agent, view = 'grid', onSelect, isSelected = false }) => {
  /* Derived from the ramp, not from `status` — the badge has to agree with the
     "Day x of y" line directly beneath it. */
  const statusLabel = agentStatusLabel(agent);
  const isActive = statusLabel === 'Active';

  /* The open card keeps a visible tie to the panel beside it. */
  const selectedRing = isSelected
    ? 'border-indigo-400 dark:border-indigo-600 ring-1 ring-indigo-200 dark:ring-indigo-800'
    : 'border-gray-200 dark:border-slate-800 hover:border-gray-300 dark:hover:border-slate-700';

  /* When the card is selectable the root itself is the hit target. It stays a
     `div` with a button role rather than a real <button>, because the kebab is
     already a button and nesting one inside another is invalid HTML. */
  const selectable = onSelect
    ? {
        onClick: () => onSelect(agent),
        onKeyDown: (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(agent); }
        },
        role: 'button',
        tabIndex: 0,
        className:
          'cursor-pointer hover:-translate-y-0.5 focus-visible:outline-none ' +
          'focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 ' +
          'dark:focus-visible:ring-offset-slate-900',
      }
    : { className: '' };

  const avatar = (
    <div className="relative flex-shrink-0">
      <div className="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-[11px] font-bold tracking-tight">
        {agent.initials}
      </div>
      {/* Selected card gets a tick on its avatar, so the tie to the open panel
          reads even when the border is off-screen. */}
      {isSelected && (
        <span className="absolute -top-1.5 -left-1.5 w-4 h-4 rounded-full bg-indigo-600 text-white flex items-center justify-center ring-2 ring-white dark:ring-slate-900">
          <i className="fa-solid fa-check text-[7px]" />
        </span>
      )}
    </div>
  );

  const statusBadge = (
    <span
      className={`px-2 py-0.5 rounded text-[9.5px] font-bold uppercase tracking-wider whitespace-nowrap ${
        isActive
          ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400'
          : 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'
      }`}
    >
      {statusLabel}
    </span>
  );

  const kebab = (
    <button
      onClick={(e) => e.stopPropagation()}
      className="w-6 h-6 -mr-1 rounded-md flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex-shrink-0"
      aria-label={`More options for ${agent.name}`}
    >
      <i className="fa-solid fa-ellipsis-vertical text-[12px]" />
    </button>
  );

  const rampFooter = (
    <>
      <p className="text-[10.5px] text-gray-400 dark:text-slate-500">
        {agent.phase} • Day {agent.rampDay} of {agent.rampTotal}
      </p>
      <p className="text-[11.5px] font-bold text-gray-900 dark:text-white mt-0.5">
        starts at {agent.startsAt}
      </p>
    </>
  );

  if (view === 'list') {
    return (
      <div {...selectable} className={`bg-white dark:bg-slate-900 border rounded-2xl px-4 py-3 flex items-center gap-3.5 transition-all ${selectedRing} ${selectable.className}`}>
        {avatar}

        <div className="min-w-0 w-[190px] flex-shrink-0">
          <p className="text-[13.5px] font-bold text-gray-900 dark:text-white leading-snug truncate">
            {agent.name}
          </p>
          <p className="text-[11px] text-gray-400 dark:text-slate-500 truncate">{agent.meta}</p>
        </div>

        <p className="text-[12.5px] text-gray-600 dark:text-slate-400 leading-snug flex-1 min-w-0 truncate">
          {agent.description}
        </p>

        <div className="hidden lg:block text-right flex-shrink-0">{rampFooter}</div>

        {statusBadge}
        {kebab}
      </div>
    );
  }

  return (
    <div {...selectable} className={`bg-white dark:bg-slate-900 border rounded-2xl p-4 flex flex-col transition-all ${selectedRing} ${selectable.className}`}>
      <div className="flex items-start gap-3">
        {avatar}

        <div className="min-w-0 flex-1">
          <p className="text-[13.5px] font-bold text-gray-900 dark:text-white leading-snug">
            {agent.name}
          </p>
          <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-snug mt-0.5">
            {agent.meta}
          </p>
        </div>

        <div className="flex items-start gap-1.5 flex-shrink-0">
          {statusBadge}
          {kebab}
        </div>
      </div>

      <p className="text-[12.5px] text-gray-600 dark:text-slate-400 leading-relaxed mt-3">
        {agent.description}
      </p>

      <div className="mt-auto pt-3">
        <div className="border-t border-gray-100 dark:border-slate-800 pt-2.5">{rampFooter}</div>
      </div>
    </div>
  );
};

export default React.memo(AgentCard);
