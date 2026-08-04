import React from 'react';

const ActionStatsCard = ({ title, value, subtitle, bgColor, textColor, borderColor, trend }) => (
  <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:shadow-md transition group">
    <div className="flex items-center justify-between mb-4">
      <div>
        <p className="text-sm text-gray-500 dark:text-slate-400 mb-1 font-medium">{title}</p>
        <p className="text-3xl font-bold text-gray-900 dark:text-slate-100">{value}</p>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <span className={`text-sm ${bgColor} ${textColor} px-2 py-1 rounded-lg border ${borderColor} font-medium flex items-center gap-1`}>
        {trend && <i className={`fa-solid ${trend} text-[10px]`}></i>}
        {subtitle}
      </span>
    </div>
  </div>
);

export default ActionStatsCard;
