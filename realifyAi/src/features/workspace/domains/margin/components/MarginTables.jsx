import React, { lazy, Suspense } from 'react';
import {
  unprofitableSKUs, adSpendImpact, cogsCompressions, returnsImpact,
} from '@/features/workspace/domains/margin/data/marginData';

const MarginTrendChart = lazy(() => import('@/features/workspace/domains/margin/components/MarginTrendChart'));
const FeeForensics = lazy(() => import('@/features/workspace/domains/margin/components/FeeForensics'));
const MarginDistributionChart = lazy(() => import('@/features/workspace/domains/margin/components/MarginDistributionChart'));

const ChartFallback = () => <div className="h-40 rounded-2xl bg-gray-100 dark:bg-slate-800 animate-pulse" />;

const ListCard = ({ title, items, renderRow }) => (
  <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4">
    <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wide mb-3">{title}</p>
    <div className="space-y-2">
      {items.map((item, i) => renderRow(item, i))}
    </div>
  </div>
);

const MarginDashboardGrid = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
    <Suspense fallback={<ChartFallback />}>
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4">
        <MarginTrendChart />
      </div>
    </Suspense>
    <Suspense fallback={<ChartFallback />}>
      <FeeForensics />
    </Suspense>

    <ListCard
      title="Unprofitable SKUs"
      items={unprofitableSKUs}
      renderRow={(sku, i) => (
        <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-800">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{sku.name}</p>
            <p className="text-xs text-gray-500 dark:text-slate-500">{sku.sku} · {sku.channel}</p>
          </div>
          <div className="text-right ml-4 flex-shrink-0">
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{sku.loss}</p>
            <p className="text-xs text-gray-400">{sku.sub}</p>
          </div>
        </div>
      )}
    />

    <ListCard
      title="Ad Spend Impact on Margin"
      items={adSpendImpact}
      renderRow={(item, i) => (
        <div key={i} className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-800">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.name}</p>
            <p className="text-xs text-gray-500 dark:text-slate-500 font-bold">Ad spend: {item.spend}</p>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{item.impact}</p>
          </div>
          <div className="text-right ml-4 flex-shrink-0">
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.erosion}</p>
            <p className="text-xs text-gray-400">erosion</p>
          </div>
        </div>
      )}
    />

    <ListCard
      title="COGS Compressions"
      items={cogsCompressions}
      renderRow={(item, i) => (
        <div key={i} className="flex items-center justify-between p-3 bg-amber-50/50 dark:bg-amber-900/10 rounded-xl border border-amber-100/50 dark:border-amber-900/20">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.name}</p>
            <p className="text-xs text-gray-500 dark:text-slate-500">{item.trend}</p>
          </div>
          <div className="text-right ml-4 flex-shrink-0">
            <p className="text-sm font-bold text-red-500">{item.increase}</p>
            <p className="text-xs text-gray-400">{item.impact}</p>
          </div>
        </div>
      )}
    />

    <ListCard
      title="Returns Impact"
      items={returnsImpact}
      renderRow={(item, i) => (
        <div key={i} className="flex items-center justify-between p-3 bg-slate-50/50 dark:bg-slate-800/50 rounded-xl border border-slate-100/50 dark:border-slate-700/50">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.name}</p>
            <p className="text-xs text-gray-500 dark:text-slate-500">{item.meta}</p>
          </div>
          <div className="text-right ml-4 flex-shrink-0">
            <p className="text-sm font-bold text-red-600">{item.loss}</p>
            <p className="text-xs text-gray-400">{item.sub}</p>
          </div>
        </div>
      )}
    />

    <Suspense fallback={<ChartFallback />}>
      <MarginDistributionChart />
    </Suspense>
  </div>
);

export default MarginDashboardGrid;
