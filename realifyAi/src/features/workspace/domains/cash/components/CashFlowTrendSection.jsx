import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { cashFlowTrendData } from '@/features/workspace/domains/cash/data/cashData';
import { SEMANTIC_COLORS } from '@/utils/chartColors';

const CashFlowTrendSection = () => {
  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm h-full flex flex-col">
      <div className="flex flex-row flex-wrap items-center justify-between mb-6 gap-3 flex-shrink-0">
        <div className="min-w-0">
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-1 whitespace-nowrap">Cash Flow Trends</h3>
          <p className="text-sm text-gray-600 dark:text-slate-400 whitespace-nowrap">7-day inflow and outflow analysis</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button className="px-3 py-1.5 bg-brand text-white rounded-lg text-sm font-medium shadow-sm dark:bg-gray-600">Daily</button>
          <button className="px-3 py-1.5 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg text-sm font-medium transition">Weekly</button>
          <button className="px-3 py-1.5 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg text-sm font-medium transition">Monthly</button>
        </div>
      </div>
      <div className="flex-1 min-h-0 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={cashFlowTrendData}
            margin={{ top: 10, right: 10, left: 10, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
            <XAxis 
              dataKey="day" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#64748b', fontSize: 12 }}
              dy={10}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#64748b', fontSize: 12 }}
              tickFormatter={(value) => `$${value}k`}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#fff', 
                borderRadius: '12px', 
                border: '1px solid #e2e8f0',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
              }}
              formatter={(value) => [`$${value}k`, '']}
            />
            <Legend 
              verticalAlign="top" 
              align="right" 
              iconType="circle"
              wrapperStyle={{ paddingBottom: '20px' }}
            />
            <Line 
              type="monotone" 
              dataKey="inflow" 
              name="Inflow" 
              stroke={SEMANTIC_COLORS.positive} 
              strokeWidth={3} 
              dot={{ r: 4, fill: '#fff', strokeWidth: 2, stroke: SEMANTIC_COLORS.positive }}
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
            <Line 
              type="monotone" 
              dataKey="outflow" 
              name="Outflow" 
              stroke={SEMANTIC_COLORS.negative} 
              strokeWidth={3} 
              dot={{ r: 4, fill: '#fff', strokeWidth: 2, stroke: SEMANTIC_COLORS.negative }}
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default CashFlowTrendSection;
