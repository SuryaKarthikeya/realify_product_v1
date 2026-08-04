import React from 'react';
import ModalPanel from '@/components/overlays/ModalPanel';

const ProductDetailModal = ({ isOpen, onClose, product }) => {
  if (!isOpen || !product) return null;

  // Mock data specifically tailored for the reference design screenshots
  const mockData = {
    cogs: product.cogs || '$247',
    margin: product.margin || '10.1%',
    velocity: product.velocity || product.inventory || '1,138',
    costStructure: {
      referral: '$21',
      fba: '$137',
      cogsUnit: product.cogs || '$247',
      freeReplacements: '25',
      aiSuggests: 'AI suggests $198 (high confidence) — ~44% of price · median of 1250 of your Automotive SKUs with confirmed COGS · tap to accept'
    },
    adsProfitability: {
      breakEvenAcos: product.margin || '10.1%',
      actualAcos: '—', // match ss2
      gap: 'No ad data yet' // match ss2
    },
    marginReality: {
      estAtLaunch: product.margin || '10.1%',
      actual: product.margin || '10.1%',
      gap: '▼ 0% margin leakage'
    }
  };

  return (
    <ModalPanel isOpen={isOpen} onClose={onClose} maxWidth="max-w-[850px]">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100 tracking-wide uppercase">
              {product.sku || 'SKU-UNKNOWN'}
            </h2>
            <button 
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg bg-transparent hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 transition-colors shrink-0 -mt-2 -mr-2"
            >
              <i className="fa-solid fa-xmark text-lg"></i>
            </button>
          </div>
          <p className="text-[15px] font-semibold text-gray-800 dark:text-slate-200 leading-snug mb-6 pr-8">
            {product.name}
          </p>

          {/* Summary Cards */}
          <div className="grid grid-cols-4 gap-3 mb-5">
            <div className="border border-gray-100 dark:border-slate-800 rounded-xl p-3 flex flex-col justify-center">
              <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">PRICE</p>
              <p className="text-lg font-bold text-gray-900 dark:text-slate-100">{product.price || '$451'}</p>
            </div>
            <div className="border border-gray-100 dark:border-slate-800 rounded-xl p-3 flex flex-col justify-center">
              <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">COGS</p>
              <p className="text-lg font-bold text-gray-900 dark:text-slate-100">{mockData.cogs}</p>
            </div>
            <div className="border border-gray-100 dark:border-slate-800 rounded-xl p-3 flex flex-col justify-center">
              <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">MARGIN</p>
              <p className="text-lg font-bold text-gray-900 dark:text-slate-100">{mockData.margin}</p>
            </div>
            <div className="border border-gray-100 dark:border-slate-800 rounded-xl p-3 flex flex-col justify-center">
              <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">UNITS/MO</p>
              <p className="text-lg font-bold text-gray-900 dark:text-slate-100">{mockData.velocity}</p>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            
            {/* COST STRUCTURE */}
            <div className="bg-indigo-50/40 dark:bg-indigo-900/10 border border-indigo-100 dark:border-indigo-800/30 rounded-xl p-5">
              <h3 className="text-[10px] font-bold text-indigo-500 dark:text-indigo-400 uppercase tracking-widest mb-4">COST STRUCTURE</h3>
              
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">REFERRAL / UNIT</p>
                  <p className="text-[15px] font-bold text-gray-900 dark:text-slate-100">{mockData.costStructure.referral}</p>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">FBA / UNIT</p>
                  <p className="text-[15px] font-bold text-gray-900 dark:text-slate-100">{mockData.costStructure.fba}</p>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">COGS / UNIT</p>
                  <div className="inline-flex items-center gap-1 border border-dashed border-indigo-300 dark:border-indigo-600 rounded px-1.5 py-0.5 -ml-1">
                    <span className="text-[15px] font-bold text-gray-900 dark:text-slate-100">{mockData.costStructure.cogsUnit}</span>
                    <i className="fa-solid fa-paperclip text-indigo-400 text-[10px]"></i>
                  </div>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">FREE REPLACEMENTS</p>
                  <p className="text-[15px] font-bold text-gray-900 dark:text-slate-100">{mockData.costStructure.freeReplacements}</p>
                </div>
              </div>
              
              <p className="text-xs font-medium text-indigo-500 dark:text-indigo-400 leading-relaxed">
                {mockData.costStructure.aiSuggests}
              </p>
            </div>

            {/* ADS PROFITABILITY */}
            <div className="bg-orange-50/30 dark:bg-orange-900/10 border border-orange-100 dark:border-orange-800/30 rounded-xl p-5">
              <h3 className="text-[10px] font-bold text-orange-600 dark:text-orange-500 uppercase tracking-widest mb-4">ADS PROFITABILITY</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">BREAK-EVEN ACOS</p>
                  <p className="text-[15px] font-bold text-gray-900 dark:text-slate-100">{mockData.adsProfitability.breakEvenAcos}</p>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">ACTUAL ACOS</p>
                  <p className="text-[15px] font-bold text-emerald-500 dark:text-emerald-400">{mockData.adsProfitability.actualAcos}</p>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">GAP</p>
                  <span className="inline-block px-2 py-0.5 bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400 text-xs font-bold rounded">
                    {mockData.adsProfitability.gap}
                  </span>
                </div>
              </div>
            </div>

            {/* MARGIN REALITY */}
            <div className="bg-red-50/40 dark:bg-red-900/10 border border-red-100 dark:border-red-800/30 rounded-xl p-5">
              <h3 className="text-[10px] font-bold text-red-500 dark:text-red-400 uppercase tracking-widest mb-4">MARGIN REALITY</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">EST. AT LAUNCH (modeled)</p>
                  <p className="text-[15px] font-bold text-gray-900 dark:text-slate-100">{mockData.marginReality.estAtLaunch}</p>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">ACTUAL (SETTLED)</p>
                  <p className="text-[15px] font-bold text-gray-900 dark:text-slate-100">{mockData.marginReality.actual}</p>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">GAP</p>
                  <p className="text-[14px] font-bold text-red-500 dark:text-red-400">{mockData.marginReality.gap}</p>
                </div>
              </div>
            </div>

            {/* STRATEGY & LABELS */}
            <div className="bg-emerald-50/40 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-800/30 rounded-xl p-5">
              <h3 className="text-[10px] font-bold text-emerald-600 dark:text-emerald-500 uppercase tracking-widest mb-4">STRATEGY & LABELS</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">LIFECYCLE</p>
                  <div className="relative inline-block w-40">
                    <select className="w-full appearance-none bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-md py-1.5 pl-3 pr-8 text-[13px] font-bold text-gray-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20">
                      <option value="launch">launch</option>
                      <option value="clearance">clearance</option>
                      <option value="seasonal">seasonal</option>
                      <option value="discontinued">discontinued</option>
                    </select>
                    <i className="fa-solid fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-gray-500 pointer-events-none"></i>
                  </div>
                </div>
                <div>
                  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">OPTIMIZE FOR</p>
                  <div className="relative inline-block w-40">
                    <select className="w-full appearance-none bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-md py-1.5 pl-3 pr-8 text-[13px] font-bold text-gray-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20">
                      <option value="none">&mdash;</option>
                      <option value="cash_flow">Cash Flow</option>
                      <option value="margin">Margin</option>
                      <option value="growth">Growth</option>
                    </select>
                    <i className="fa-solid fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-gray-500 pointer-events-none"></i>
                  </div>
                </div>
              </div>
            </div>

          </div>
          
    </ModalPanel>
  );
};

export default ProductDetailModal;
