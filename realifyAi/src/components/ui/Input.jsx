import React from 'react';

const base =
  'w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:text-slate-200';

export const Input = ({ className = '', ...props }) => (
  <input className={`${base} ${className}`} {...props} />
);

export const Select = ({ className = '', children, ...props }) => (
  <select className={`${base} ${className}`} {...props}>
    {children}
  </select>
);

export const Textarea = ({ className = '', ...props }) => (
  <textarea className={`${base} resize-none ${className}`} {...props} />
);
