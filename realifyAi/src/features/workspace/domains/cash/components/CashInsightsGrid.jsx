import { motion } from 'framer-motion';
import React from 'react';
import { formatCompactCurrency } from '@/utils/formatters';
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { upcomingDeposits, feesBreakdownData, workingCapitalTrendData } from '@/features/workspace/domains/cash/data/cashData';

export const UpcomingDepositsContent = () => (
  <div className="space-y-3">
    {upcomingDeposits.map((item, idx) => (
      <div key={idx} className="flex items-center justify-between p-4 rounded-xl border transition-all bg-gray-50/50 dark:bg-slate-800/50 border-gray-100 dark:border-slate-700/50">
        <div className="min-w-0 flex-1">
          <p className="text-base font-bold text-gray-900 dark:text-slate-100">{item.amount}</p>
          <p className="text-xs text-gray-500 dark:text-slate-500 font-medium mt-0.5">{item.source}</p>
        </div>
        <div className="text-right ml-4">
          <p className="text-base font-bold text-gray-900 dark:text-slate-100">{item.date}</p>
          <p className="text-[11px] text-gray-400 font-medium mt-0.5">{item.status}</p>
        </div>
      </div>
    ))}
  </div>
);

export const FeesBreakdownContent = () => (
  <>
    <div className="h-[260px] mb-4">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={feesBreakdownData} innerRadius={80} outerRadius={110} paddingAngle={5} dataKey="value">
            {feesBreakdownData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
            formatter={(val) => [`$${val.toLocaleString()}`, 'Amount']}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
    <div className="grid grid-cols-2 gap-2">
      {feesBreakdownData.map((fee, idx) => (
        <div key={idx} className="p-3 bg-gray-50/50 dark:bg-slate-800/50 rounded-xl border border-gray-100/50 dark:border-slate-700/50 text-center">
          <p className="text-xs font-bold text-gray-400 tracking-tighter mb-0.5">{fee.name}</p>
          <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{formatCompactCurrency(fee.value, { decimals: 1 })}</p>
        </div>
      ))}
    </div>
  </>
);

export const WorkingCapitalContent = () => (
  <div className="h-[300px]">
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={workingCapitalTrendData}>
        <defs>
          <linearGradient id="colorWCFull" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 600, fill: '#94a3b8' }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 600, fill: '#94a3b8' }} tickFormatter={(val) => `$${val}k`} />
        <Tooltip
          contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
          formatter={(val) => [`$${val}k`, 'Working Capital']}
        />
        <Area type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} fillOpacity={1} fill="url(#colorWCFull)" />
      </AreaChart>
    </ResponsiveContainer>
  </div>
);

const CashInsightCard = ({ title, icon, iconColor, children, actionLabel = "Details" }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all group"
  >
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100 flex items-center gap-2">
        <i className={`fa-solid ${icon} ${iconColor}`}></i>
        {title}
      </h3>
      <button className="text-xs text-blue-600 dark:text-blue-400 font-semibold hover:underline opacity-0 group-hover:opacity-100 transition-opacity">
        {actionLabel}
      </button>
    </div>
    {children}
  </motion.div>
);

const CashInsightsGrid = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-5">
      {/* Upcoming Deposits */}
      <CashInsightCard title="Upcoming Deposits" icon="fa-calendar-check" iconColor="text-green-600">
        <div className="space-y-3">
          {upcomingDeposits.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 rounded-xl border transition-all bg-gray-50/50 dark:bg-slate-800/50 border-gray-100 dark:border-slate-700/50">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.amount}</p>
                <p className="text-[10px] text-gray-500 dark:text-slate-500 truncate font-bold tracking-tight">{item.source}</p>
              </div>
              <div className="text-right ml-4">
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.date}</p>
                <p className="text-[10px] text-gray-400 font-medium">{item.status}</p>
              </div>
            </div>
          ))}
        </div>
      </CashInsightCard>

      {/* Fees Breakdown (30d) */}
      <CashInsightCard title="Fees Breakdown (30d)" icon="fa-receipt" iconColor="text-purple-500">
        <div className="h-[180px] mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={feesBreakdownData}
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {feesBreakdownData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                formatter={(val) => [`$${val.toLocaleString()}`, 'Amount']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {feesBreakdownData.map((fee, idx) => (
            <div key={idx} className="p-2 bg-gray-50/50 dark:bg-slate-800/50 rounded-xl border border-gray-100/50 dark:border-slate-700/50 text-center">
              <p className="text-[10px] font-bold text-gray-400 tracking-tighter mb-0.5">{fee.name}</p>
              <p className="text-xs font-bold text-gray-900 dark:text-slate-100">{formatCompactCurrency(fee.value, { decimals: 1 })}</p>
            </div>
          ))}
        </div>
      </CashInsightCard>

      {/* Working Capital Trend */}
      <CashInsightCard title="Working Capital Trend" icon="fa-chart-line" iconColor="text-blue-600">
        <div className="h-[200px] -mx-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={workingCapitalTrendData}>
              <defs>
                <linearGradient id="colorWC" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
              <XAxis 
                dataKey="name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} 
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }}
                tickFormatter={(val) => `$${val}k`}
              />
              <Tooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                formatter={(val) => [`$${val}k`, 'Working Capital']}
              />
              <Area type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} fillOpacity={1} fill="url(#colorWC)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CashInsightCard>
    </div>
  );
};

export default CashInsightsGrid;
