import React from 'react';

// Shown whenever a user edits data that only lives in Realify until they push
// it back out — the product listing bulk-edit view and the product detail
// page both surface this same reminder.
const MarketplaceSyncBanner = ({ onGoToMarketplace }) => (
  <div className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/40">
    <div className="flex items-start gap-2.5">
      <i className="fa-solid fa-circle-info text-amber-500 dark:text-amber-400 mt-0.5 flex-shrink-0 text-sm" />
      <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
        Changes made here apply only within the Realify platform. To sync these updates with your marketplace, create a stimulation and execute it.
      </p>
    </div>
    <button
      onClick={onGoToMarketplace}
      className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 dark:bg-amber-500 text-white text-xs font-semibold hover:bg-amber-700 dark:hover:bg-amber-600 transition-colors whitespace-nowrap"
    >
      Go to Marketplace <i className="fa-solid fa-arrow-right text-[10px]" />
    </button>
  </div>
);

export default MarketplaceSyncBanner;
