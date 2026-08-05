import React, { useState, useEffect } from 'react';
import { IMPACT_BANDS, EMPTY_SKU_FILTER } from '@/features/workspace/skuFilterOptions';
import {
  useFloating,
  autoUpdate,
  offset,
  flip,
  shift,
  size,
  FloatingPortal,
} from '@floating-ui/react';

/** Same neutral tick the other filter dropdowns use — no coloured checkbox. */
const Tick = ({ checked }) => (
  <span className="w-4 flex-shrink-0 text-gray-900 dark:text-white">
    {checked && <i className="fa-solid fa-check text-[11px]" />}
  </span>
);

const Row = ({ checked, label, onClick }) => (
  <button
    onClick={onClick}
    className="w-full flex items-center gap-2 px-4 py-1.5 text-left text-[13px] font-medium text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
  >
    <Tick checked={checked} />
    <span className="truncate">{label}</span>
  </button>
);

/** Collapsible group header — closed until the user opens it. */
const Section = ({ title, count, isOpen, onToggle, children }) => (
  <>
    <button
      onClick={onToggle}
      className="w-full px-4 py-2 flex items-center gap-1.5 text-[13px] text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
    >
      <i className={`fa-solid fa-caret-${isOpen ? 'down' : 'right'} text-gray-400 text-[10px] w-3 text-center`} />
      <span>{title}</span>
      {count > 0 && (
        <span className="ml-auto rounded-full bg-blue-50 dark:bg-blue-950/50 px-1.5 text-[10px] font-bold text-blue-600 dark:text-blue-400">
          {count}
        </span>
      )}
    </button>
    {isOpen && (
      <div className="pl-4 pb-1 animate-in fade-in slide-in-from-top-1 duration-150">
        {children}
      </div>
    )}
  </>
);

/** Small uppercase divider label, used to group the popup into sections. */
const GroupLabel = ({ children }) => (
  <p className="px-4 pt-2 pb-1 text-[9.5px] font-bold uppercase tracking-widest text-gray-400 dark:text-slate-500">
    {children}
  </p>
);

/**
 * The SKU column's filter popover, laid out in the order a Google Sheets column
 * menu uses: sort, then search, then collapsed filter groups, then visibility,
 * then the commit row.
 */
