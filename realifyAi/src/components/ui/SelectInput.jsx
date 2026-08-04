import React from 'react';

// The filter-bar "select" look shared by PageHeader and GlobalAppHeader's
// default filter row. Callers with a different look (different padding,
// background, etc.) pass their own `className`, which fully replaces this
// default rather than being appended — appending would leave conflicting
// Tailwind utilities (e.g. two different `dark:bg-*` classes) in the same
// class list, and the effective style would depend on stylesheet order.
const DEFAULT_CLASS = 'px-3 py-1.5 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-semibold text-gray-700 dark:text-slate-300 focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 outline-none transition-colors hover:border-gray-300 dark:hover:border-slate-600 shadow-sm';

const SelectInput = ({ className, children, ...props }) => (
  <select className={className ?? DEFAULT_CLASS} {...props}>
    {children}
  </select>
);

export default SelectInput;
