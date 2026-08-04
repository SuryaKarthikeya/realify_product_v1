import React, { lazy, Suspense, useState, useEffect, useRef } from 'react';
import { formatCompactCurrency } from '@/utils/formatters';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import StatCard from '@/components/data-display/StatCard';
import BaseAreaChart from '@/components/data-display/charts/BaseAreaChart';
import { revenueTrendData } from '@/features/workspace/domains/revenue';

import ProductHeatmap from '@/features/workspace/modules/dashboard-view/components/ProductHeatmap';
import ChannelMixWidget from '@/features/workspace/modules/dashboard-view/components/ChannelMixWidget';
import SectionHeading from '@/components/data-display/SectionHeading';
import StickyKpiStrip from '@/features/workspace/modules/dashboard-view/components/StickyKpiStrip';
import { useStickyOnScroll, SCROLL_CONTAINER_SELECTOR } from '@/hooks/useStickyOnScroll';
import DashboardViewTabNav from '@/features/workspace/modules/dashboard-view/components/DashboardViewTabNav';

import BriefCard from '@/components/data-display/brief/BriefCard';
import BriefHeaderControls from '@/components/data-display/brief/BriefHeaderControls';
import { REALIFY_BRIEF } from '@/data/briefData';
import { useViewModeStore } from '@/store/useViewModeStore';
import { DOMAIN_KPI_CARDS, PAGE_TITLES, BACK_ROUTES } from '@/features/workspace/modules/dashboard-view/data/dashboardViewData';

import { RevenueTables } from '@/features/workspace/domains/revenue';
import { MarginTables as MarginDashboardGrid } from '@/features/workspace/domains/margin';
import { InventoryTables } from '@/features/workspace/domains/inventory';
import { AdsTables } from '@/features/workspace/domains/ads';
import { CashTables as CashPageTables } from '@/features/workspace/domains/cash';

// Margin — used directly in the Row 1 "Bleeding Margin SKUs" panel
import { BleedingMarginTable, MarginWaterfall } from '@/features/workspace/domains/margin';
import { CashFlowTable } from '@/features/workspace/domains/cash';
import { dashboardPath, toDomainKey } from '@/features/workspace/workspaceRoutes';
import { ROUTES } from '@/constants/routes';

// Inventory charts — lazy: only loaded when domain === 'inventory'
const InventoryTrendChart = lazy(() => import('@/features/workspace/domains/inventory/components/InventoryTrendChart'));
const StockStatusChart = lazy(() => import('@/features/workspace/domains/inventory/components/StockStatusChart'));
const DOCDistributionChart = lazy(() => import('@/features/workspace/domains/inventory/components/DOCDistributionChart'));
const ForecastActualChart = lazy(() => import('@/features/workspace/domains/inventory/components/ForecastActualChart'));

// Ads charts — lazy: only loaded when domain === 'ads'
const AdSpendTrendChart = lazy(() => import('@/features/workspace/domains/ads/components/AdSpendTrendChart'));

// Cash charts — lazy: only loaded when domain === 'cash'
const CashFlowTrendSection = lazy(() => import('@/features/workspace/domains/cash/components/CashFlowTrendSection'));

const TABLES_MAP = { sales: RevenueTables, inventory: InventoryTables, ads: AdsTables, cash: CashPageTables };

