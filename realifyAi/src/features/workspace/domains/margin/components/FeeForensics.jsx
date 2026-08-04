import React from 'react';

const FeeForensics = ({ data }) => {
  const fees = data || [
    { label: 'FBA Fees', value: '$14,200', change: '+$340', isAlert: true },
    { label: 'Selling Fees', value: '$7,800', change: 'flat', isAlert: false },
    { label: 'Storage', value: '$1,640', change: '+$120', isAlert: true },
    { label: 'Returns', value: '$720', change: '+$80', isAlert: true },
  ];

  const totalFees = '$24,360';
  const feePct = '19% of revenue';

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Fee Forensics · last 30d</h3>
        <button className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline">View Detail</button>
      </div>
      
      <div className="space-y-3">
        {fees.map((fee, idx) => (
          <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-800 transition-all hover:border-gray-200 dark:hover:border-slate-700">
            <span className="text-sm font-medium text-gray-700 dark:text-slate-300">{fee.label}</span>
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-900 dark:text-slate-100 font-sans">{fee.value}</span>
              <span className={`px-2 py-0.5 rounded-lg text-[10px] font-bold flex items-center gap-1 ${
                fee.isAlert 
                  ? 'bg-amber-100 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400' 
                  : 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'
              }`}>
                {fee.change}
                {fee.isAlert && <i className="fa-solid fa-triangle-exclamation"></i>}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="pt-4 mt-4 border-t border-gray-100 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-gray-900 dark:text-slate-100">Total Fees</span>
          <div className="text-right">
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100 font-sans">{totalFees}</p>
            <p className="text-[10px] text-gray-500 dark:text-slate-400">{feePct}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeeForensics;
