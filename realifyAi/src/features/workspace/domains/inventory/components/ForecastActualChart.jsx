import React from 'react';
import { 
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Legend 
} from 'recharts';
import { SEMANTIC_COLORS } from '@/utils/chartColors';

const ForecastActualChart = () => {
  const data = [
    { name: 'Feb 1', actual: 42, forecast: 40 },
    { name: 'Feb 5', actual: 38, forecast: 42 },
    { name: 'Feb 10', actual: 45, forecast: 41 },
    { name: 'Feb 15', actual: 48, forecast: 43 },
    { name: 'Feb 20', actual: 52, forecast: 46 },
    { name: 'Feb 25', actual: 41, forecast: 48 },
    { name: 'Mar 1', actual: 49, forecast: 50 },
  ];

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm h-full">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Forecast vs Actual</h3>
          <p className="text-sm text-gray-500 dark:text-slate-400">Demand prediction accuracy · last 30 days</p>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1 bg-brand text-white rounded-lg text-xs font-medium dark:bg-gray-600">Top 10</button>
          <button className="px-3 py-1 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-lg text-xs font-medium hover:bg-gray-200">All</button>
        </div>
      </div>
      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} strokeOpacity={0.1} />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }}
              itemStyle={{ fontSize: '12px' }}
            />
            <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ fontSize: '10px', paddingBottom: '20px' }} />
            <Bar dataKey="actual" name="Actual Sold" fill={SEMANTIC_COLORS.actual} radius={[4, 4, 0, 0]} barSize={20} />
            <Line type="monotone" dataKey="forecast" name="Forecast" stroke={SEMANTIC_COLORS.forecast} strokeWidth={2} dot={{ r: 3 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ForecastActualChart;
