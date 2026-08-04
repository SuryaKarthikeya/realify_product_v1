import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { stockStatusData } from '@/features/workspace/domains/inventory/data/inventoryData';
import { SEMANTIC_COLORS } from '@/utils/chartColors';

const StockStatusChart = ({ darkMode: _darkMode }) => {
  const total = stockStatusData.reduce((acc, curr) => acc + curr.value, 0);

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Stock Status</h3>
      
      <div className="flex items-center justify-center mb-6 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={stockStatusData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {stockStatusData.map((entry, index) => {
                let color = SEMANTIC_COLORS.neutral;
                if (entry.name === 'In Stock') color = SEMANTIC_COLORS.positive;
                if (entry.name === 'Low Stock') color = SEMANTIC_COLORS.warning;
                if (entry.name === 'Out of Stock') color = SEMANTIC_COLORS.negative;
                return <Cell key={`cell-${index}`} fill={color} />;
              })}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--tooltip-bg)',
                border: '1px solid var(--tooltip-border)',
                borderRadius: '12px',
                color: 'var(--tooltip-text)'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute flex flex-col items-center justify-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{total.toLocaleString()}</p>
          <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">Total SKUs</p>
        </div>
      </div>

      <div className="space-y-3">
        {stockStatusData.map((item, idx) => {
          const percentage = ((item.value / total) * 100).toFixed(0);
          const statusColors = {
            'In Stock': {
              bg: 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-200 dark:border-emerald-900/30',
              dot: SEMANTIC_COLORS.positive
            },
            'Low Stock': {
              bg: 'bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-900/30',
              dot: SEMANTIC_COLORS.warning
            },
            'Out of Stock': {
              bg: 'bg-rose-50 dark:bg-rose-900/10 border-rose-200 dark:border-rose-900/30',
              dot: SEMANTIC_COLORS.negative
            }
          };

          const config = statusColors[item.name] || { bg: 'bg-gray-50', dot: SEMANTIC_COLORS.neutral };

          return (
            <div key={idx} className="flex items-center justify-between p-3 rounded-xl border bg-white dark:bg-slate-900 border-gray-100 dark:border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: config.dot }}></div>
                <span className="text-sm font-medium text-gray-700 dark:text-slate-300">{item.name}</span>
              </div>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-100">
                {item.value.toLocaleString()} ({percentage}%)
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-6 p-4 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-600 dark:text-slate-400 font-medium">Stock Fill Rate</span>
          <span className="text-xs bg-gray-700 dark:bg-slate-600 text-white px-2 py-1 rounded-lg font-medium shadow-sm">
            <i className="fa-solid fa-arrow-up mr-1 text-[8px]"></i>+2.4%
          </span>
        </div>
        <p className="text-sm font-bold text-gray-900 dark:text-slate-100">95% Fill Rate</p>
      </div>
    </div>
  );
};

export default StockStatusChart;
