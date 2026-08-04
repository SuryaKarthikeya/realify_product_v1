import React, { useEffect, useRef, useState } from 'react';

/**
 * A dropdown that is real DOM, not a native `<select>`.
 *
 * Why this exists: the option list of a `<select>` is drawn by the operating
 * system, not the page. `color-scheme` can nudge it, but nothing in CSS can
 * actually style it — so on a Mac set to Dark those popups render as black
 * panels over a white app, and no amount of Tailwind reaches inside them. This
 * renders the list ourselves, so it looks the same everywhere and can carry the
 * app's own selected/hover treatment.
 *
 * Promoted out of AssignCoverageStep, which had the only copy of this look.
 *
 * `options` accepts plain strings or `{ id, label }` — string lists are the
 * common case for filters, and normalising here saves every caller mapping.
 */

const normalize = (options = []) =>
  options.map((o) => (typeof o === 'string' ? { id: o, label: o } : o));

const SIZES = {
  md: { trigger: 'py-3 pr-10 text-[13px]', pad: 'pl-4', badgePad: 'pl-12', item: 'px-4 py-2 text-[13px]' },
  sm: { trigger: 'py-2 pr-9 text-[12.5px]', pad: 'pl-3', badgePad: 'pl-10', item: 'px-3 py-1.5 text-[12.5px]' },
};

const SelectMenu = ({
  label,
  value,
  options,
  onChange,
  badge,
  size = 'md',
  className = '',
  buttonClassName = '',
  ariaLabel,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef(null);
  const items = normalize(options);
  const selected = items.find((o) => o.id === value) || items[0];
  const s = SIZES[size] || SIZES.md;

  /* Escape closes, and focus returns nowhere surprising — the trigger is still
     where the user left it. A click-catcher below handles pointer dismissal. */
  useEffect(() => {
    if (!isOpen) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') setIsOpen(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen]);

  return (
    <div className={className} ref={rootRef}>
      {label && (
        <p className="text-[12.5px] font-semibold text-gray-700 dark:text-slate-300 mb-2">{label}</p>
      )}
      <div className="relative">
        {badge}
        <button
          type="button"
          onClick={() => setIsOpen((v) => !v)}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-label={ariaLabel || label}
          className={`w-full text-left appearance-none rounded-xl border bg-white dark:bg-slate-900 font-semibold transition-colors cursor-pointer truncate ${s.trigger} ${
            isOpen ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-200 dark:border-slate-700'
          } text-gray-900 dark:text-white ${badge ? s.badgePad : s.pad} ${buttonClassName}`}
        >
          {selected?.label}
        </button>
        <i
          className={`fa-solid fa-chevron-${isOpen ? 'up' : 'down'} text-[10px] text-gray-400 absolute ${
            size === 'sm' ? 'right-3.5' : 'right-4'
          } top-1/2 -translate-y-1/2 pointer-events-none`}
        />

        {isOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
            {/* Capped and scrollable: a long list (every feed a connector has)
                would otherwise run off the bottom of the viewport. */}
            <div
              role="listbox"
              className="absolute top-full mt-2 left-0 w-full min-w-[160px] max-h-[280px] overflow-y-auto custom-scrollbar bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-gray-100 dark:border-slate-800 py-1.5 z-50 animate-in fade-in slide-in-from-top-1 duration-150"
            >
              {items.map((o) => {
                const isSelected = o.id === value;
                return (
                  <button
                    key={o.id}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => { onChange?.(o.id); setIsOpen(false); }}
                    className={`w-full text-left font-medium transition-colors flex items-center ${s.item} ${
                      isSelected
                        ? 'text-blue-600 dark:text-blue-400 font-bold bg-blue-50/50 dark:bg-slate-800/50'
                        : 'text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <span className="w-5 flex-shrink-0">
                      {isSelected && <i className="fa-solid fa-check text-[11px]" />}
                    </span>
                    <span className="truncate">{o.label}</span>
                  </button>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SelectMenu;
