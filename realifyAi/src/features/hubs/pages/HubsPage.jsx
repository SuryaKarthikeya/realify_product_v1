import { useState, useCallback } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import HubsHeader from '@/features/hubs/components/HubsHeader';
import DiscoverSection from '@/features/hubs/components/DiscoverSection';
import PluginDetail from '@/features/hubs/components/PluginDetail';
import CheckoutModal from '@/features/hubs/components/CheckoutModal';
import { PLUGINS } from '@/features/hubs/data/hubsData';

// ─── Empty States ─────────────────────────────────────────────────────────────

const InstalledTab = () => (
  <main className="p-3 sm:p-4">
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="w-16 h-16 bg-gray-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center text-2xl text-gray-400 mb-4">
        <i className="fa-solid fa-puzzle-piece" />
      </div>
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">2 Plugins Installed</h3>
      <p className="text-sm text-gray-500 dark:text-slate-400 max-w-xs">
        Your installed plugins will appear here. Manage subscriptions and settings from this tab.
      </p>
    </div>
  </main>
);

const UpdatesTab = () => (
  <main className="p-3 sm:p-4">
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-2xl flex items-center justify-center text-2xl text-blue-500 mb-4">
        <i className="fa-solid fa-arrow-up-from-bracket" />
      </div>
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">1 Update Available</h3>
      <p className="text-sm text-gray-500 dark:text-slate-400 max-w-xs">
        Plugin updates will appear here. Keep your installed plugins up-to-date for the latest features.
      </p>
      <button className="mt-4 px-6 py-2.5 bg-brand text-white text-sm font-medium rounded-xl hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition">
        Update All
      </button>
    </div>
  </main>
);

// ─── HubsPage ─────────────────────────────────────────────────────────────────

const HubsPage = () => {
  const [activeTab, setActiveTab] = useState('discover');
  const [viewMode, setViewMode] = useState('list');
  const [selectedPluginId, setSelectedPluginId] = useState(null);
  const [openMainFAQs, setOpenMainFAQs] = useState({});
  const [openDetailFAQs, setOpenDetailFAQs] = useState({});
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [checkoutState, setCheckoutState] = useState('idle');

  const selectedPlugin = selectedPluginId ? PLUGINS[selectedPluginId] : null;

  const handleTabChange = useCallback((tab) => {
    setActiveTab(tab);
    setSelectedPluginId(null);
  }, []);

  const handleSelectPlugin = useCallback((id) => {
    setSelectedPluginId(id);
    setOpenDetailFAQs({});
    window.scrollTo(0, 0);
  }, []);

  const handleBack = useCallback(() => {
    setSelectedPluginId(null);
    window.scrollTo(0, 0);
  }, []);

  const handleToggleMainFAQ = useCallback((i) => {
    setOpenMainFAQs((prev) => ({ ...prev, [i]: !prev[i] }));
  }, []);

  const handleToggleDetailFAQ = useCallback((i) => {
    setOpenDetailFAQs((prev) => ({ ...prev, [i]: !prev[i] }));
  }, []);

  const handleOpenCheckout = useCallback(() => setCheckoutOpen(true), []);

  const handleCloseCheckout = useCallback(() => {
    setCheckoutOpen(false);
    setTimeout(() => setCheckoutState('idle'), 400);
  }, []);

  const handleProcessCheckout = useCallback(() => {
    setCheckoutState('processing');
    setTimeout(() => {
      setCheckoutState('success');
      setTimeout(() => {
        setCheckoutOpen(false);
        setTimeout(() => setCheckoutState('idle'), 400);
      }, 1500);
    }, 2000);
  }, []);

  return (
    <DashboardLayout hideHeader noPadding showAIPrompt={false}>
      <HubsHeader activeTab={activeTab} onTabChange={handleTabChange} />

      {activeTab === 'discover' && (
        selectedPlugin ? (
          <PluginDetail
            plugin={selectedPlugin}
            onBack={handleBack}
            onCheckout={handleOpenCheckout}
            openFAQs={openDetailFAQs}
            onToggleFAQ={handleToggleDetailFAQ}
          />
        ) : (
          <DiscoverSection
            viewMode={viewMode}
            onViewMode={setViewMode}
            onSelect={handleSelectPlugin}
            openFAQs={openMainFAQs}
            onToggleFAQ={handleToggleMainFAQ}
          />
        )
      )}

      {activeTab === 'installed' && <InstalledTab />}
      {activeTab === 'updates' && <UpdatesTab />}

      {checkoutOpen && selectedPlugin && (
        <CheckoutModal
          plugin={selectedPlugin}
          state={checkoutState}
          onClose={handleCloseCheckout}
          onProcess={handleProcessCheckout}
        />
      )}
    </DashboardLayout>
  );
};

export default HubsPage;
