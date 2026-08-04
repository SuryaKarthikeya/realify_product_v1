import React from 'react';

const variantStyles = {
  primary: 'bg-brand hover:bg-brand-hover text-white shadow-sm dark:bg-brand dark:hover:bg-brand-hover',
  secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300',
  outline: 'border border-gray-300 hover:bg-gray-50 text-gray-700 dark:border-slate-700 dark:hover:bg-slate-800 dark:text-slate-300',
  ghost: 'hover:bg-gray-100 text-gray-600 dark:hover:bg-slate-800 dark:text-slate-400',
  danger: 'bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400'
};

const sizeStyles = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base'
};

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className = '', 
  ...props 
}) => {
  return (
    <button 
      className={`font-medium rounded-lg transition-colors inline-flex items-center justify-center ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
