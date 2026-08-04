import React from 'react';

const dummyData = [
  {
    id: 'PID-8821',
    name: 'Premium Wireless Headphones Gen 2',
    asin: 'B08N5KWB9H',
    marketplace: 'amazon',
    marketplaceIcon: 'fa-brands fa-amazon',
    marketplaceColor: 'text-orange-500',
    status: 'Synced',
    timestamp: 'Today, 10:45 AM'
  },
  {
    id: 'PID-4412',
    name: 'Ergonomic Standing Desk - Maple',
    asin: 'B09G96T278',
    marketplace: 'shopify',
    marketplaceIcon: 'fa-brands fa-shopify',
    marketplaceColor: 'text-green-600',
    status: 'Verified',
    timestamp: 'Today, 09:12 AM'
  },
  {
    id: 'PID-1190',
    name: 'Smart Home Hub - Pro Edition',
    asin: 'B07VGRJDFY',
    marketplace: 'ebay',
    marketplaceIcon: 'fa-brands fa-ebay',
    marketplaceColor: 'text-red-500',
    status: 'Active',
    timestamp: 'Yesterday, 04:30 PM'
  },
  {
    id: 'PID-8821',
    name: 'Premium Wireless Headphones Gen 2',
    asin: 'B08N5KWB9H',
    marketplace: 'amazon',
    marketplaceIcon: 'fa-brands fa-amazon',
    marketplaceColor: 'text-orange-500',
    status: 'Synced',
    timestamp: 'Today, 10:45 AM'
  }, {
    id: 'PID-8821',
    name: 'Premium Wireless Headphones Gen 2',
    asin: 'B08N5KWB9H',
    marketplace: 'amazon',
    marketplaceIcon: 'fa-brands fa-amazon',
    marketplaceColor: 'text-orange-500',
    status: 'Synced',
    timestamp: 'Today, 10:45 AM'
  }, {
    id: 'PID-8821',
    name: 'Premium Wireless Headphones Gen 2',
    asin: 'B08N5KWB9H',
    marketplace: 'amazon',
    marketplaceIcon: 'fa-brands fa-amazon',
    marketplaceColor: 'text-orange-500',
    status: 'Synced',
    timestamp: 'Today, 10:45 AM'
  }
];

const ConnectionResultArea = ({ results }) => {
  const allResults = results.length > 0 ? results : [];

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6 px-4">
        <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Activity Log</h3>
        <p className="text-sm text-gray-600 dark:text-slate-400">Processing results & connection history</p>
      </div>

      <div className="flex-1 overflow-y-auto hide-scroll px-4 space-y-4">
        {/* Real-time Results */}
        {allResults.map((res, idx) => (
          <div key={`real-${idx}`} className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 shadow-sm anim-fade-in relative overflow-hidden group">
            <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${res.type === 'csv' ? 'bg-green-100 text-green-600' : 'bg-purple-100 text-purple-600'
                  }`}>
                  <i className={`fa-solid ${res.type === 'csv' ? 'fa-file-csv' : 'fa-keyboard'} text-sm`}></i>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100">
                    {res.type === 'csv' ? 'CSV Import Successful' : 'Manual Entry Processed'}
                  </h4>
                  <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold tracking-wider">{res.timestamp}</p>
                </div>
              </div>
              <span className="text-[10px] bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 px-2 py-0.5 rounded-full font-bold border border-green-100 dark:border-green-900/40">
                SUCCESS
              </span>
            </div>

            <div className="pl-10">
              {res.type === 'csv' ? (
                <p className="text-xs text-gray-600 dark:text-slate-400">
                  File <span className="font-semibold text-gray-800 dark:text-slate-200">"{res.fileName}"</span> was processed. <span className="text-blue-600 font-bold">{res.count} products</span> identified and synced.
                </p>
              ) : (
                <div className="space-y-1">
                  <p className="text-xs text-gray-600 dark:text-slate-400">
                    Processed <span className="text-blue-600 font-bold">{res.items.length} product codes</span>.
                  </p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {res.items.slice(0, 3).map((asin, i) => (
                      <span key={i} className="text-[10px] bg-gray-100 dark:bg-slate-800 px-1.5 py-0.5 rounded border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-400">
                        {asin}
                      </span>
                    ))}
                    {res.items.length > 3 && <span className="text-[10px] text-gray-400">+{res.items.length - 3} more</span>}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Dummy Previews (always show or show when empty) */}
        <div className="pt-4 border-t border-gray-100 dark:border-slate-800">
          <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-4">Sample Identifications</p>
          <div className="space-y-3 opacity-70">
            {dummyData.map((item, idx) => (
              <div key={`dummy-${idx}`} className="bg-gray-50/50 dark:bg-slate-800/20 border border-gray-200 dark:border-slate-800/50 rounded-xl p-3 flex items-center justify-between group hover:opacity-100 transition-opacity">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-lg border border-gray-100 dark:border-slate-800 flex items-center justify-center relative shadow-sm">
                    <i className="fa-solid fa-box text-gray-400 dark:text-slate-600"></i>
                    <div className="absolute -bottom-1 -right-1 bg-white dark:bg-slate-900 rounded-full p-0.5 border border-gray-100 dark:border-slate-800">
                      <i className={`${item.marketplaceIcon} ${item.marketplaceColor} text-[10px]`}></i>
                    </div>
                  </div>
                  <div>
                    <h5 className="text-[13px] font-bold text-gray-800 dark:text-slate-200 truncate max-w-[140px]">{item.name}</h5>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-gray-500 dark:text-slate-500">ID: {item.id}</span>
                      <span className="text-[10px] text-blue-500 font-medium">ASIN: {item.asin}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-green-600 font-bold">{item.status}</div>
                  <div className="text-[9px] text-gray-400 dark:text-slate-500">{item.timestamp}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 px-4">
        <button className="w-full py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 text-xs font-bold rounded-xl transition-all border border-gray-200 dark:border-slate-700">
          Sync Status Report
        </button>
      </div>
    </div>
  );
};

export default ConnectionResultArea;
