import React from 'react';
import { categoryBreakdown, inflowCategoryChartData } from '@/features/workspace/domains/cash/data/cashData';
import BasePieChart from '@/components/data-display/charts/BasePieChart';

const TransactionAnalysisSection = () => {
  return (
    <section id="transaction-analysis" className="mb-5 mt-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Transaction Category Analysis</h3>
          <p className="text-sm text-gray-600 dark:text-slate-400">Detailed breakdown of cash movements by category</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <h4 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Category Breakdown</h4>
          <div className="space-y-4">
            {categoryBreakdown.map((item, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h5 className="font-bold text-gray-900 dark:text-slate-100">{item.title}</h5>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{item.subtext}</p>
                  </div>
                  <span className="px-3 py-1 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 rounded-lg text-xs font-bold">{item.status}</span>
                </div>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Amount</p>
                    <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.amount}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{item.countLabel || 'Count'}</p>
                    <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{item.avgLabel || 'Avg'}</p>
                    <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.avg}</p>
                  </div>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-gray-400 dark:bg-slate-500 rounded-full" style={{ width: `${item.progress}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm h-full flex flex-col">
          <h4 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Inflow by Category</h4>
          <BasePieChart 
            data={inflowCategoryChartData}
            height={350}
            innerRadius={80}
            outerRadius={110}
            tooltipFormatter={(val) => [`$${val}K`, 'Inflow']}
          />
        </div>
      </div>
    </section>
  );
};

export default TransactionAnalysisSection;
