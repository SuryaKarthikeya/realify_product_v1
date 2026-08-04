import React, { lazy, Suspense } from 'react';
import SectionHeading from '@/components/data-display/SectionHeading';
import TransactionAnalysisSection from '@/features/workspace/domains/cash/components/TransactionAnalysisSection';
import { UpcomingDepositsContent } from '@/features/workspace/domains/cash/components/CashInsightsGrid';

const CashDistributionSection = lazy(() => import('@/features/workspace/domains/cash/components/CashDistributionSection'));

const CashPageTables = () => (
  <div className="space-y-6">
    {/* ── Cash Distribution + Upcoming Deposits 50-50 ── */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
      <Suspense fallback={<div className="h-40 rounded-2xl bg-gray-100 dark:bg-slate-800 animate-pulse" />}>
        <div>
          <SectionHeading title="Cash Distribution" />
          <CashDistributionSection />
        </div>
      </Suspense>
      <div>
        <SectionHeading title="Upcoming Deposits" />
        <UpcomingDepositsContent />
      </div>
    </div>
    <div>
      <SectionHeading title="Transaction Categories" />
      <TransactionAnalysisSection />
    </div>
  </div>
);

export default CashPageTables;
