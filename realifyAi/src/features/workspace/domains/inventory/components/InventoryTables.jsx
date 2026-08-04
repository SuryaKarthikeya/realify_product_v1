import React from 'react';
import SectionHeading from '@/components/data-display/SectionHeading';
import { poDrafts, overstockItems } from '@/features/workspace/domains/inventory/data/inventoryDashboardData';
import ReorderRecommendationsTable from '@/features/workspace/domains/inventory/components/ReorderRecommendationsTable';
import WarehouseSection from '@/features/workspace/domains/inventory/components/WarehouseSection';

const InventoryTables = () => (
  <div className="space-y-6">
    <div>
      <ReorderRecommendationsTable />
    </div>

    <div>
      <WarehouseSection />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
      <div>
        <SectionHeading title="Recommended PO Drafts" />
        <div className="space-y-3">
          {poDrafts.map((po, idx) => (
            <div key={idx} className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{po.title}</p>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300">{po.status}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div><p className="text-gray-400">Vendor</p><p className="font-semibold text-gray-800 dark:text-slate-200">{po.vendor}</p></div>
                <div><p className="text-gray-400">Qty</p><p className="font-semibold text-gray-800 dark:text-slate-200">{po.qty}</p></div>
                <div><p className="text-gray-400">Value</p><p className="font-semibold text-gray-800 dark:text-slate-200">{po.value}</p></div>
              </div>
              <p className="text-[10px] text-gray-400 mt-1">Lead time: {po.lt}</p>
            </div>
          ))}
        </div>
      </div>
      <div>
        <SectionHeading title="Overstock (DOC>180d)" />
        <div className="space-y-3">
          {overstockItems.map((item, idx) => (
            <div key={idx} className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.title}</p>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300">{item.action}</span>
              </div>
              <p className="text-xs text-gray-500 dark:text-slate-500 mb-2">{item.sub}</p>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div><p className="text-gray-400">DOC</p><p className="font-bold text-gray-800 dark:text-slate-200">{item.doc}</p></div>
                <div><p className="text-gray-400">Units</p><p className="font-semibold text-gray-800 dark:text-slate-200">{item.units}</p></div>
                <div><p className="text-gray-400">Tied Capital</p><p className="font-bold text-gray-800 dark:text-slate-200">{item.value}</p></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

export default InventoryTables;
