import React, { lazy, Suspense } from 'react';
import SectionHeading from '@/components/data-display/SectionHeading';
import { TableCard, TD, TR, TableHead } from '@/components/data-display/DenseTable';
import { campaignStatusColor } from '@/utils/filterUtils';
import { campaignData, platformData } from '@/features/workspace/domains/ads/data/adsDashboardData';
import PlatformPerformanceSection from '@/features/workspace/domains/ads/components/PlatformPerformanceSection';

const PlatformDistributionChart = lazy(() => import('@/features/workspace/domains/ads/components/PlatformDistributionChart'));

const AdsTables = () => (
  <div className="space-y-5">
    <div>
      <SectionHeading title="Campaign Performance — ROAS, ACoS, CTR" />
      <TableCard scrollable>
        <table className="w-full">
          <TableHead cols={['Campaign', 'Type', 'Spend', 'Revenue', 'ROAS', 'ACoS', 'Conv %', 'Status']} />
          <tbody>
            {campaignData.map((r, i) => (
              <TR key={i}>
                <TD className="font-semibold text-gray-900 dark:text-slate-100 max-w-[200px] truncate">{r.campaign}</TD>
                <TD><span className="px-1.5 py-0.5 bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400 rounded text-[9px] font-sans">{r.type}</span></TD>
                <TD className="text-gray-700 dark:text-slate-300">{r.spend}</TD>
                <TD className="font-semibold text-gray-900 dark:text-slate-100">{r.revenue}</TD>
                <TD className={parseFloat(r.roas) >= 8 ? 'font-bold text-green-600 dark:text-green-400' : parseFloat(r.roas) >= 4 ? 'font-bold text-amber-600 dark:text-amber-400' : 'font-bold text-red-500 dark:text-red-400'}>{r.roas}</TD>
                <TD className={parseFloat(r.acos) <= 15 ? 'text-green-600 dark:text-green-400' : parseFloat(r.acos) <= 25 ? 'text-amber-600 dark:text-amber-400' : 'text-red-500 dark:text-red-400'}>{r.acos}</TD>
                <TD className="text-gray-600 dark:text-slate-400">{r.convRate}</TD>
                <TD><span className={`px-1.5 py-0.5 rounded-md text-[9px] font-bold uppercase ${campaignStatusColor(r.status)}`}>{r.status}</span></TD>
              </TR>
            ))}
          </tbody>
        </table>
      </TableCard>
    </div>
    {/* ── Platform Distribution + Platform Performance Summary 50-50 ── */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
      <Suspense fallback={<div className="h-40 rounded-2xl bg-gray-100 dark:bg-slate-800 animate-pulse" />}>
        <div>
          <SectionHeading title="Platform Distribution" />
          <PlatformDistributionChart />
        </div>
      </Suspense>
      <div>
        <SectionHeading title="Platform Performance Summary" />
        <TableCard>
          <table className="w-full">
            <TableHead cols={['Platform', 'Total Spend', 'Revenue', 'ROAS', 'ACoS', 'Campaigns', 'Active SKUs']} />
            <tbody>
              {platformData.map((r, i) => (
                <TR key={i}>
                  <TD className="font-semibold text-gray-900 dark:text-slate-100">{r.platform}</TD>
                  <TD className="text-gray-700 dark:text-slate-300">{r.spend}</TD>
                  <TD className="font-semibold text-gray-900 dark:text-slate-100">{r.revenue}</TD>
                  <TD className="font-bold text-green-600 dark:text-green-400">{r.roas}</TD>
                  <TD className={parseFloat(r.acos) <= 12 ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'}>{r.acos}</TD>
                  <TD className="text-gray-600 dark:text-slate-400">{r.campaigns}</TD>
                  <TD className="text-gray-600 dark:text-slate-400">{r.skus}</TD>
                </TR>
              ))}
            </tbody>
          </table>
        </TableCard>
      </div>
    </div>
    <div>
      <SectionHeading title="Channel Distribution" />
      <PlatformPerformanceSection />
    </div>
  </div>
);

export default AdsTables;
