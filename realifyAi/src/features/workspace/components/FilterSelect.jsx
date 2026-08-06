import React from 'react';
import { pillSurface } from '@/features/workspace/components/filterPillSurface';
import { isFilterOff, multiSelectLabel } from '@/features/workspace/signalFilters';

/**
 * One pill-button filter with a checkable option list — the shape shared by
 * Category, Channel, Status and Advertising on the Workspace filter bar.
 *
 * Pass `multiple` for a multi-select filter: `value` is then an array of chosen
 * values, an empty array means the filter is off, and the first option acts as
 * the "clear" row. Single-select keeps `value` as a plain string.
 *
 * Open state is owned by the bar (only one dropdown open at a time), which also
 * owns the click-outside that closes it.
 */
const FilterSelect = ({
  label,          // shown when nothing is selected, and as the "all" option
  value,
  options,        // [{ value, label }]
  onChange,
  isOpen,
  onToggle,
  width = 'w-[150px]',
  multiple = false,
  surface,        // 'table' tints the pill for a table's filter bar — see pillSurface
}) => {
  // Single-select treats the first option as its neutral value.
  const isDefault = multiple
    ? isFilterOff(value)
    : (!value || value === options[0]?.value);

  const buttonLabel = multiple
    ? multiSelectLabel(label, value, options)
    : (isDefault ? label : options.find((o) => o.value === value)?.label || label);

  const isChecked = (opt, index) => {
    if (!multiple) return value === opt.value;
    // Row 0 is the "All …" row: ticked only while nothing else is.
    return index === 0 ? isDefault : (value || []).includes(opt.value);
  };

  const handleSelect = (opt, index) => {
    if (!multiple) return onChange(opt.value);
    if (index === 0) return onChange([]);          // clear
    const current = value || [];
    onChange(
      current.includes(opt.value)
        ? current.filter((v) => v !== opt.value)
        : [...current, opt.value]
    );
  };

  return (
    <div className="relative" data-filter-dropdown>
      <button
        onClick={onToggle}
        className={`px-3 py-1.5 ${pillSurface(surface)} border rounded-xl text-xs font-semibold focus:outline-none cursor-pointer shadow-2xs flex items-center gap-1.5 transition-colors ${
          isOpen
            ? 'border-blue-600 text-blue-600'
            : isDefault
              ? 'border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700'
              : 'border-blue-200 dark:border-blue-800/60 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30'
        }`}
      >
        {buttonLabel}
        <i className="fa-solid fa-chevron-down text-[10px] opacity-80" />
      </button>

      {isOpen && (
        <div className={`absolute top-full mt-1.5 left-0 ${width} bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-gray-100 dark:border-slate-800 py-1.5 z-50 animate-in fade-in slide-in-from-top-1 duration-150`}>
          {options.map((opt, index) => {
            const checked = isChecked(opt, index);
            return (
              <button
                key={opt.value}
                onClick={() => handleSelect(opt, index)}
                className={`w-full text-left px-4 py-2 text-[13px] font-medium transition-colors flex items-center ${
                  checked
                    ? 'text-blue-600 dark:text-blue-400 font-bold'
                    : 'text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                }`}
              >
                <span className="w-5 flex-shrink-0">
                  {checked && <i className="fa-solid fa-check text-[11px]" />}
                </span>
                <span className="whitespace-nowrap">{opt.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FilterSelect;
