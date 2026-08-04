import React from 'react';


// ─── Compact Watchlist Card ───────────────────────────────────────────────────

const CompactWatchlistCard = ({ title, sku, stock, velocity, image, status }) => (
  <div className="p-3 rounded-xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-all">
    <div className="flex items-center gap-2 mb-2">
      {image ? (
        <img src={image} alt={title} className="w-9 h-9 rounded-lg object-contain bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 flex-shrink-0" />
      ) : (
        <div className="w-9 h-9 rounded-lg bg-gray-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0 border border-dashed border-gray-300 dark:border-slate-700">
          <i className="fa-solid fa-box text-gray-400 text-[10px]" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-1">
          <h4 className="font-semibold text-gray-900 dark:text-slate-100 text-xs leading-tight line-clamp-2">{title}</h4>
          {status && (
            <span className={`px-1.5 py-0.5 text-white text-[8px] rounded font-bold flex-shrink-0 ml-1 ${status === 'LOW' ? 'bg-red-600' : status === 'HOT' ? 'bg-green-600' : 'bg-yellow-600'}`}>
              {status}
            </span>
          )}
        </div>
        <p className="text-[9px] text-gray-500 dark:text-slate-400 mt-0.5 font-sans">SKU: {sku}</p>
      </div>
    </div>
    <div className="grid grid-cols-2 gap-2">
      <div>
        <p className="text-[9px] text-gray-500 dark:text-slate-400">Stock</p>
        <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{stock}</p>
      </div>
      {velocity && (
        <div>
          <p className="text-[9px] text-gray-500 dark:text-slate-400">Velocity</p>
          <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{velocity}</p>
        </div>
      )}
    </div>
  </div>
);

export default CompactWatchlistCard;
