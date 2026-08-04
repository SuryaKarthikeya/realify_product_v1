import React, { useState } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import AutoConnectMarketplaces from '@/features/onboarding/components/AutoConnectMarketplaces';
import ManualEntryBox from '@/features/onboarding/components/ManualEntryBox';
import ConnectionResultArea from '@/features/onboarding/components/ConnectionResultArea';

const MarketplaceConnectionPage = () => {
  const [results, setResults] = useState([]);

  const addResult = (newResult) => {
    setResults(prev => [newResult, ...prev]);
  };

  return (
    <DashboardLayout
      title="Connect Your Marketplaces"
      subtitle="Complete your store integration to unlock AI-powered intelligence and margin analysis"
      showTabs={false}
      showAIPrompt={false}
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 h-[calc(100vh-220px)] min-h-[600px]">
        {/* Left Column - Auto Connect */}
        <div className="lg:col-span-4 h-full">
          <AutoConnectMarketplaces />
        </div>

        {/* Middle Column - Results */}
        <div className="lg:col-span-4 h-full border-x border-gray-100 dark:border-slate-800/50">
          <ConnectionResultArea results={results} />
        </div>

        {/* Right Column - Manual Entry */}
        <div className="lg:col-span-4 h-full">
          <ManualEntryBox onResult={addResult} />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default MarketplaceConnectionPage;