const DashboardViewPage = () => {
  const { domain: domainSegment } = useParams();
  const domain = toDomainKey(domainSegment);
  const location = useLocation();
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);
  const kpiSectionRef = useRef(null);
  // Sticky KPI ribbon takes over once the KPI section is < 28% visible.
  const kpiIsSticky = useStickyOnScroll(kpiSectionRef, {
    threshold: [0, 0.1, 0.25, 0.28, 0.5, 1.0],
    isStuck: (entry) => entry.intersectionRatio < 0.28,
  });

  // Remember that Dashboard View (this page) is the active view + which tab, so
  // navigating away and back to Workspace (e.g. via the sidebar) restores it.
  const { setDashboardView, setLastWorkspaceDomain } = useViewModeStore();
  useEffect(() => {
    setDashboardView(true);
    setLastWorkspaceDomain(domain);
  }, [domain]); // eslint-disable-line react-hooks/exhaustive-deps

  // The same five domain cards on every dashboard — clicking one changes the
  // content below, not the cards themselves.
  const statsData = DOMAIN_KPI_CARDS;
  const pageTitle = PAGE_TITLES[domain] || 'Sales';
  const backRoute = location.state?.from || BACK_ROUTES[domain] || ROUTES.WORKSPACE;

  const briefData = REALIFY_BRIEF[domain] || REALIFY_BRIEF.sales;

  const TablesComponent = TABLES_MAP[domain] || RevenueTables;

  // Scroll detection — shows tabs in sticky header, collapses search bar
  useEffect(() => {
    const el = document.querySelector(SCROLL_CONTAINER_SELECTOR);
    if (!el) return;
    const onScroll = () => setIsScrolled(el.scrollTop > 30);
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  const goToTab = (tabKey) => navigate(dashboardPath(tabKey), { state: { from: backRoute } });

  return (
    <DashboardLayout
      title="Intelligence"
      subtitle={`${pageTitle} — Detailed View`}
      showTabs={false}
      showAIPrompt={false}
      filters={null}
      showSearch={true}
      searchCollapsed={isScrolled}
      customRightElement={null}
    >
      <StickyKpiStrip
        kpiIsSticky={kpiIsSticky}
        statsData={statsData}
        /* The strip is the same five cards as the grid below, so it marks the
           current domain and switches domain the same way. */
        activeDomain={domain}
        onSelectDomain={goToTab}
        onDashboardClick={() => navigate(backRoute)}
      />

      {/* Realify Brief and Filters */}
      <div className="flex flex-col space-y-4 mb-4">
        <BriefCard data={briefData} />

        {/* Filters + Dashboard Toggle */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <BriefHeaderControls
            isDashboardViewActive={true}
            onDashboardToggle={() => navigate(backRoute)}
          />
        </div>

        {/* Tab Navigation */}
        {/* <div className="border-b border-gray-100 dark:border-slate-800 mb-5 pb-2">
          <DashboardViewTabNav domain={domain} onTabClick={goToTab} />
        </div> */}
      </div>

      {/* KPI cards — the five domains, acting as this page's navigation */}
      <div ref={kpiSectionRef} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5 sm:gap-3 mb-4">
        {statsData.map(stat => (
          <StatCard
            key={stat.domainKey}
            title={stat.title}
            value={stat.value}
            change={stat.change}
            isPositive={stat.isPositive}
            subtext={stat.subtext}
            isSelected={stat.domainKey === domain}
            onClick={() => goToTab(stat.domainKey)}
          />
        ))}
      </div>

      {/* Main dashboard content */}
      <div className="space-y-4">

        {/* Row 1: For margin — BleedingMarginSKUs + ChannelMix. For others — primary trend chart + ChannelMix */}
        {domain === 'margin' ? (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100">Bleeding Margin SKUs</h4>
                  <span className="text-[11px] text-gray-400 dark:text-slate-500">Sorted by $ at risk descending</span>
                </div>
                <BleedingMarginTable onRowClick={() => { }} hideTitleBar />
              </div>
              <div><ChannelMixWidget /></div>
            </div>

            {/* Sits directly under Bleeding Margin SKUs — the table names which
                SKUs leak margin, this explains where the margin goes overall. */}
            <MarginWaterfall />
          </>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:items-stretch">
            <div className="lg:col-span-2 flex flex-col">
              {domain === 'sales' && (
                <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden h-full flex flex-col">
                  <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-800 flex-shrink-0">
                    <p className="text-xs font-bold text-gray-800 dark:text-slate-200">Revenue Trend</p>
                  </div>
                  <div className="p-3">
                    <BaseAreaChart
                      data={revenueTrendData}
                      yAxisFormatter={v => formatCompactCurrency(v)}
                      tooltipFormatter={(v, n) => [formatCompactCurrency(v), n]}
                      areas={[{ key: 'revenue', name: 'Revenue Trend', color: '#22c55e' }]}
                      height={308}
                    />
                  </div>
                </div>
              )}
              {domain === 'inventory' && (
                <Suspense fallback={<div className="min-h-[200px] rounded-2xl bg-gray-100 dark:bg-slate-800 animate-pulse" />}>
                  <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden h-full flex flex-col">
                    <div className="flex-1 min-h-0 p-4"><InventoryTrendChart /></div>
                  </div>
                </Suspense>
              )}
              {domain === 'ads' && (
                <Suspense fallback={<div className="min-h-[200px] rounded-2xl bg-gray-100 dark:bg-slate-800 animate-pulse" />}>
                  <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden h-full flex flex-col">
                    <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-800 flex-shrink-0">
                      <p className="text-xs font-bold text-gray-800 dark:text-slate-200">Ad Spend Trend</p>
                    </div>
                    <div className="flex-1 min-h-0 p-3"><AdSpendTrendChart /></div>
                  </div>
                </Suspense>
              )}
              {domain === 'cash' && (
                <Suspense fallback={<div className="min-h-[200px] rounded-2xl bg-gray-100 dark:bg-slate-800 animate-pulse" />}>
                  <div className="h-full"><CashFlowTrendSection /></div>
                </Suspense>
              )}
            </div>
            <div>
              <ChannelMixWidget />
            </div>
          </div>
        )}

        {/* Row 2: Product heatmap — every domain except inventory, which has its
            own Stock status / DOC / Forecast charts below and no use for a margin
            distribution grid. */}
        {domain !== 'inventory' && (
          <div className="bg-white dark:bg-[#030712] border border-gray-200 dark:border-slate-800 rounded-2xl p-4">
            <ProductHeatmap domain={domain} />
          </div>
        )}

        {/* Row 3: Secondary charts — remaining inventory charts */}
        {domain === 'inventory' && (
          <Suspense fallback={<div className="h-40 rounded-2xl bg-gray-100 dark:bg-slate-800 animate-pulse" />}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
              <StockStatusChart />
              <DOCDistributionChart />
              <ForecastActualChart />
            </div>
          </Suspense>
        )}

        {/* Row 4: KPI detail tables / Margin 50-50 grid */}
        {domain === 'margin' ? <MarginDashboardGrid /> : <TablesComponent />}
      </div>

      {domain === 'cash' && (
        <div className="mt-6">
          <SectionHeading title="Cash Flow" />
          <CashFlowTable />
        </div>
      )}

    </DashboardLayout>
  );
};

export default DashboardViewPage;
