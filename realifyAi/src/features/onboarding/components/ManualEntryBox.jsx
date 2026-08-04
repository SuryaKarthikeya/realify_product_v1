import React, { useState } from 'react';

const ManualEntryBox = ({ onResult }) => {
  const [activeTab, setActiveTab] = useState('csv'); // 'csv' or 'manual'
  const [asinText, setAsinText] = useState('');

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (!asinText.trim()) return;
    
    // Simulate processing
    const asins = asinText.split(/[,\n]/).map(s => s.trim()).filter(Boolean);
    onResult({
      type: 'manual',
      items: asins,
      timestamp: new Date().toLocaleTimeString()
    });
    setAsinText('');
  };

  const handleCsvUpload = () => {
    // Simulate processing
    onResult({
      type: 'csv',
      fileName: 'products_import.csv',
      count: 24,
      timestamp: new Date().toLocaleTimeString()
    });
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm h-full flex flex-col">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Manual Data Entry</h3>
        <p className="text-sm text-gray-600 dark:text-slate-400">Import data via CSV or manual entry</p>
      </div>

      {/* Tabs */}
      <div className="flex p-1 bg-gray-100 dark:bg-slate-800 rounded-xl mb-6">
        <button 
          onClick={() => setActiveTab('csv')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'csv' 
              ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm' 
              : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'
          }`}
        >
          <i className="fa-solid fa-file-csv"></i> Upload CSV
        </button>
        <button 
          onClick={() => setActiveTab('manual')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'manual' 
              ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm' 
              : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'
          }`}
        >
          <i className="fa-solid fa-keyboard"></i> Manual
        </button>
      </div>

      <div className="flex-1 flex flex-col">
        {activeTab === 'csv' ? (
          <div className="flex-1 border-2 border-dashed border-gray-200 dark:border-slate-700 rounded-2xl flex flex-col items-center justify-center p-6 text-center group hover:border-blue-500 dark:hover:border-blue-400 transition-colors">
            <div className="w-16 h-16 bg-gray-50 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <i className="fa-solid fa-cloud-arrow-up text-2xl text-gray-400 dark:text-slate-500 group-hover:text-gray-700 dark:group-hover:text-gray-300"></i>
            </div>
            <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-1">Upload CSV file</h4>
            <p className="text-xs text-gray-500 dark:text-slate-400 mb-6">Drag and drop your file here, or click to browse</p>
            <button 
              onClick={handleCsvUpload}
              className="px-6 py-2.5 bg-brand hover:bg-brand-hover text-white dark:bg-gray-600 dark:hover:bg-gray-500 text-sm font-semibold rounded-lg transition-all shadow-md shadow-black/10 dark:shadow-gray-700/20"
            >
              Select File
            </button>
          </div>
        ) : (
          <div className="flex-1 flex flex-col">
            <label className="text-sm font-semibold text-gray-700 dark:text-slate-300 mb-2">ASIN / Product IDs</label>
            <textarea 
              value={asinText}
              onChange={(e) => setAsinText(e.target.value)}
              placeholder="Enter ASINs separated by commas or new lines (e.g. B08N5KWB9H, B09G96T278)"
              className="flex-1 w-full p-4 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 dark:text-slate-200 transition-all resize-none mb-4"
            />
            <button 
              onClick={handleManualSubmit}
              disabled={!asinText.trim()}
              className="w-full py-3 bg-brand hover:bg-brand-hover text-white dark:bg-gray-600 dark:hover:bg-gray-500 font-semibold rounded-xl transition-all shadow-md shadow-black/10 dark:shadow-gray-700/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Add Products
            </button>
          </div>
        )}
      </div>

      <div className="mt-6">
        <p className="text-[11px] text-gray-500 dark:text-slate-400 flex items-start gap-2">
          <i className="fa-solid fa-info-circle mt-0.5 text-blue-500"></i>
          Manual entries require validation before they appear in your active inventory.
        </p>
      </div>
    </div>
  );
};

export default ManualEntryBox;
