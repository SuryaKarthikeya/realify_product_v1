import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import { useExplainStore } from '@/store/useExplainStore';
import { useIntegrationsStore } from '@/store/useIntegrationsStore';

const ProfileDrawer = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { explainMode, setExplainMode } = useExplainStore();
  const resetCompletedSetups = useIntegrationsStore((s) => s.resetCompletedSetups);
  const [deleteMode, setDeleteMode] = useState(false);
  const [wipeMode, setWipeMode] = useState(false);
  
  const [password, setPassword] = useState('');
  const [confirmText, setConfirmText] = useState('');

  const userName = user?.name || localStorage.getItem('user_name') || 'Rohit';

  const handleSignOut = () => {
    logout();
    onClose();
    navigate('/');
  };

  const fileInputRef = useRef(null);

  const handleUploadCogsClick = () => {
    fileInputRef.current?.click();
  };

  const handleGoToOnboarding = () => {
    onClose();
    navigate('/onboarding?step=5&fromIntel=true');
  };

  /**
   * Wipe this account's data and land back at the start of onboarding.
   *
   * Unlike "Delete account" below, the account itself survives — this clears the
   * stored data and sends the user back to step 1 to seed it again from demo or
   * uploaded ASINs, so it deliberately does not log out.
   */
  const handleWipeAndReonboard = () => {
    localStorage.clear();
    /* Clearing the key is not enough — the store already holds the parsed copy in
       memory, and this navigates rather than reloads, so integrations would still
       report "Setup Completed" over an empty localStorage. */
    resetCompletedSetups();
    setWipeMode(false);
    onClose();
    navigate('/');
  };

  const handleDataWipe = () => {
    if (confirmText.toLowerCase() === 'delete') {
      localStorage.clear();
      logout();
      onClose();
      navigate('/');
    }
  };

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 dark:bg-black/40 z-[60]"
          onClick={onClose}
        />
      )}

      <div
        className={`fixed right-0 top-0 h-screen w-full sm:w-[420px] bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800 shadow-2xl z-[70] flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header Section */}
        <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <h2 className="text-[18px] font-bold text-gray-900 dark:text-white font-sans">
              Account & data
            </h2>
            <button
              onClick={onClose}
              className="w-7 h-7 flex items-center justify-center text-gray-500 hover:text-gray-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
            >
              <i className="fa-solid fa-xmark text-[14px]" />
            </button>
          </div>
        </div>

        {/* Content Section */}
        <div className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4 bg-gray-50/50 dark:bg-slate-900/50">
          
          {/* User Info */}
          <div className="flex flex-col items-start mb-2 mt-1">
            <p className="text-[14px] text-gray-600 dark:text-slate-300 mb-2.5">
              Signed in to <span className="font-bold text-gray-900 dark:text-white">{userName}</span>
            </p>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 text-[10px] font-bold tracking-wider">
              CUSTOMER <span className="text-emerald-300 dark:text-emerald-700">•</span> LIVE DATA
            </div>
          </div>
          
          {/* Explanation Mode Card */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-slate-700">
            <h3 className="text-base font-bold text-gray-900 dark:text-white mb-2 font-sans">Explanation mode</h3>
            <p className="text-[13px] text-gray-600 dark:text-slate-300 leading-relaxed mb-4">
              When on, every card you open shows a full provenance trace — inputs by source, the rule and its formula, the anomaly, the calculation, and the exact data sent to (and returned from) the LLM. Off by default.
            </p>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setExplainMode(!explainMode)}
                className={`relative w-10 h-5 rounded-full transition-colors ${explainMode ? 'bg-blue-600' : 'bg-gray-200 dark:bg-slate-600'}`}
              >
                <div className={`absolute top-0.5 left-0.5 bg-white w-4 h-4 rounded-full transition-transform ${explainMode ? 'translate-x-5' : 'translate-x-0'}`} />
              </button>
              <span className="text-[13px] font-medium text-gray-600 dark:text-slate-400">Show explainability on every card</span>
            </div>
          </div>

          {/* New: Data Completeness */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-slate-700">
            <h3 className="text-base font-bold text-gray-900 dark:text-white mb-2 font-sans">Data completeness</h3>
            <p className="text-[13px] text-gray-600 dark:text-slate-300 leading-relaxed mb-4">
              Detectors light up as you upload the reports that feed them. Anything missing stays dark — nothing is ever synthesized for your account.
            </p>
            <p className="text-[12px] font-sans text-gray-500 mb-4 tracking-tight">
              6/10 detector groups active · 1447 SKUs
            </p>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-check text-green-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Price</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">1424 SKUs</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-check text-green-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">COGS</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">1388 SKUs</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-check text-green-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Margin</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">1 SKUs</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-check text-green-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Buy Box %</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">1273 SKUs</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-check text-green-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Sales velocity</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">395 SKUs</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-regular fa-circle text-gray-300 dark:text-gray-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Inventory & cover</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">add: Inventory report</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-solid fa-check text-green-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Return rate</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">395 SKUs</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-regular fa-circle text-gray-300 dark:text-gray-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Ad efficiency (TACoS)</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">add: Ads / Sales report</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-slate-700/50">
                <div className="flex items-center gap-2">
                  <i className="fa-regular fa-circle text-gray-300 dark:text-gray-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Rating & reviews</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">add: Listings export</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <div className="flex items-center gap-2">
                  <i className="fa-regular fa-circle text-gray-300 dark:text-gray-600 text-xs w-3" />
                  <span className="text-[13px] text-gray-800 dark:text-slate-200">Conversion</span>
                </div>
                <span className="text-[11px] font-sans text-gray-400">add: Sales & Traffic</span>
              </div>
            </div>
          </div>

          {/* New: Your reports & COGS */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-slate-700">
            <h3 className="text-base font-bold text-gray-900 dark:text-white mb-2 font-sans">Your reports & COGS</h3>
            <p className="text-[13px] text-gray-600 dark:text-slate-300 leading-relaxed mb-5">
              Add or replace reports anytime — each is processed and persisted as it comes in. Re-upload a report of the same type to replace it; update COGS to refresh margins.
            </p>
            
            <div className="flex flex-col gap-4">
              <button 
                onClick={handleGoToOnboarding}
                className="w-fit px-4 py-2 bg-white border border-gray-200 dark:bg-slate-900 dark:border-slate-700 rounded-lg text-[13px] font-bold text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors shadow-sm"
              >
                Add / replace channel reports
              </button>
              
              <div className="flex items-center justify-between flex-wrap gap-3">
                <button className="text-[12.5px] text-blue-600 hover:text-blue-700 underline font-medium">
                  Download COGS template
                </button>
                <button 
                  onClick={handleUploadCogsClick}
                  className="w-fit px-4 py-2 bg-white border border-gray-200 dark:bg-slate-900 dark:border-slate-700 rounded-lg text-[13px] font-bold text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors shadow-sm"
                >
                  Upload / update COGS
                </button>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  className="hidden" 
                  accept=".csv,.xlsx,.xls"
                />
              </div>
            </div>
          </div>


          {/* Wipe data & re-onboard Card */}
          <div className="bg-[#FAF7F7] dark:bg-red-900/10 rounded-2xl p-5 shadow-sm border border-red-200 dark:border-red-900/50">
            <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1.5 font-sans">
              Wipe data &amp; re-onboard
            </h3>
            <p className="text-[13px] text-gray-600 dark:text-slate-300 mb-4 leading-relaxed">
              Permanently delete all of this account&apos;s data (SKUs, orders, insights, settings)
              and return to the onboarding screen to start over with demo or uploaded ASINs.
            </p>

            {/* Two-step, because the wipe cannot be undone and the button sits one
                stray click away from the Log out button below it. */}
            {!wipeMode ? (
              <button
                onClick={() => setWipeMode(true)}
                className="px-4 py-2 rounded-xl bg-[#A43B2A] text-white text-[13px] font-bold hover:bg-[#8A3022] transition-colors"
              >
                Wipe all data &amp; re-onboard
              </button>
            ) : (
              <div className="space-y-3">
                <p className="text-[12.5px] font-bold text-[#A43B2A] dark:text-red-400">
                  This deletes everything and cannot be undone. Continue?
                </p>
                <div className="flex items-center gap-2.5">
                  <button
                    onClick={handleWipeAndReonboard}
                    className="px-4 py-2 rounded-xl bg-[#A43B2A] text-white text-[13px] font-bold hover:bg-[#8A3022] transition-colors"
                  >
                    Yes, wipe &amp; re-onboard
                  </button>
                  <button
                    onClick={() => setWipeMode(false)}
                    className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-600 text-[13px] font-bold text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sign out Card */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-slate-700">
            <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1.5 font-sans">Sign out</h3>
            <p className="text-[13px] text-gray-600 dark:text-slate-300 mb-4">
              Log out of this account. Your data is kept.
            </p>
            <button 
              onClick={handleSignOut}
              className="px-4 py-1.5 rounded-xl border border-gray-200 dark:border-slate-600 text-[13px] font-bold text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              Log out
            </button>
          </div>

          {/* Danger Zone Card */}
          <div className="bg-[#FAF7F7] dark:bg-red-900/10 rounded-2xl p-5 shadow-sm border border-red-200 dark:border-red-900/50">
            <h3 className="text-base font-bold text-[#A43B2A] dark:text-red-400 mb-1.5 font-sans">Danger zone</h3>
            <p className="text-[13px] text-gray-600 dark:text-slate-300 mb-4">
              Permanently deletes your account, organization, and all its data. Your email is freed for reuse. This cannot be undone.
            </p>
            
            {!deleteMode ? (
              <button 
                onClick={() => setDeleteMode(true)}
                className="px-4 py-2 rounded-xl bg-[#A43B2A] text-white text-[13px] font-bold hover:bg-[#8A3022] transition-colors"
              >
                Delete account
              </button>
            ) : (
              <div className="flex flex-col gap-3">
                <input 
                  type="password"
                  placeholder="Your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-[13px] focus:outline-none focus:ring-2 focus:ring-red-500/20"
                />
                <input 
                  type="text"
                  placeholder='Type "delete" to confirm'
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-[13px] focus:outline-none focus:ring-2 focus:ring-red-500/20"
                />
                <div className="flex items-center gap-2 mt-1">
                  <button 
                    onClick={handleDataWipe}
                    disabled={confirmText.toLowerCase() !== 'delete'}
                    className="px-4 py-2 rounded-xl bg-[#A43B2A] text-white text-[13px] font-bold hover:bg-[#8A3022] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Permanently delete
                  </button>
                  <button 
                    onClick={() => {
                      setDeleteMode(false);
                      setPassword('');
                      setConfirmText('');
                    }}
                    className="px-4 py-2 rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-900 dark:text-white text-[13px] font-bold hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </>
  );
};

export default ProfileDrawer;
