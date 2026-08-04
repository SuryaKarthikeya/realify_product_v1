import React, { useState } from 'react';
import BaseLineChart from '@/components/data-display/charts/BaseLineChart';
import { adSpendTrends } from '@/features/workspace/domains/ads/data/adsData';
import { CHART_CATEGORICAL } from '@/utils/chartColors';

const weeklyData = [
  { day: 'W1', google: 92000, facebook: 74000, amazon: 52000 },
  { day: 'W2', google: 104000, facebook: 81000, amazon: 57000 },
  { day: 'W3', google: 98000, facebook: 76000, amazon: 54000 },
  { day: 'W4', google: 118000, facebook: 89000, amazon: 63000 },
];

const monthlyData = [
  { day: 'Jan', google: 380000, facebook: 290000, amazon: 210000 },
  { day: 'Feb', google: 420000, facebook: 310000, amazon: 230000 },
  { day: 'Mar', google: 395000, facebook: 295000, amazon: 215000 },
  { day: 'Apr', google: 450000, facebook: 340000, amazon: 248000 },
  { day: 'May', google: 118200, facebook: 91500, amazon: 66000 },
];

const AdSpendTrendChart = () => {
  const [period, setPeriod] = useState('daily');

  const dataMap = { daily: adSpendTrends, weekly: weeklyData, monthly: monthlyData };
  const currentData = dataMap[period];

  const lines = [
    { key: 'google', name: 'Google Ads', color: CHART_CATEGORICAL[0] },
    { key: 'facebook', name: 'Facebook Ads', color: CHART_CATEGORICAL[1] },
    { key: 'amazon', name: 'Amazon Ads', color: CHART_CATEGORICAL[2] }
  ];

  return (
    <div className="h-full w-full flex flex-col">
      <div className="flex items-center justify-end gap-1 mb-3 flex-shrink-0">
        {['Daily', 'Weekly', 'Monthly'].map(label => {
          const key = label.toLowerCase();
          return (
            <button
              key={key}
              onClick={() => setPeriod(key)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                period === key
                  ? 'bg-brand text-white dark:bg-gray-600'
                  : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400 hover:bg-gray-200 dark:hover:bg-slate-700'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>
      <div className="flex-1">
        <BaseLineChart
          data={currentData}
          lines={lines}
          xAxisKey="day"
          height="100%"
          yAxisFormatter={(val) => `$${val / 1000}k`}
          tooltipFormatter={(val) => [`$${val.toLocaleString()}`, '']}
        />
      </div>
    </div>
  );
};

export default AdSpendTrendChart;
