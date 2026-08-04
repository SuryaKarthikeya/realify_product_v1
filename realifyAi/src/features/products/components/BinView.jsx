import React, { useState } from 'react';
import { STATUS_STYLES } from '@/features/products/data/productsData';

// ─── Bin View ─────────────────────────────────────────────────────────────────
const BinView = ({ items, onBack, onRestore, onRestoreMany }) => {
  const [selectedIds, setSelectedIds] = useState(new Set());

  const toggleSelect = (id) => setSelectedIds(prev => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });

  const toggleAll = () => {
    if (selectedIds.size === items.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(items.map(p => p.id)));
  };

  const handleBulkRestore = () => {
    onRestoreMany([...selectedIds]);
    setSelectedIds(new Set());
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3 py-1">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm font-medium text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 transition-colors"
        >
          <i className="fa-solid fa-arrow-left text-[11px]" />
        </button>
        <span className="text-gray-300 dark:text-slate-700 select-none">|</span>
        <h3 className="text-base font-bold text-gray-900 dark:text-slate-100">
          Deleted Products{' '}
          <span className="text-gray-400 dark:text-slate-500 font-normal text-sm">({items.length})</span>
        </h3>
        {selectedIds.size > 1 && (
          <button
            onClick={handleBulkRestore}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/40 text-green-700 dark:text-green-400 text-xs font-bold hover:bg-green-100 dark:hover:bg-green-900/40 transition-all"
          >
            <i className="fa-solid fa-rotate-left text-[10px]" />
            Restore ({selectedIds.size})
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm flex flex-col items-center justify-center py-10 gap-3">
          <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center">
            <span className="fa-stack" style={{ fontSize: '0.75rem', lineHeight: '1' }}>
              <i className="fa-solid fa-trash-can fa-stack-2x text-gray-400 dark:text-slate-500" />
              <i className="fa-solid fa-recycle fa-stack-1x fa-inverse" style={{ fontSize: '0.55em' }} />
            </span>
          </div>
          <p className="text-sm text-gray-400 dark:text-slate-500">Recycle Bin is empty</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] lg:min-w-0">
              <thead>
                <tr className="border-b border-gray-100 dark:border-slate-800">
                  <th className="px-4 py-3 w-8">
                    <input type="checkbox" checked={items.length > 0 && selectedIds.size === items.length} onChange={toggleAll} className="rounded border-gray-300 dark:border-slate-600" />
                  </th>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left w-10">#</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left w-12">Image</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Product</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Status</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Price</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Category</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Inventory</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Velocity</th>
                  <th className="px-3 py-3 w-20"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-slate-800/60">
                {items.map((product, idx) => {
                  const ss = STATUS_STYLES[product.status] || STATUS_STYLES.Active;
                  return (
                    <tr key={product.id} className="hover:bg-gray-50/80 dark:hover:bg-slate-800/30 transition-colors opacity-70">
                      <td className="px-4 py-3 w-8">
                        <input type="checkbox" checked={selectedIds.has(product.id)} onChange={() => toggleSelect(product.id)} className="rounded border-gray-300 dark:border-slate-600" />
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400 dark:text-slate-500 font-sans w-10">{idx + 1}</td>
                      <td className="px-3 py-3">
                        <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 flex items-center justify-center overflow-hidden">
                          {product.image
                            ? <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
                            : <i className="fa-solid fa-box text-gray-300 dark:text-slate-600 text-[11px]" />}
                        </div>
                      </td>
                      <td className="px-3 py-3 min-w-[160px]">
                        <p className="text-sm font-semibold text-gray-900 dark:text-slate-100 leading-tight">{product.name}</p>
                        <p className="text-[10px] text-gray-400 dark:text-slate-500 font-sans mt-0.5">{product.sku}</p>
                      </td>
                      <td className="px-3 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${ss.pill}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${ss.dot} flex-shrink-0`} />
                          {product.status}
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <span className="text-xs font-semibold text-gray-700 dark:text-slate-300">{product.price}</span>
                      </td>
                      <td className="px-3 py-3">
                        <span className="text-xs text-gray-600 dark:text-slate-400">{product.category}</span>
                      </td>
                      <td className="px-3 py-3">
                        <span className={`text-xs font-semibold ${product.inventory === 0 ? 'text-red-600 dark:text-red-400' : product.inventory < 20 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-slate-300'}`}>
                          {product.inventory === 0 ? 'Out of stock' : `${product.inventory.toLocaleString()} in stock`}
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <span className="text-xs text-gray-600 dark:text-slate-400">{product.velocity}</span>
                      </td>
                      <td className="px-3 py-3 text-right">
                        <button
                          onClick={() => onRestore(product.id)}
                          title="Restore"
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-green-200 dark:border-green-800/40 text-green-700 dark:text-green-400 text-[11px] font-semibold hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                        >
                          <i className="fa-solid fa-rotate-left text-[9px]" /> Restore
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Product Edit View ────────────────────────────────────────────────────────

export default BinView;
