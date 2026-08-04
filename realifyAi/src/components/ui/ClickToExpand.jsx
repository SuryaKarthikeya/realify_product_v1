import React from 'react';

const ClickToExpand = ({ className = 'mt-auto' }) => (
  <p className={`text-[10px] text-center text-gray-400 dark:text-slate-500 ${className} font-medium group-hover:text-gray-700 dark:group-hover:text-gray-300 transition-colors`}>
    <i className="fa-solid fa-expand mr-1"></i>Click to expand
  </p>
);

export default ClickToExpand;
