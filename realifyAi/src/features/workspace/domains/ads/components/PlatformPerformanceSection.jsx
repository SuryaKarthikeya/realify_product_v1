import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { platformMetrics } from '@/features/workspace/domains/ads/data/adsData';

const PlatformPerformanceSection = () => {
  const chartData = platformMetrics.map(m => ({
    name: m.name,
    roas: parseFloat(m.roas)
  }));

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <div className="xl:col-span-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <h4 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">ROAS by Platform</h4>
        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
              <XAxis 
                dataKey="name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#64748b', fontSize: 12 }}
                dy={10}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#64748b', fontSize: 12 }}
                tickFormatter={(value) => `${value}x`}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  borderRadius: '12px', 
                  border: '1px solid #e2e8f0' 
                }}
                formatter={(value) => [`${value}x`, 'ROAS']}
              />
              <Bar dataKey="roas" radius={[8, 8, 0, 0]} barSize={50}>
                {chartData.map((entry, index) => {
                  const colors = {
                    'Google Ads': '#6366f1',
                    'Facebook Ads': '#3b82f6',
                    'Amazon Ads': '#38bdf8'
                  };
                  return <Cell key={`cell-${index}`} fill={colors[entry.name] || '#6366f1'} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <h4 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Platform Metrics</h4>
        <div className="space-y-4">
          {platformMetrics.map((platform, idx) => (
            <div key={idx} className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-800 transition-all hover:shadow-md">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h5 className="font-bold text-gray-900 dark:text-slate-100">{platform.name}</h5>
                  <p className="text-xs text-gray-600 dark:text-slate-400">{platform.type}</p>
                </div>
                <span className="px-3 py-1 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 rounded-lg text-[10px] font-bold tracking-wider">{platform.status}</span>
              </div>
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-gray-100 dark:border-slate-700">
                  <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold mb-1">ROAS</p>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{platform.roas}</p>
                </div>
                <div className="p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-gray-100 dark:border-slate-700">
                  <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold mb-1">CTR</p>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{platform.ctr}</p>
                </div>
                <div className="p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-gray-100 dark:border-slate-700">
                  <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold mb-1">CVR</p>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{platform.cvr}</p>
                </div>
              </div>
              <div className="w-full h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-gray-400 dark:bg-slate-500 rounded-full transition-all duration-1000 ease-out" style={{ width: `${platform.progress}%` }}></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PlatformPerformanceSection;
