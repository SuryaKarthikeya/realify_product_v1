import { useState, useRef, useCallback, useEffect } from 'react';
import { useOnboardingStore } from '@/features/onboarding/store/useOnboardingStore';
import { useCsvUpload } from '@/features/onboarding/hooks/useCsvUpload';
import { getIngestCatalog, downloadCogsTemplate } from '@/services/onboardingService';

/** Shopify report types are the manifest's own ids (SHOP_*); everything else is Amazon. */
const isShopifyType = (type) => type.startsWith('SHOP_');

/**
 * ESSENTIAL is a hard requirement, SUPPORTING is optional enrichment — so they
 * get different weights rather than the same purple.
 */
const TAG_STYLES = {
  ESSENTIAL: 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200/70',
  SUPPORTING: 'bg-gray-100 text-gray-500 ring-1 ring-inset ring-gray-200',
};

const ReportTag = ({ tag }) => (
  <span className={`text-[9px] font-bold uppercase tracking-wider rounded-full px-1.5 py-0.5 whitespace-nowrap ${TAG_STYLES[tag] || TAG_STYLES.SUPPORTING}`}>
    {tag}
  </span>
);

/** One guided-setup question: a label plus a row of selectable pills. */
const WizardQuestion = ({ label, hint, options, selected, onSelect }) => {
  const isSelected = (opt) => (Array.isArray(selected) ? selected.includes(opt) : selected === opt);

  return (
    <div className="mb-5">
      <p className="text-[14.5px] font-bold text-gray-900 mb-3">
        {label}
        {hint && <span className="font-normal text-gray-500"> {hint}</span>}
      </p>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className={`px-4 py-1.5 rounded-lg text-[13.5px] font-medium transition ${isSelected(opt)
              ? 'bg-[#eff4ff] border border-blue-500 text-[#1e40af] font-bold shadow-sm'
              : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
};

function Step5Connect() {
  const { setStep: _setStep } = useOnboardingStore();
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const [showGuidedSetup, setShowGuidedSetup] = useState(false);

  /**
   * Guided-wizard answers. `channels` is multi-select; the rest are single-choice.
   * Which follow-up questions appear depends on the channels picked, so Amazon
   * and Shopify each unlock their own fulfilment question.
   */
  const [wizard, setWizard] = useState({
    channels: [],
    amazonFulfilment: null,
    shopifyShipping: null,
    sharedSkus: null,
    costTracking: null,
    adPlatforms: [],
    firstView: null,
  });
  const [checklistReady, setChecklistReady] = useState(false);

  const toggleChannel = (channel) =>
    setWizard((w) => ({
      ...w,
      channels: w.channels.includes(channel)
        ? w.channels.filter((c) => c !== channel)
        : [...w.channels, channel],
    }));

  const toggleAdPlatform = (platform) =>
    setWizard((w) => ({
      ...w,
      adPlatforms: w.adPlatforms.includes(platform)
        ? w.adPlatforms.filter((p) => p !== platform)
        : [...w.adPlatforms, platform],
    }));

  const pick = (field) => (option) =>
    setWizard((w) => ({ ...w, [field]: w[field] === option ? null : option }));

  const sellsAmazon = wizard.channels.includes('Amazon');
  const sellsShopify = wizard.channels.includes('Shopify');
  const [showMarketplaceDropdown, setShowMarketplaceDropdown] = useState(false);
  const [selectedMarketplace, setSelectedMarketplace] = useState("India — amazon.in (₹)");
  const marketplacesList = ["India — amazon.in (₹)", "United States — amazon.com ($)"];
  // The backend's country profiles are keyed by ISO code; the dropdown only
  // ever offers these two markets today.
  const countryCode = selectedMarketplace.startsWith('India') ? 'IN' : 'US';

  const { identify, commit, identifying, committing, error: uploadError } = useCsvUpload();
  const [pendingFiles, setPendingFiles] = useState([]);       // File[] accumulated across drops
  const [identifyResult, setIdentifyResult] = useState(null); // last /api/ingest/identify response
  const [commitResult, setCommitResult] = useState(null);     // /api/onboard/reports response
  const [connectStatus, setConnectStatus] = useState('idle'); // idle | reading | ready
  // Pre-upload checklist: the real report catalog, so the list shows actual
  // report types + "unlocks" copy before a single file is dropped, instead
  // of a blank section. Replaced row-for-row by identifyResult.checklist
  // (which carries real `present` flags) the moment a file is identified.
  const [catalog, setCatalog] = useState({ amazon: [], shopify: [] });

  useEffect(() => {
    getIngestCatalog()
      .then((data) => {
        const reportsFor = (channel) => data.channels?.find((c) => c.channel === channel)?.reports ?? [];
        setCatalog({ amazon: reportsFor('amazon'), shopify: reportsFor('shopify') });
      })
      .catch(() => {
        // The checklist just stays empty until the first identify call —
        // the upload flow itself doesn't depend on this.
      });
  }, []);

  // 'uploaded' means "we have a recognition result", not "every report
  // matched" — identifyResult.ready is what actually gates the commit button.
  const uploadStatus = identifying ? 'uploading' : identifyResult ? 'uploaded' : 'idle';
  const checklist = identifyResult?.checklist
    ?? [...catalog.amazon, ...catalog.shopify].map((c) => ({ ...c, present: false }));
  const amazonChecklist = checklist.filter((c) => !isShopifyType(c.type));
  const shopifyChecklist = checklist.filter((c) => isShopifyType(c.type));
  const filesForType = (type) => (identifyResult?.files ?? []).filter((f) => f.recognized && f.type === type);

  const recognizedFiles = identifyResult?.files?.filter((f) => f.recognized) ?? [];
  const unrecognizedCount = (identifyResult?.files?.length ?? 0) - recognizedFiles.length;
  const recognizedPeriods = [...new Set(recognizedFiles.flatMap((f) => f.periods ?? []))].sort();
  const hasOverlapsOrConflicts = (identifyResult?.overlaps?.length ?? 0) > 0 || (identifyResult?.conflicts?.length ?? 0) > 0;

  const processFiles = useCallback(async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    const allFiles = [...pendingFiles, ...Array.from(fileList)];
    setPendingFiles(allFiles);
    try {
      const result = await identify(allFiles);
      setIdentifyResult(result);
    } catch {
      // uploadError from the hook surfaces the message below.
    }
  }, [pendingFiles, identify]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    processFiles(e.dataTransfer.files);
  };

  const handleConnectClick = async () => {
    if (uploadStatus !== 'uploaded' || !identifyResult?.ready) return;
    const confirmed = window.confirm("Set up this account as a CUSTOMER? Your dashboard is built from these reports — nothing is synthesized.");
    if (!confirmed) return;
    setConnectStatus('reading');
    try {
      const result = await commit(pendingFiles, countryCode);
      setCommitResult(result);
      setConnectStatus('ready');
    } catch {
      // uploadError from the hook surfaces the message below.
      setConnectStatus('idle');
    }
  };

  const handleDownloadCogsTemplate = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await downloadCogsTemplate();
    } catch (err) {
      console.error('Failed to download COGS template:', err);
    }
  };

  return (
  <div className="flex flex-col h-full anim-fade-in relative max-w-3xl mx-auto w-full">

    {/* Guided Wizard & Tabs */}
    <div className="mb-6 text-left">
      <button 
        onClick={() => setShowGuidedSetup(!showGuidedSetup)}
        className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#6b52d6] text-white font-bold rounded-xl hover:bg-[#5a42bc] transition text-[15px] shadow-sm mb-5"
      >
        <i className="fa-solid fa-wand-magic-sparkles text-sm" />
        Set up with a guided wizard
      </button>

      {/* Once the checklist is built the wizard collapses into a confirmation —
          the questions are answered, so the form would just be noise. */}
      {showGuidedSetup && checklistReady && (
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm mb-5 text-left anim-fade-in">
          <div className="rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3.5">
            <p className="text-[14px] leading-relaxed text-emerald-900">
              <i className="fa-solid fa-check text-emerald-600 mr-1.5" />
              Your checklist is ready below — drop your files into the box and each one ticks off.{' '}
              <button
                onClick={() => setChecklistReady(false)}
                className="font-bold underline underline-offset-2 hover:text-emerald-700 transition"
              >
                Change answers
              </button>
            </p>
          </div>
        </div>
      )}

      {showGuidedSetup && !checklistReady && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm mb-5 text-left anim-fade-in">
           <h3 className="text-[17px] font-bold text-gray-900 mb-5">Guided setup</h3>

           <WizardQuestion
             label="Where do you sell today?"
             options={['Amazon', 'Shopify', 'Other website', 'Walmart', 'eBay', 'TikTok Shop']}
             selected={wizard.channels}
             onSelect={toggleChannel}
           />

           {/* Channel-specific follow-ups — each appears only for the channel it
               belongs to, and both show when both channels are selected. */}
           {sellsAmazon && (
             <div className="anim-fade-in">
               <WizardQuestion
                 label="How do you fulfill Amazon orders?"
                 options={['FBA', 'FBM', 'Both']}
                 selected={wizard.amazonFulfilment}
                 onSelect={pick('amazonFulfilment')}
               />
             </div>
           )}

           {sellsShopify && (
             <div className="anim-fade-in">
               <WizardQuestion
                 label="How do your Shopify orders get shipped?"
                 options={['Self', '3PL', 'MCF']}
                 selected={wizard.shopifyShipping}
                 onSelect={pick('shopifyShipping')}
               />
             </div>
           )}

           {/* Only meaningful when the seller is on both channels. */}
           {sellsAmazon && sellsShopify && (
             <div className="anim-fade-in">
               <WizardQuestion
                 label="Do your Amazon and Shopify listings use the same SKUs?"
                 options={['Yes', 'No', 'Not sure']}
                 selected={wizard.sharedSkus}
                 onSelect={pick('sharedSkus')}
               />
             </div>
           )}

           <WizardQuestion
             label="Do you track your product cost per unit?"
             options={['In Shopify', 'Spreadsheet', 'Not yet']}
             selected={wizard.costTracking}
             onSelect={pick('costTracking')}
           />

           <WizardQuestion
             label="Where do you run ads?"
             options={['Amazon Ads', 'Meta', 'Google', 'TikTok', 'Walmart Connect', 'None yet']}
             selected={wizard.adPlatforms}
             onSelect={toggleAdPlatform}
           />

           <WizardQuestion
             label="What do you want to see first?"
             hint="optional"
             options={['Profit after ads', 'Ad efficiency', 'Category intel', 'Everything']}
             selected={wizard.firstView}
             onSelect={pick('firstView')}
           />

           <button
             onClick={() => setChecklistReady(true)}
             disabled={wizard.channels.length === 0}
             className={`w-full py-3 font-bold rounded-xl text-[15px] transition shadow-md ${wizard.channels.length === 0
               ? 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-none'
               : 'bg-[#131d33] text-white hover:bg-[#1a2642]'
               }`}
           >
             Build my checklist
           </button>
        </div>
      )}

      {/* Marketplace Selector */}
      <div className="flex flex-col text-left mb-5">
        <label className="text-[14px] text-gray-600 font-medium mb-1.5">Marketplace</label>
        <div className="relative">
          <button 
            onClick={() => setShowMarketplaceDropdown(!showMarketplaceDropdown)}
            className="w-full flex items-center justify-between bg-white border border-gray-300 text-gray-900 text-[14.5px] rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand focus:border-brand cursor-pointer shadow-sm text-left"
          >
            {selectedMarketplace}
            <i className={`fa-solid fa-chevron-down text-gray-500 text-xs transition-transform ${showMarketplaceDropdown ? 'rotate-180' : ''}`}></i>
          </button>
          
          {showMarketplaceDropdown && (
            <div className="absolute left-0 right-0 top-[calc(100%+4px)] bg-white border border-gray-200 rounded-xl shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] z-50 py-1.5 overflow-hidden">
              {marketplacesList.map(m => (
                <button
                  key={m}
                  onClick={() => { setSelectedMarketplace(m); setShowMarketplaceDropdown(false); }}
                  className="w-full text-left px-4 py-2.5 text-[14.5px] text-gray-900 hover:bg-gray-50 flex items-center transition"
                >
                  {selectedMarketplace === m && <i className="fa-solid fa-check text-blue-600 text-sm w-6"></i>}
                  <span className={selectedMarketplace === m ? 'ml-0 font-bold text-gray-900' : 'ml-6'}>{m}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3">
        <button className="px-5 py-2.5 bg-[#eff4ff] border border-blue-500 text-[#1e40af] rounded-xl text-[14.5px] font-bold shadow-sm transition">
          Amazon
        </button>
        <button className="px-5 py-2.5 border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 rounded-xl text-[14.5px] font-bold shadow-sm transition">
          Shopify
        </button>
        <button className="px-5 py-2.5 border border-gray-200 bg-gray-50 text-gray-400 rounded-xl text-[14.5px] font-bold cursor-not-allowed flex items-center gap-2">
          Walmart <span className="text-[10px] text-amber-600 font-black tracking-widest uppercase">SOON</span>
        </button>
      </div>
    </div>

    {/* Upload drop zone */}
    <div
      className={`flex flex-col items-center justify-center gap-1.5 py-7 border border-dashed rounded-2xl cursor-pointer transition-all mb-5 ${dragging ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300 hover:border-gray-400 bg-gray-50/30'
        }`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <i className="fa-solid fa-arrow-down text-blue-500 mb-2" />
      <p className="text-sm text-gray-600 font-medium">
        Drag & drop your reports here, or <span className="text-blue-600 font-bold hover:underline">choose files</span>
      </p>
      <p className="text-xs text-gray-400">Drop as many as you like — we recognize each one.</p>
      <a href="#" onClick={handleDownloadCogsTemplate} className="text-xs text-blue-500 font-medium hover:underline mt-1">
        Download the COGS template
      </a>
      <input ref={inputRef} type="file" multiple accept=".csv,.xlsx,.xls" className="hidden" onChange={e => processFiles(e.target.files)} />
    </div>

    {uploadError && (
      <div className="mb-6 bg-red-50 text-red-700 text-sm p-4 rounded-xl font-medium border border-red-100">
        {uploadError}
      </div>
    )}

    {/* AMAZON SECTION */}
    <div className="mb-5">
      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
        AMAZON
      </p>
      <div className="flex flex-col">
        {amazonChecklist.map((item) => {
          const matches = filesForType(item.type);
          const tag = item.sku_source || item.is_cogs ? 'ESSENTIAL' : 'SUPPORTING';
          return (
            <div key={item.type} className="flex items-center gap-4 py-3.5 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition px-2 -mx-2 rounded-lg">
              {item.present ? (
                <i className="fa-solid fa-circle-check text-emerald-600 text-lg w-4 h-4 flex items-center justify-center" />
              ) : (
                <span className="w-4 h-4 rounded border border-gray-300 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className={`text-[13px] font-medium truncate ${item.present ? 'text-gray-900 font-bold' : 'text-gray-700'}`}>{item.label}</p>
                  <ReportTag tag={tag} />
                </div>
              </div>
              {item.present && matches.length > 0 ? (
                <p className="text-[11px] text-emerald-600 font-bold text-right w-5/12 leading-tight truncate pl-4">
                  {matches[0].filename}{matches.length > 1 ? ` +${matches.length - 1} more` : ''}
                </p>
              ) : (
                <p className="text-[11px] text-gray-400 text-right w-5/12 leading-tight truncate pl-4">{item.unlocks}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>

    {/* SHOPIFY SECTION */}
    <div className="mb-5">
      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
        SHOPIFY
      </p>
      <div className="flex flex-col">
        {shopifyChecklist.map((item) => {
          const matches = filesForType(item.type);
          const tag = item.sku_source || item.is_cogs ? 'ESSENTIAL' : 'SUPPORTING';
          return (
            <div key={item.type} className="flex items-center gap-4 py-3.5 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition px-2 -mx-2 rounded-lg">
              {item.present ? (
                <i className="fa-solid fa-circle-check text-emerald-600 text-lg w-4 h-4 flex items-center justify-center" />
              ) : (
                <span className="w-4 h-4 rounded border border-gray-300 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className={`text-[13px] font-medium truncate ${item.present ? 'text-gray-900 font-bold' : 'text-gray-700'}`}>{item.label}</p>
                  <ReportTag tag={tag} />
                </div>
              </div>
              {item.present && matches.length > 0 ? (
                <p className="text-[11px] text-emerald-600 font-bold text-right w-5/12 leading-tight truncate pl-4 max-w-[200px]">
                  {matches[0].filename}{matches.length > 1 ? ` +${matches.length - 1} more` : ''}
                </p>
              ) : (
                <p className="text-[11px] text-gray-400 text-right w-5/12 leading-tight pl-4 max-w-[200px]">{item.unlocks}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>

    {/* Footer */}
    <div className="pb-4 pt-5 mt-6 border-t border-gray-200 flex flex-col items-center justify-end w-full">
      
      {uploadStatus === 'uploaded' && connectStatus === 'idle' && (
        <div className="mb-6 flex flex-col gap-3 w-full max-w-lg">
          <div className="bg-emerald-50 text-emerald-800 text-sm p-4 rounded-xl font-medium border border-emerald-100">
            Recognized {recognizedFiles.length} of {identifyResult?.files?.length ?? 0} file(s)
            {recognizedPeriods.length > 0 ? ` · ${recognizedPeriods.join(', ')}` : ''}.
          </div>
          {!identifyResult?.ready && (
            <div className="bg-orange-50 text-orange-800 text-sm p-4 rounded-xl font-medium border border-orange-100">
              We haven't found a catalog/listings file yet — one report must establish your product SKUs before you can connect.
            </div>
          )}
          {unrecognizedCount > 0 && (
            <div className="bg-orange-50 text-orange-800 text-sm p-4 rounded-xl font-medium border border-orange-100">
              {unrecognizedCount} file(s) weren't recognized as a supported report type.
            </div>
          )}
          {hasOverlapsOrConflicts && (
            <div className="bg-orange-50 text-orange-800 text-sm p-4 rounded-xl font-medium border border-orange-100">
              Some uploaded files overlap in coverage — the later file wins where they conflict.
            </div>
          )}
        </div>
      )}

      {connectStatus === 'idle' && (
        <div className="flex items-center justify-end w-full">
          <button
            onClick={handleConnectClick}
            disabled={uploadStatus !== 'uploaded' || !identifyResult?.ready || committing}
            className={`flex items-center justify-center gap-2 px-10 py-3.5 font-bold rounded-xl transition text-[15px] w-full sm:w-auto ${
              uploadStatus !== 'uploaded' || !identifyResult?.ready || committing
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-[#131d33] text-white hover:bg-[#1a2642] shadow-md hover:shadow-lg'
            }`}
          >
            {uploadStatus === 'uploading' && <i className="fa-solid fa-circle-notch fa-spin"></i>}
            Connect my data
          </button>
        </div>
      )}

      {connectStatus === 'reading' && (
        <div className="flex flex-col items-center justify-center w-full max-w-sm ml-auto">
          <button className="w-full flex items-center justify-center gap-2 px-10 py-3 bg-[#131d33] text-blue-500 font-semibold rounded-xl text-xl shadow-md mb-3 cursor-default">
            <i className="fa-solid fa-certificate fa-spin"></i>
          </button>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2 relative overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full absolute left-0 top-0 bottom-0 transition-all duration-[3000ms] ease-in-out" 
              style={{ width: connectStatus === 'reading' ? '95%' : '0%' }}
            ></div>
          </div>
          <p className="text-[13px] text-gray-600 font-mono mt-1">Reading your reports...</p>
        </div>
      )}

      {connectStatus === 'ready' && (
        <div className="flex flex-col items-center justify-center w-full max-w-sm ml-auto">
          <button 
            onClick={() => _setStep(4)}
            className="w-full flex items-center justify-center gap-2 px-10 py-3.5 bg-[#131d33] text-white font-bold rounded-xl text-[15px] shadow-md mb-3 hover:bg-[#1a2642] transition"
          >
            Continue
          </button>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full w-full"></div>
          </div>
          <p className="text-[13px] text-gray-600 font-mono mt-1">Ready — {commitResult?.skus_written ?? 0} SKUs.</p>
        </div>
      )}
    </div>
  </div>
);
}

export default Step5Connect;
