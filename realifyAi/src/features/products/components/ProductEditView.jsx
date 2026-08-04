import React, { useState } from 'react';
import MarketplaceSyncBanner from '@/components/feedback/MarketplaceSyncBanner';
import { CATEGORIES, STATUS_OPTIONS, STATUS_STYLES } from '@/features/products/data/productsData';

const ProductEditView = ({ items, onBack, onGoToMarketplace }) => {
  const [rows, setRows] = useState(items.map(p => ({ ...p })));
  const update = (id, field, value) =>
    setRows(prev => prev.map(r => r.id === id ? { ...r, [field]: value } : r));

  return (
    <div className="flex flex-col gap-4">
      {/* Edit Banner */}
      <MarketplaceSyncBanner onGoToMarketplace={onGoToMarketplace} />

      <div className="flex items-center justify-between gap-3 py-1">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="flex items-center gap-1.5 text-sm font-medium text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 transition-colors">
            <i className="fa-solid fa-arrow-left text-[11px]" />
          </button>
          <span className="text-gray-300 dark:text-slate-700 select-none">|</span>
          <h3 className="text-base font-bold text-gray-900 dark:text-slate-100">
            Editing {rows.length} product{rows.length !== 1 ? 's' : ''}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-600 dark:text-slate-300 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800 transition">
            <i className="fa-solid fa-table-columns text-[10px]" /> Columns
          </button>
          <button onClick={onBack} className="px-4 py-2 rounded-xl bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition">
            Save
          </button>
        </div>
      </div>
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 dark:border-slate-800 bg-gray-50/70 dark:bg-slate-800/50">
                <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left min-w-[220px]">Product title</th>
                <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left min-w-[140px]">Status</th>
                <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left min-w-[150px]">Category</th>
                <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left min-w-[150px]">Vendor</th>
                <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-right min-w-[110px]">Base price</th>
                <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-right min-w-[130px]">Available qty</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-slate-800/60">
              {rows.map(row => {
                const ss = STATUS_STYLES[row.status] || STATUS_STYLES.Active;
                return (
                  <tr key={row.id} className="hover:bg-gray-50/60 dark:hover:bg-slate-800/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <i className="fa-solid fa-chevron-up text-gray-300 dark:text-slate-600 text-[10px] flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-gray-900 dark:text-slate-100 leading-tight truncate">{row.name}</p>
                          <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">Default</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className={`inline-flex items-center gap-1.5 pl-2 pr-1 py-1 rounded-full ${ss.pill}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${ss.dot} flex-shrink-0`} />
                        <select value={row.status} onChange={e => update(row.id, 'status', e.target.value)} className="text-xs font-semibold bg-transparent border-none outline-none cursor-pointer appearance-none pr-1" style={{ color: 'inherit' }}>
                          {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                        <i className="fa-solid fa-chevron-down text-[8px] opacity-60 flex-shrink-0" />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="inline-flex items-center gap-1 px-2.5 py-1 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800/40 rounded-md">
                        <select value={row.category} onChange={e => update(row.id, 'category', e.target.value)} className="text-xs font-medium text-purple-700 dark:text-purple-400 bg-transparent border-none outline-none cursor-pointer appearance-none">
                          {CATEGORIES.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <i className="fa-solid fa-chevron-down text-purple-400 text-[8px] flex-shrink-0" />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <input type="text" value={row.vendor} onChange={e => update(row.id, 'vendor', e.target.value)} className="w-full text-xs text-gray-700 dark:text-slate-300 bg-transparent border-b border-transparent hover:border-gray-300 dark:hover:border-slate-600 focus:border-gray-500 dark:focus:border-slate-400 outline-none py-0.5 transition-colors" />
                    </td>
                    <td className="px-4 py-3">
                      <input type="text" value={row.price} onChange={e => update(row.id, 'price', e.target.value)} className="w-full text-xs text-gray-700 dark:text-slate-300 bg-transparent border-b border-transparent hover:border-gray-300 dark:hover:border-slate-600 focus:border-gray-500 dark:focus:border-slate-400 outline-none py-0.5 transition-colors text-right" />
                    </td>
                    <td className="px-4 py-3">
                      <input type="number" value={row.inventory} onChange={e => update(row.id, 'inventory', parseInt(e.target.value) || 0)} className="w-full text-xs text-gray-700 dark:text-slate-300 bg-transparent border-b border-transparent hover:border-gray-300 dark:hover:border-slate-600 focus:border-gray-500 dark:focus:border-slate-400 outline-none py-0.5 transition-colors text-right" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ─── Products List Page ───────────────────────────────────────────────────────

export default ProductEditView;
