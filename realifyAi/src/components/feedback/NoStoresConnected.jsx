import React from 'react';
import { useNavigate } from 'react-router-dom';

const SUGGESTED = [
  {
    id: 'amazon',
    name: 'Amazon Seller',
    icon: 'fa-amazon',
    desc: 'Sync FBA/FBM orders & Inventory.',
    popular: true,
    color: 'text-orange-500',
    bg: 'bg-orange-50 dark:bg-orange-900/20',
  },
  {
    id: 'shopify',
    name: 'Shopify',
    icon: 'fa-shopify',
    desc: 'Direct API sync for DTC sales.',
    popular: false,
    color: 'text-green-600',
    bg: 'bg-green-50 dark:bg-green-900/20',
  },
  {
    id: 'walmart',
    name: 'Walmart Marketplace',
    icon: 'fa-store',
    desc: 'Expand your multi-channel reach.',
    popular: false,
    color: 'text-blue-600',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    iconLib: 'fa-solid',
  },
];

const NoStoresConnected = () => {
  const navigate = useNavigate();

  const goToIntegrations = () => navigate('/settings?tab=integrations');

  return (
    <div className="flex flex-col items-center py-8 px-6 min-h-full">
      <div className="w-full max-w-md flex flex-col items-center text-center">
        {/* Icon */}
        <div className="w-16 h-16 rounded-2xl bg-brand/10 dark:bg-brand/20 flex items-center justify-center mb-5 shadow-sm">
          <i className="fa-solid fa-store text-2xl text-brand" />
        </div>

        <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">
          No stores connected
        </h2>
        <p className="text-sm text-gray-500 dark:text-slate-400 leading-relaxed mb-7 max-w-xs">
          Connect your marketplace accounts to begin analyzing your cross-channel
          sales, margins, and operational health.
        </p>

        <button
          onClick={goToIntegrations}
          className="flex items-center gap-2 px-6 py-2.5 bg-gray-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-xl text-sm font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition-all active:scale-95 shadow mb-6"
        >
          <i className="fa-solid fa-plug text-xs" />
          Connect Marketplace
        </button>
      </div>

      {/* Suggested Integrations */}
      {/* <div className="w-full max-w-xl">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide">
            Suggested Integrations
          </span>
          <button
            onClick={goToIntegrations}
            className="text-xs text-brand dark:text-blue-400 hover:underline font-medium"
          >
            View all 12 →
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {SUGGESTED.map((s) => (
            <div
              key={s.id}
              className="relative border border-gray-100 dark:border-slate-800 rounded-2xl p-4 bg-white dark:bg-slate-900 hover:border-gray-200 dark:hover:border-slate-700 hover:shadow-sm transition-all flex flex-col gap-3"
            >
              {s.popular && (
                <span className="absolute top-3 right-3 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-[9px] font-bold rounded-full">
                  Popular
                </span>
              )}
              <div className={`w-10 h-10 ${s.bg} rounded-xl flex items-center justify-center`}>
                <i className={`${s.iconLib || 'fa-brands'} ${s.icon} ${s.color} text-lg`} />
              </div>
              <div>
                <p className="text-xs font-bold text-gray-900 dark:text-slate-100">{s.name}</p>
                <p className="text-[11px] text-gray-500 dark:text-slate-500 mt-0.5">{s.desc}</p>
              </div>
              <button
                onClick={goToIntegrations}
                className="mt-auto w-full py-1.5 bg-gray-900 dark:bg-slate-700 text-white text-xs font-bold rounded-lg hover:bg-gray-700 dark:hover:bg-slate-600 transition-all active:scale-95"
              >
                Connect
              </button>
            </div>
          ))}
        </div>
      </div> */}
    </div>
  );
};

export default NoStoresConnected;
