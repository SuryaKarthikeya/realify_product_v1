import React, { useEffect, useState } from 'react';
import { MODAL_MOCK_DATA } from '@/features/profit-ads/data/profitAdsData';
import { downloadProfitAdsReport } from '@/services/exportService';
import ModalPanel from '@/components/overlays/ModalPanel';

const recommendationsData = [
  {
    id: 1,
    campaignLabel: 'Campaign 1 of 4',
    title: 'Generic keyword ads',
    breadcrumbs: 'SC | SP | Phrase gen kwt | Bike covers',
    gain: '+$29,276/mo',
    desc: 'Shows your ad on broad searches like "bike cover." Spends 35% of budget at 37% ACOS vs 6% break-even.',
    simulation: {
      defaultBidChange: -15,
      targetAcos: 6,
      projections: [
        { days: '30D', gain: '+$18,240', p: 'p≈.58' },
        { days: '60D', gain: '+$38,920', p: 'p≈.51' },
        { days: '90D', gain: '+$57,600', p: 'p≈.44' }
      ]
    }
  },
  {
    id: 2,
    campaignLabel: 'Campaign 2 of 4',
    title: 'Competitor page ads',
    breadcrumbs: 'SC | SP | Comp ASIN tar | Bike covers BSR 1',
    gain: '+$25,143/mo',
    desc: 'Shows your ad on rival bike-cover pages. Spends 31% of budget at 34% ACOS vs 6% break-even.',
    simulation: {
      defaultBidChange: -18,
      targetAcos: 6,
      projections: [
        { days: '30D', gain: '+$15,860', p: 'p≈.55' },
        { days: '60D', gain: '+$33,410', p: 'p≈.49' },
        { days: '90D', gain: '+$49,920', p: 'p≈.42' }
      ]
    }
  },
  {
    id: 3,
    campaignLabel: 'Campaign 3 of 4',
    title: 'Category placement ads',
    breadcrumbs: 'SC | SP | Category tar | Bike covers BSR 1',
    gain: '+$12,891/mo',
    desc: 'Shows your ad across the two-wheeler category. Spends 17% of budget at 28% ACOS vs 6% break-even.',
    simulation: {
      defaultBidChange: -20,
      targetAcos: 6,
      projections: [
        { days: '30D', gain: '+$29,880', p: 'p≈.61' },
        { days: '60D', gain: '+$64,720', p: 'p≈.53' },
        { days: '90D', gain: '+$99,540', p: 'p≈.47' }
      ]
    }
  },
  {
    id: 4,
    campaignLabel: 'Campaign 4 of 4',
    title: 'Auto targeting ads',
    breadcrumbs: 'SC | SP | Auto | Bike covers',
    gain: '+$10,500/mo',
    desc: 'Shows your ad automatically based on keywords and products related to yours. Spends 15% of budget at 30% ACOS vs 6% break-even.',
    simulation: {
      defaultBidChange: -12,
      targetAcos: 6,
      projections: [
        { days: '30D', gain: '+$8,400', p: 'p≈.59' },
        { days: '60D', gain: '+$17,200', p: 'p≈.54' },
        { days: '90D', gain: '+$25,800', p: 'p≈.48' }
      ]
    }
  }
];

