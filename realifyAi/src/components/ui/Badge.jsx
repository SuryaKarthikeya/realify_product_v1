import React from 'react';

const variantStyles = {
  default: 'bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-slate-300',
  primary: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  success: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  danger: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  processing: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
};

const Badge = ({ children, variant = 'default', className = '' }) => {
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider inline-flex items-center justify-center ${variantStyles[variant]} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;
