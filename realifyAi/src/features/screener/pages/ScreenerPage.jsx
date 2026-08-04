import React, { lazy, Suspense } from 'react';
import { useLocation } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';

const MarketShareTab         = lazy(() => import('@/features/screener/pages/tabs/MarketShareTab'));
const PriceBuyBoxTab         = lazy(() => import('@/features/screener/pages/tabs/PriceBuyBoxTab'));
const AssortmentGapsTab      = lazy(() => import('@/features/screener/pages/tabs/AssortmentGapsTab'));
const BSRDemandTab           = lazy(() => import('@/features/screener/pages/tabs/BSRDemandTab'));
const OpportunityResearchTab = lazy(() => import('@/features/screener/pages/tabs/OpportunityResearchTab'));

const screenerTabs = [
  { path: '/research', label: 'Market Share', icon: 'fa-chart-pie' },
  { path: '/research/price-buybox', label: 'Price & Buy Box', icon: 'fa-tags' },
  { path: '/research/assortment-gaps', label: 'Assortment Gaps', icon: 'fa-layer-group' },
  { path: '/research/bsr-demand', label: 'BSR & Demand', icon: 'fa-fire' },
  { path: '/research/opportunity-research', label: 'Opportunity Research', icon: 'fa-magnifying-glass-chart' },
];

const ScreenerPage = () => {
  const { pathname } = useLocation();

  const renderTab = () => {
    switch (pathname) {
      case '/research/price-buybox':
        return <PriceBuyBoxTab />;
      case '/research/assortment-gaps':
        return <AssortmentGapsTab />;
      case '/research/bsr-demand':
        return <BSRDemandTab />;
      case '/research/opportunity-research':
        return <OpportunityResearchTab />;
      default:
        return <MarketShareTab />;
    }
  };

  return (
    <DashboardLayout
      title="Research"
      subtitle="Real-time analytics and predictive insights"
      tabs={screenerTabs}
      showSearch={true}
      aiPromptFullWidth={true}
    >
      <Suspense fallback={
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-4 border-brand border-t-transparent rounded-full animate-spin" />
        </div>
      }>
        {renderTab()}
      </Suspense>
    </DashboardLayout>
  );
};

export default ScreenerPage;
