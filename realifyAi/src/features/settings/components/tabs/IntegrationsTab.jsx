import React, { useState } from 'react';
import { useMarketplaceStore } from '@/store/useMarketplaceStore';

const INTEGRATIONS = [
  {
    id: 'amazon',
    name: 'Amazon SP-API',
    subtitle: 'Connect your Amazon Seller account',
    icon: 'fa-amazon',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100 dark:bg-orange-900/20',
    fieldLabel: 'Amazon Seller ID',
    fieldPlaceholder: 'Enter your Seller ID',
    dummyDetail: 'Seller ID connected · Synced just now',
  },
  {
    id: 'shopify',
    name: 'Shopify',
    subtitle: 'Connect your Shopify store',
    icon: 'fa-shopify',
    color: 'text-green-600',
    bgColor: 'bg-green-100 dark:bg-green-900/20',
    fieldLabel: 'Shopify Store URL',
    fieldPlaceholder: 'yourstore.myshopify.com',
    dummyDetail: (val) => `${val} · Synced just now`,
  },
  {
    id: 'google-ads',
    name: 'Google Ads',
    subtitle: 'Connect your Google Ads account',
    icon: 'fa-google',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100 dark:bg-blue-900/20',
    fieldLabel: 'Google Ads Customer ID',
    fieldPlaceholder: 'Enter your Customer ID',
    dummyDetail: 'Customer ID connected · Synced just now',
  },
  {
    id: 'meta-ads',
    name: 'Meta Ads',
    subtitle: 'Connect your Meta Ads account',
    icon: 'fa-meta',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100 dark:bg-blue-900/20',
    fieldLabel: 'Meta Ad Account ID',
    fieldPlaceholder: 'Enter your Ad Account ID',
    dummyDetail: 'Ad Account connected · Synced just now',
  },
];

const ConnectForm = ({ platform, onClose, onConnected }) => {
  const [value, setValue] = useState('');
  const [connecting, setConnecting] = useState(false);

  const handleConnect = () => {
    if (!value.trim()) return;
    setConnecting(true);
    setTimeout(() => {
      onConnected(value.trim());
      setConnecting(false);
    }, 1200);
  };

  return (
    /* The card and its contents were hardcoded light, so this dialog stayed
       white while the rest of the app was dark. The platform icon tiles already
       carry their own dark tints via `bgColor`, so only the chrome needed it. */
    <div className="fixed inset-0 z-[9999] flex items-start sm:items-center justify-center px-4 py-5 sm:px-0 sm:py-0 overflow-y-auto bg-black/40 dark:bg-black/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100 dark:border-slate-800">
          <div className={`w-10 h-10 ${platform.bgColor} rounded-xl flex items-center justify-center flex-shrink-0`}>
            <i className={`fa-brands ${platform.icon} ${platform.color} text-xl`} />
          </div>
          <div>
            <p className="text-sm font-bold text-gray-900 dark:text-white">{platform.name}</p>
            <p className="text-xs text-gray-500 dark:text-slate-400">{platform.subtitle}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-auto text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 transition-colors p-1"
          >
            <i className="fa-solid fa-xmark text-sm" />
          </button>
        </div>

        {/* Form */}
        <div className="px-6 py-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-slate-300 mb-2">
              {platform.fieldLabel}
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={platform.fieldPlaceholder}
              className="w-full bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-500 focus:outline-none focus:border-blue-400 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-500/20 transition-all"
              onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
            />
          </div>

          <button
            onClick={handleConnect}
            disabled={!value.trim() || connecting}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 shadow-md"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #2563eb)' }}
          >
            {connecting ? (
              <>
                <i className="fa-solid fa-circle-notch fa-spin text-sm" />
                Connecting...
              </>
            ) : (
              <>
                <i className="fa-solid fa-plug text-xs" />
                Connect Seller
              </>
            )}
          </button>

          <button
            onClick={onClose}
            className="w-full py-2 text-sm text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

const IntegrationsTab = () => {
  const { connectedStores, addStore, removeStore } = useMarketplaceStore();
  const [connectingPlatform, setConnectingPlatform] = useState(null);
  const [justConnected, setJustConnected] = useState(null);

  const isConnected = (id) => connectedStores.some((s) => s.id === id);
  const getStore = (id) => connectedStores.find((s) => s.id === id);

  const handleConnected = (platform, value) => {
    const detail =
      typeof platform.dummyDetail === 'function'
        ? platform.dummyDetail(value)
        : platform.dummyDetail;

    addStore({ id: platform.id, name: platform.name, sellerId: value, detail, connectedAt: Date.now() });
    setConnectingPlatform(null);
    setJustConnected(platform.id);
    setTimeout(() => setJustConnected(null), 3000);
  };

  const handleDisconnect = (id) => {
    removeStore(id);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm">
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Integrations</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
          Manage your connected data sources and marketing platforms
        </p>
      </div>

      <div className="p-6 space-y-4">
        {INTEGRATIONS.map((app) => {
          const connected = isConnected(app.id);
          const store = getStore(app.id);

          return (
            <div
              key={app.id}
              className="flex items-center justify-between p-5 border border-gray-100 dark:border-slate-800 rounded-2xl hover:border-gray-200 dark:hover:border-slate-700 transition-all hover:shadow-sm"
            >
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 ${app.bgColor} rounded-2xl flex items-center justify-center shadow-sm`}>
                  <i className={`fa-brands ${app.icon} ${app.color} text-2xl`} />
                </div>
                <div>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{app.name}</p>
                  <p className="text-xs text-gray-500 dark:text-slate-500 mt-0.5">
                    {connected ? store?.detail : app.subtitle}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {connected ? (
                  <>
                    <span className="flex items-center gap-1.5 px-3 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-full text-[10px] font-bold border border-green-100 dark:border-green-800">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                      CONNECTED
                    </span>
                    <button className="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-all">
                      Re-auth
                    </button>
                    <button
                      onClick={() => handleDisconnect(app.id)}
                      className="px-4 py-2 bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 rounded-xl text-sm font-bold hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setConnectingPlatform(app)}
                    className="px-6 py-2 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition-all shadow-md active:scale-95"
                  >
                    Connect
                  </button>
                )}

                {justConnected === app.id && (
                  <span className="text-xs text-green-600 dark:text-green-400 font-semibold flex items-center gap-1">
                    <i className="fa-solid fa-check" /> Connected!
                  </span>
                )}
              </div>
            </div>
          );
        })}

        {/* CSV Upload */}
        <div className="flex items-center justify-between p-5 border border-gray-100 dark:border-slate-800 rounded-2xl bg-gray-50/50 dark:bg-slate-800/30 border-dashed">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gray-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center">
              <i className="fa-solid fa-file-csv text-gray-600 dark:text-slate-400 text-2xl" />
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Smart CSV Upload</p>
              <p className="text-xs text-gray-500 dark:text-slate-500 mt-0.5">3 files uploaded · Last: COGS_Q1.csv</p>
            </div>
          </div>
          <button className="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-all">
            <i className="fa-solid fa-upload mr-2" />
            Upload File
          </button>
        </div>
      </div>

      {/* Connect form modal */}
      {connectingPlatform && (
        <ConnectForm
          platform={connectingPlatform}
          onClose={() => setConnectingPlatform(null)}
          onConnected={(val) => handleConnected(connectingPlatform, val)}
        />
      )}
    </div>
  );
};

export default IntegrationsTab;
