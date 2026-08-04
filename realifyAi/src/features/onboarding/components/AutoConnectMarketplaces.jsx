import React from 'react';
import { useOnboardingStore } from '@/features/onboarding/store/useOnboardingStore';

const marketplaces = [
  { id: 'amazon', name: 'Amazon', icon: 'fa-brands fa-amazon', color: 'bg-orange-100', iconColor: 'text-orange-600', desc: 'Seller Central' },
  { id: 'shopify', name: 'Shopify', icon: 'fa-brands fa-shopify', color: 'bg-green-100', iconColor: 'text-green-600', desc: 'Shopify Store' },
  { id: 'woocommerce', name: 'WooCommerce', icon: 'fa-brands fa-wordpress', color: 'bg-purple-100', iconColor: 'text-purple-600', desc: 'WordPress Store' },
  { id: 'ebay', name: 'eBay', icon: 'fa-brands fa-ebay', color: 'bg-red-100', iconColor: 'text-red-600', desc: 'eBay Account' },
  { id: 'walmart', name: 'Walmart', icon: 'fa-solid fa-store', color: 'bg-blue-100', iconColor: 'text-blue-600', desc: 'Walmart Seller' },
];

const AutoConnectMarketplaces = () => {
  const { connectedMarketplaces, setActiveModal, setCurrentMarketplace } = useOnboardingStore();

  const handleConnect = (m) => {
    setCurrentMarketplace(m);
    setActiveModal("connection");
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm h-full">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Auto-Connect</h3>
        <p className="text-sm text-gray-600 dark:text-slate-400">One-click integration with major channels</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {marketplaces.map((m) => {
          const isConnected = connectedMarketplaces.includes(m.id);
          return (
            <div key={m.id} className="group relative flex items-center justify-between p-4 border border-gray-200 dark:border-slate-800 rounded-xl hover:border-blue-500 dark:hover:border-blue-400 transition-all bg-gray-50/50 dark:bg-slate-800/50">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 ${m.color} rounded-lg flex items-center justify-center`}>
                  <i className={`${m.icon} text-2xl ${m.iconColor}`}></i>
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 dark:text-slate-100">{m.name}</h4>
                  <p className="text-xs text-gray-500 dark:text-slate-400">{m.desc}</p>
                </div>
              </div>
              
              {isConnected ? (
                <div className="flex items-center text-green-600 dark:text-green-400 font-semibold text-sm">
                  <i className="fa-solid fa-check-circle mr-1.5"></i> Connected
                </div>
              ) : (
                <button 
                  onClick={() => handleConnect(m)}
                  className="px-4 py-2 bg-brand text-white text-sm font-semibold rounded-lg hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition"
                >
                  Connect
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-5 p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30 rounded-xl">
        <h4 className="text-sm font-bold text-blue-900 dark:text-blue-300 mb-2 flex items-center">
          <i className="fa-solid fa-bolt mr-2 text-yellow-500"></i>
          Instant Sync
        </h4>
        <p className="text-xs text-blue-700/80 dark:text-blue-400/80 leading-relaxed">
          Automated connections sync orders, inventory, and pricing data every 15 minutes.
        </p>
      </div>
    </div>
  );
};

export default AutoConnectMarketplaces;
