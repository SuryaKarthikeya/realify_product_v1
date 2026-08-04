import React from 'react';

const BillingTab = ({ onOpenPayment }) => {
  const invoices = [
    { date: 'May 1, 2026', amount: '$79.00', status: 'Paid', id: '#INV-4592' },
    { date: 'Apr 1, 2026', amount: '$79.00', status: 'Paid', id: '#INV-4410' },
    { date: 'Mar 1, 2026', amount: '$79.00', status: 'Paid', id: '#INV-4287' },
  ];

  return (
    <div className="space-y-6">
      {/* Payment Methods */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 dark:border-slate-800">
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Payment Methods</h3>
        </div>
        <div className="p-6">
          <div className="space-y-3 mb-6">
            <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 shadow-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-8 bg-gray-50 dark:bg-slate-800 rounded flex items-center justify-center border border-gray-100 dark:border-slate-700">
                  <i className="fa-brands fa-cc-visa text-blue-700 dark:text-blue-500 text-xl"></i>
                </div>
                <div>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Visa ending in 4242</p>
                  <p className="text-xs text-gray-500 dark:text-slate-400">Expires 12/2027</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded text-[10px] font-bold border border-green-100 dark:border-green-800">Default</span>
                <button className="text-xs font-bold text-red-500 hover:underline">Remove</button>
              </div>
            </div>
          </div>
          <button 
            onClick={onOpenPayment}
            className="px-4 py-2 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-bold hover:bg-gray-100 transition-all active:scale-95"
          >
            <i className="fa-solid fa-plus mr-2"></i>Add Payment Method
          </button>
        </div>
      </div>

      {/* Payout Setup */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Payout Setup</h3>
          <span className="px-3 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-xl text-[10px] font-bold border border-green-100 dark:border-green-800">
            <i className="fa-solid fa-check-circle mr-1.5"></i>KYC Verified
          </span>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 rounded-2xl">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-white dark:bg-slate-800 rounded-xl flex items-center justify-center border border-gray-100 dark:border-slate-700 shadow-sm">
                <i className="fa-solid fa-building-columns text-gray-600 dark:text-slate-400"></i>
              </div>
              <div>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Chase Bank ****7890</p>
                <p className="text-xs text-gray-500 dark:text-slate-400">Weekly Payouts (Monday)</p>
              </div>
            </div>
            <button className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline">Edit Payouts</button>
          </div>
        </div>
      </div>

      {/* Invoices */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 dark:border-slate-800">
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Invoices</h3>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-bold text-gray-400 dark:text-slate-500 tracking-wider border-b border-gray-100 dark:border-slate-800">
                  <th className="pb-3 px-2">Date</th>
                  <th className="pb-3 px-2">Invoice ID</th>
                  <th className="pb-3 px-2">Amount</th>
                  <th className="pb-3 px-2">Status</th>
                  <th className="pb-3 px-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv, i) => (
                  <tr key={i} className="border-b border-gray-50 dark:border-slate-800/50 last:border-0 hover:bg-gray-50/50 dark:hover:bg-slate-800/20 transition-colors">
                    <td className="py-4 px-2 text-gray-700 dark:text-slate-300 font-medium">{inv.date}</td>
                    <td className="py-4 px-2 text-gray-500 dark:text-slate-500 font-sans text-xs">{inv.id}</td>
                    <td className="py-4 px-2 font-bold text-gray-900 dark:text-slate-100">{inv.amount}</td>
                    <td className="py-4 px-2">
                      <span className="px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded text-[10px] font-bold">Paid</span>
                    </td>
                    <td className="py-4 px-2 text-right">
                      <button className="text-blue-600 dark:text-blue-400 font-bold hover:underline flex items-center gap-1.5 ml-auto">
                        <i className="fa-solid fa-download"></i>PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BillingTab;
