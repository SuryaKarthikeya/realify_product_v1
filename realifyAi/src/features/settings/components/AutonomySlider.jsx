import React from 'react';

const levels = [
  { id: 0, label: 'Observe', color: 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700' },
  { id: 1, label: 'Suggest', color: 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800' },
  { id: 2, label: 'Assist', color: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800' },
  { id: 3, label: 'Act', color: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800' },
];

const AutonomySlider = ({ title, sub, value, onChange }) => {
  const currentLevel = levels[value] || levels[0];

  return (
    <div className="p-5 border border-gray-100 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 shadow-sm transition-all hover:shadow-md">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{title}</p>
          <p className="text-xs text-gray-500 dark:text-slate-500">{sub}</p>
        </div>
        <span className={`px-3 py-1 rounded-lg text-[10px] font-bold border transition-colors ${currentLevel.color}`}>
          {currentLevel.label}
        </span>
      </div>
      
      <div className="px-1">
        <input 
          type="range" 
          min="0" 
          max="3" 
          step="1" 
          value={value} 
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="w-full h-1.5 bg-gray-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between mt-2">
          {levels.map((l) => (
            <span key={l.id} className="text-[10px] font-bold text-gray-400 dark:text-slate-600">
              {l.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AutonomySlider;
