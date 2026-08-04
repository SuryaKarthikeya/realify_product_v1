import React from 'react';

const ExplanationPanel = ({ data }) => {
  if (!data) return null;

  return (
    <div className="bg-[#fcfbf9] dark:bg-slate-900 border border-[#e5e0d8] dark:border-slate-800 rounded-2xl p-6 mt-4 shadow-sm animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-[10px] font-bold text-[#627a8e] dark:text-blue-400 font-sans tracking-widest uppercase">
          {data.provenanceBadge || 'L1'}
        </span>
        <span className="text-[10px] text-[#627a8e] dark:text-blue-400 font-sans tracking-widest uppercase">
          · {data.title || 'DETERMINISTIC — HOW THIS NUMBER IS DERIVED'}
        </span>
      </div>

      <div className="grid grid-cols-[140px_1fr] gap-y-3 text-[13px]">
        {/* Formula */}
        <div className="text-gray-400 dark:text-slate-500 font-sans">Formula</div>
        <div>
          <span className="bg-[#efeadf] dark:bg-slate-800 text-gray-800 dark:text-slate-200 px-2 py-1 rounded font-sans text-[11px]">
            {data.formula}
          </span>
        </div>

        {/* Top contributors */}
        <div className="text-gray-400 dark:text-slate-500 font-sans mt-2">Top contributors</div>
        <div className="mt-2 space-y-2">
          {data.contributors.map((c, i) => (
            <div key={i} className="flex items-center gap-6 font-sans">
              <span className="text-gray-400 dark:text-slate-500 w-24">{c.sku}</span>
              <span className="font-bold text-gray-900 dark:text-slate-100">{c.value}</span>
            </div>
          ))}
        </div>

        {/* Result */}
        <div className="text-gray-400 dark:text-slate-500 font-sans mt-2 pt-2 border-t border-transparent">Result</div>
        <div className="font-bold text-gray-900 dark:text-slate-100 mt-2 pt-2 border-t border-transparent font-sans">
          {data.result}
        </div>

        {/* Timeframe */}
        <div className="text-gray-400 dark:text-slate-500 font-sans">Timeframe</div>
        <div className="text-gray-700 dark:text-slate-300 font-sans">
          {data.timeframe}
        </div>

        {/* Provenance */}
        <div className="text-gray-400 dark:text-slate-500 font-sans">Provenance</div>
        <div className="flex items-center gap-2 font-sans">
          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 dark:bg-emerald-900/30 px-1.5 py-0.5 rounded">
            {data.provenanceBadge || 'L1'}
          </span>
          <span className="text-gray-700 dark:text-slate-300">{data.provenanceText}</span>
        </div>
      </div>
    </div>
  );
};

export default ExplanationPanel;