const ProfitAdsModal = ({ isOpen, onClose, skuData }) => {
  const [activeRecId, setActiveRecId] = useState(3);
  const [bidChange, setBidChange] = useState(-20);
  const [activeSection, setActiveSection] = useState(null); // 'preview', 'why', or null
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    const activeRec = recommendationsData.find(r => r.id === activeRecId);
    if (activeRec) {
      setBidChange(activeRec.simulation.defaultBidChange);
    }
  }, [activeRecId]);

  if (!isOpen || !skuData) return null;

  const _data = MODAL_MOCK_DATA;
  const activeRec = recommendationsData.find(r => r.id === activeRecId);

  // ACOS colors
  const isAcosHigh = skuData.acos > skuData.be;
  const acosColor = isAcosHigh ? 'text-red-600 dark:text-red-500' : 'text-emerald-600 dark:text-emerald-500';

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await downloadProfitAdsReport({ sku: skuData.sku });
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const modalFooter = (
    <div className="flex items-center justify-between w-full">
      <div>
        <p className="text-[15px] text-gray-700 dark:text-slate-300">
          Projected if all applied · <span className="text-gray-900 dark:text-white">net CMAA gain</span> <span className="font-bold text-emerald-600 dark:text-emerald-500">+$67,309/mo</span>
        </p>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={handleExport}
          disabled={isExporting}
          className="px-4 py-2 border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-800 dark:text-slate-200 text-sm font-bold rounded-lg transition-colors disabled:opacity-70 flex items-center gap-2 shadow-sm"
        >
          {isExporting && <i className="fa-solid fa-spinner fa-spin"></i>}
          Export
        </button>
        <button className="px-5 py-2 bg-[#0052ff] hover:bg-blue-700 text-white text-sm font-bold rounded-lg transition-colors shadow-sm">
          Apply all 3 changes
        </button>
      </div>
    </div>
  );

  return (
    <ModalPanel isOpen={isOpen} onClose={onClose} maxWidth="max-w-[1050px]" footer={modalFooter}>
      {/* Header Row */}
      <div className="flex items-start justify-between mb-6">
        <div className="pr-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-slate-100 tracking-tight mb-1">
            {skuData.title}
          </h2>
          <p className="text-[10px] text-gray-500 dark:text-slate-400 font-sans tracking-wide">
            {skuData.sku} · {recommendationsData.length} campaign{recommendationsData.length !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="flex items-center gap-4 shrink-0 mt-1">
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition-colors"
          >
            <i className="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-5 mb-6">
        <div>
          <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1">ACOS VS BREAK-EVEN</p>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-bold tracking-tight ${acosColor}`}>{skuData.acos}%</span>
            <span className="text-sm font-medium text-gray-500 dark:text-slate-400">vs {skuData.be}% BE</span>
          </div>
        </div>
        <div>
          <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1">CMAA</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-slate-100 tracking-tight">{skuData.cmaa}</p>
        </div>
        <div>
          <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1">RECOVERABLE</p>
          <p className="text-3xl font-bold text-emerald-500 tracking-tight">{skuData.recoverable}</p>
        </div>
      </div>

      {/* Recommendations */}
      <div className="mb-5">
        <p className="text-[13px] font-bold text-blue-600 dark:text-blue-500 italic mb-4">
          Recommendations — each acts on its own
        </p>

        {/* Horizontal Cards */}
        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
          {recommendationsData.map((rec, index) => {
            const isActive = activeRecId === rec.id;
            return (
              <div
                key={rec.id}
                onClick={() => setActiveRecId(rec.id)}
                className={`shrink-0 w-[300px] border rounded-xl p-5 cursor-pointer transition-colors ${isActive
                    ? 'border-blue-600 bg-white dark:bg-slate-900 shadow-sm'
                    : 'border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-gray-300 dark:hover:border-slate-700'
                  }`}
              >
                <div className="mb-3">
                  <span className={`px-2 py-1 text-[10px] font-bold rounded-full ${isActive
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400'
                    }`}>
                    Campaign {index + 1} of {recommendationsData.length}
                  </span>
                </div>
                <h3 className="text-[15px] font-bold text-gray-900 dark:text-slate-100 mb-1">{rec.title}</h3>
                <p className="text-[10px] text-gray-400 dark:text-slate-500 font-sans mb-2">{rec.breadcrumbs}</p>
                <p className="text-lg font-bold text-emerald-600 dark:text-emerald-500 tracking-tight mb-3">{rec.gain}</p>
                <p className="text-[13px] text-gray-700 dark:text-slate-300 leading-relaxed">
                  {rec.desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* Bottom Split Section */}
        <div className="flex flex-col md:flex-row gap-4 mt-2">

          {/* Simulate Section */}
          <div className="flex-1 border border-gray-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 shadow-sm overflow-hidden p-5">

            <div className="flex items-center justify-between mb-6">
              <p className="text-[10px] font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest flex items-center gap-2">
                SIMULATE — ADJUST AND RE-RUN <span className="text-gray-900 dark:text-slate-100 normal-case font-bold tracking-normal text-[12px] ml-1">· {activeRec?.title}</span>
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActiveSection(activeSection === 'why' ? null : 'why')}
                  className="text-blue-600 dark:text-blue-400 text-[13px] font-bold hover:underline"
                >
                  Why
                </button>
                <span className="text-gray-300 dark:text-slate-600">·</span>
                <button
                  onClick={() => window.open('https://sellercentral.amazon.in/', '_blank')}
                  className="text-blue-600 dark:text-blue-400 text-[13px] font-bold hover:underline flex items-center gap-1"
                >
                  Open in Amazon <i className="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                </button>
              </div>
            </div>

            {/* Simulate Controls */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-4 mb-6">
              <div className="flex items-center gap-3">
                <span className="text-[13px] text-gray-600 dark:text-slate-400">Bid change:</span>
                <span className="text-[14px] font-bold text-gray-900 dark:text-slate-100">{bidChange}%</span>
                <div className="w-24 h-2 bg-gray-200 dark:bg-slate-700 rounded-full relative mx-1">
                  <input
                    type="range"
                    min="-100"
                    max="0"
                    value={bidChange}
                    onChange={(e) => setBidChange(Number(e.target.value))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  />
                  <div className="absolute top-0 left-0 h-full bg-[#0052ff] rounded-full" style={{ width: `${100 + bidChange}%` }}></div>
                  <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border border-gray-200 shadow-sm pointer-events-none" style={{ left: `${100 + bidChange}%`, transform: 'translate(-50%, -50%)' }}></div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[13px] text-gray-600 dark:text-slate-400">Target ACOS:</span>
                <div className="flex items-center border border-gray-200 dark:border-slate-700 rounded-md px-2 py-1">
                  <input key={activeRec?.id} type="text" defaultValue={activeRec?.simulation.targetAcos} className="w-6 text-center text-[13px] font-bold text-gray-900 dark:text-slate-100 bg-transparent focus:outline-none" />
                  <span className="text-[13px] text-gray-900 font-bold">%</span>
                </div>
              </div>

              <button className="px-4 py-1.5 bg-[#0052ff] hover:bg-blue-700 text-white text-[13px] font-bold rounded-md transition-colors">
                Re-simulate
              </button>
            </div>

            {/* Projections */}
            <div className="grid grid-cols-3 gap-3 mb-5">
              {activeRec?.simulation.projections.map((proj, idx) => (
                <div key={idx} className="border border-gray-100 dark:border-slate-800 rounded-lg p-3 text-center">
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 mb-1 tracking-wider">{proj.days}</p>
                  <p className="text-[15px] font-bold text-emerald-600 dark:text-emerald-500 mb-0.5">{proj.gain}</p>
                  <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500">{proj.p}</p>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 mb-4">
              <button className="flex-1 py-2.5 bg-[#0052ff] hover:bg-blue-700 text-white text-[14px] font-bold rounded-lg transition-colors">
                Apply change
              </button>
              <button
                onClick={() => setActiveSection(activeSection === 'preview' ? null : 'preview')}
                className={`flex-1 py-2.5 border rounded-lg text-[14px] font-bold transition-colors ${activeSection === 'preview' ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-white border-gray-200 text-gray-900 hover:bg-gray-50'}`}
              >
                Preview
              </button>
            </div>

            <div className="flex items-center gap-1.5 text-[#d93025]">
              <i className="fa-solid fa-triangle-exclamation text-[11px]"></i>
              <span className="text-[11px] font-medium tracking-wide">Tripwire: units/wk drop {'>'}15% → auto-revert.</span>
            </div>

            {/* Toggled Sections (Preview / Why) */}
            {activeSection === 'preview' && (
              <div className="mt-5 border-l-4 border-blue-600 border-y border-r border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800/30 rounded-xl p-5 shadow-sm">
                <p className="text-[14px] font-bold text-gray-900 dark:text-slate-100 mb-2">
                  Preview: instruction only
                </p>
                <p className="text-[13px] text-gray-700 dark:text-slate-300 mb-3 font-sans">
                  update bid: {bidChange}% on {activeRec?.title}
                </p>
              </div>
            )}

            {activeSection === 'why' && (
              <div className="mt-5 border-l-4 border-blue-600 border-y border-r border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800/30 rounded-xl p-5 shadow-sm">
                <p className="text-[13px] text-gray-700 dark:text-slate-300 leading-relaxed">
                  <span className="font-bold text-gray-900 dark:text-slate-100">Why:</span> Break-even ACOS is <span className="font-bold">{skuData.be}%</span> (contribution ÷ net settled revenue, from your COGS). This SKU runs at <span className="font-bold">{skuData.acos}%</span>.
                </p>
              </div>
            )}

          </div>

          {/* Advisory Section */}
          <div className="w-full md:w-[300px] border border-gray-200 dark:border-slate-800 rounded-xl bg-[#fcfbf9] dark:bg-slate-900/50 p-5 shrink-0">
            <p className="text-[13px] font-bold text-gray-900 dark:text-white italic mb-3">
              Advisory — you do this yourself
            </p>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[13px] font-bold text-gray-900 dark:text-slate-100">campaign split</span>
              <span className="bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-slate-300 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded">ADVISORY</span>
            </div>
            <p className="text-[13px] text-gray-700 dark:text-slate-300 leading-relaxed mb-4">
              This SKU's spend is spread across several campaigns — a dedicated campaign would let its bids/budget be tuned without side effects. Realify won't auto-execute.
            </p>
            <button className="text-[12px] font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
              How to <i className="fa-solid fa-caret-down"></i>
            </button>
          </div>

        </div>
      </div>

    </ModalPanel>
  );
};

export default ProfitAdsModal;