const SkuFilterPopover = ({
  value,
  onApply,
  isOpen,
  onToggle,
  onClose,
  actionOptions,
}) => {
  const [draft, setDraft] = useState({ ...value });
  const [impactOpen, setImpactOpen] = useState(false);
  const [actionsOpen, setActionsOpen] = useState(false);

  // Reset draft whenever the popover is opened
  useEffect(() => {
    if (isOpen) {
      setDraft({ ...value });
    }
  }, [isOpen, value]);

  const toggleIn = (list, key) =>
    list.includes(key) ? list.filter((k) => k !== key) : [...list, key];

  const set = (patch) => setDraft((d) => ({ ...d, ...patch }));

  const handleApply = () => {
    onApply(draft);
    onClose();
  };

  const sortRow = (key, label) => (
    <button
      onClick={() => set({ sort: draft.sort === key ? null : key })}
      className={`w-full text-left px-4 py-2 text-[13px] hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 ${draft.sort === key ? 'font-bold text-gray-900 dark:text-white' : 'font-medium text-gray-700 dark:text-slate-300'}`}
    >
      <Tick checked={draft.sort === key} />
      {label}
    </button>
  );

  const { refs, floatingStyles } = useFloating({
    open: isOpen,
    onOpenChange: (open) => {
      if (!open) onClose();
    },
    placement: 'bottom-start',
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(6),
      flip({ padding: 12 }),
      shift({ padding: 12 }),
      size({
        apply({ availableWidth, availableHeight, elements }) {
          Object.assign(elements.floating.style, {
            maxWidth: `${Math.max(268, availableWidth)}px`,
            maxHeight: `${Math.max(200, availableHeight - 16)}px`, // prevent overflow
          });
        },
        padding: 12,
      }),
    ],
  });

  return (
    <div className="relative" data-filter-dropdown>
      <button
        ref={refs.setReference}
        onClick={onToggle}
        className={`px-3 py-1.5 bg-white dark:bg-slate-800 border rounded-xl text-xs font-semibold focus:outline-none cursor-pointer shadow-2xs flex items-center gap-1.5 transition-colors ${
          isOpen
            ? 'border-blue-600 text-blue-600'
            : 'border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700'
        }`}
      >
        SKU
        <i className="fa-solid fa-chevron-down text-[10px] opacity-80" />
      </button>

      {isOpen && (
        <FloatingPortal>
          <div
            // floating-ui's setFloating is a stable callback ref, not a ref-value read during render
            // eslint-disable-next-line react-hooks/refs
            ref={refs.setFloating}
            style={{ ...floatingStyles, display: 'flex', flexDirection: 'column' }}
            className="z-50 outline-none"
            data-filter-dropdown
          >
            <div 
              className="w-[268px] bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-gray-100 dark:border-slate-800 py-1.5 flex flex-col animate-in fade-in zoom-in-95 duration-150"
              style={{ overflow: 'hidden' }}
            >
              <div className="overflow-y-auto custom-scrollbar flex-1 min-h-0">
                {/* ── 1. Sort ── */}
                {sortRow('asc', 'Sort A to Z')}
                {sortRow('desc', 'Sort Z to A')}

                <div className="my-1.5 border-t border-gray-100 dark:border-slate-800" />

                {/* ── 2. Search ── */}
                <div className="px-4 py-1">
                  <div className="relative">
                    <input
                      type="text"
                      value={draft.search}
                      onChange={(e) => set({ search: e.target.value })}
                      placeholder="Search"
                      className="w-full bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg pl-3 pr-8 py-1.5 text-[13px] text-gray-800 dark:text-slate-200 placeholder-gray-400 dark:placeholder-slate-500 outline-none focus:border-blue-500 transition-colors"
                    />
                    <i className="fa-solid fa-magnifying-glass absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-[11px] pointer-events-none" />
                  </div>
                </div>

                <div className="my-1.5 border-t border-gray-100 dark:border-slate-800" />

                {/* ── 3. Filters ── */}
                <GroupLabel>Filters</GroupLabel>

                <Section
                  title="Filter by impact"
                  count={draft.impact.length}
                  isOpen={impactOpen}
                  onToggle={() => setImpactOpen((o) => !o)}
                >
                  {IMPACT_BANDS.map((band) => (
                    <Row
                      key={band.key}
                      label={band.label}
                      checked={draft.impact.includes(band.key)}
                      onClick={() => set({ impact: toggleIn(draft.impact, band.key) })}
                    />
                  ))}
                </Section>

                <Section
                  title="Filter by action"
                  count={draft.actions.length}
                  isOpen={actionsOpen}
                  onToggle={() => setActionsOpen((o) => !o)}
                >
                  {actionOptions.map((opt) => (
                    <Row
                      key={opt.key}
                      label={opt.label}
                      checked={draft.actions.includes(opt.key)}
                      onClick={() => set({ actions: toggleIn(draft.actions, opt.key) })}
                    />
                  ))}
                </Section>

                <div className="my-1.5 border-t border-gray-100 dark:border-slate-800" />

                {/* ── 4. Visibility ── */}
                <GroupLabel>Visibility</GroupLabel>
                <Row
                  label="Show Active SKUs"
                  checked={draft.showActive}
                  onClick={() => set({ showActive: !draft.showActive })}
                />
                <Row
                  label="Show Inactive SKUs"
                  checked={draft.showInactive}
                  onClick={() => set({ showInactive: !draft.showInactive })}
                />
              </div>

              {/* ── 5. Footer ── */}
              <div className="pt-2.5 px-3 pb-1 flex flex-wrap justify-between items-center gap-2 border-t border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 flex-shrink-0 mt-1.5">
                <button
                  onClick={() => setDraft({ ...EMPTY_SKU_FILTER })}
                  className="text-[11.5px] font-semibold text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors"
                >
                  Reset Filters
                </button>
                <div className="flex gap-2 ml-auto">
                  <button
                    onClick={onClose}
                    className="px-3.5 py-1.5 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 rounded-lg text-xs font-bold hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleApply}
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors"
                  >
                    Apply
                  </button>
                </div>
              </div>
            </div>
          </div>
        </FloatingPortal>
      )}
    </div>
  );
};

export default SkuFilterPopover;
