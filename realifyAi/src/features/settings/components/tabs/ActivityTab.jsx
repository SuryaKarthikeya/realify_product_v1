import React, { useState } from 'react';

const ActivityTab = () => {
  const [activeTab, setActiveTab] = useState('Log');

  const mockLogs = [
    {
      id: 1,
      type: 'Case / report',
      time: '10:36:07',
      title: 'No settlement shortfall above threshold right now.',
      desc: 'Realify queried your settled orders, found those where the actual deposit fell short of the expected (gross — referral — FBA fees), summed the recoverable gap, and drafted a case body with the real order IDs. Realify does NOT file the case — you open the Case Log and paste. Every figure here comes from your own order/settlement data.',
      labels: ['DRAFT + DEEP-LINK', 'C8']
    },
    {
      id: 2,
      type: 'Dismissed.',
      time: '10:35:21',
      title: 'Dismissed.',
      desc: 'You dismissed this card. Realify removes it from the feed; the underlying condition is re-checked on the next data pull, so if it recurs it will surface again as a new card.',
      labels: ['INTERNAL', 'SALES-08']
    },
    {
      id: 3,
      type: 'Case / report',
      time: '10:35:21',
      title: 'No settlement shortfall above threshold right now.',
      desc: 'Realify queried your settled orders, found those where the actual deposit fell short of the expected (gross — referral — FBA fees), summed the recoverable gap, and drafted a case body with the real order IDs. Realify does NOT file the case — you open the Case Log and paste. Every figure here comes from your own order/settlement data.',
      labels: ['DRAFT + DEEP-LINK', 'C8']
    },
    {
      id: 4,
      type: 'Case / report',
      time: '10:35:17',
      title: 'No settlement shortfall above threshold right now.',
      desc: 'Realify queried your settled orders, found those where the actual deposit fell short of the expected (gross — referral — FBA fees), summed the recoverable gap, and drafted a case body with the real order IDs. Realify does NOT file the case — you open the Case Log and paste. Every figure here comes from your own order/settlement data.',
      labels: ['DRAFT + DEEP-LINK', 'C8']
    }
  ];

  return (
    /* Header block + padded body, matching every other settings tab: the page
       renders each tab into a bare rounded card and expects the tab to supply
       its own `p-6`. Without it the heading and cards sat flush against the
       card's edge, and `max-w-4xl` stopped them short of its right edge. */
    <div>
      <div className="px-6 pt-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Activity</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
          Every action Realify took on your account, newest first
        </p>

        {/* Tabs */}
        <div className="flex items-center gap-6 mt-4">
          {['Log', 'Sourcing', 'Watchlist'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 text-[14px] font-semibold transition-colors relative ${
                activeTab === tab
                  ? 'text-gray-900 dark:text-white'
                  : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300'
              }`}
            >
              {tab}
              {activeTab === tab && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-white rounded-t-sm" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 space-y-4">
        {activeTab === 'Log' && (
          mockLogs.map(log => (
            <div key={log.id} className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-2xl p-5 shadow-sm transition-all hover:shadow-md">
              <div className="flex items-start justify-between mb-2.5">
                <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100">{log.type}</h3>
                <span className="text-[11px] text-gray-400 dark:text-slate-500 font-sans tracking-wide bg-gray-50 dark:bg-slate-900 px-2 py-0.5 rounded border border-gray-100 dark:border-slate-700/50">{log.time}</span>
              </div>
              <p className="text-[14px] text-gray-800 dark:text-slate-200 font-bold mb-3">
                {log.title}
              </p>
              <p className="text-[13px] leading-relaxed text-gray-600 dark:text-slate-400 mb-4">
                {log.desc}
              </p>
              <div className="flex items-center gap-2 flex-wrap">
                {log.labels.map((label, idx) => (
                  <span 
                    key={idx} 
                    className="px-2 py-1 bg-gray-100 dark:bg-slate-900 text-gray-600 dark:text-slate-400 text-[10px] font-bold font-sans tracking-wider rounded border border-gray-200/60 dark:border-slate-700/60 uppercase"
                  >
                    {label}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}

        {activeTab === 'Sourcing' && (
          <div className="text-center py-8 text-gray-500 dark:text-slate-400">
            <i className="fa-solid fa-cart-shopping text-4xl mb-4 opacity-50 block"></i>
            <p>Your sourcing list is currently empty.</p>
          </div>
        )}

        {activeTab === 'Watchlist' && (
          <div className="text-center py-8 text-gray-500 dark:text-slate-400">
            <i className="fa-regular fa-eye text-4xl mb-4 opacity-50 block"></i>
            <p>You aren't watching any items yet.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityTab;
