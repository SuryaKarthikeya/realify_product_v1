import React from 'react';
import DataTable from '@/components/data-display/DataTable';
import { cashFlowByPeriodData } from '@/features/workspace/domains/cash/data/cashData';

const CashFlowTable = () => {
  const columns = [
    { header: 'Period', key: 'period', bold: true },
    { header: 'Channel', key: 'channel', render: (val) => (
      <span className="text-xs text-gray-700 dark:text-slate-300 font-medium">{val}</span>
    )},
    { header: 'Revenue', key: 'revenue', align: 'right', bold: true },
    { header: 'Selling Fees', key: 'selling', align: 'right', render: (val) => <span className="text-gray-700 dark:text-slate-300 font-medium">{val}</span> },
    { header: 'FBA Fees', key: 'fba', align: 'right', render: (val) => <span className={val === '—' ? 'text-gray-400' : 'text-gray-700 dark:text-slate-300 font-medium'}>{val}</span> },
    { header: 'Ad Spend', key: 'ads', align: 'right', render: (val) => <span className="text-gray-700 dark:text-slate-300 font-medium">{val}</span> },
    { header: 'Net Deposit', key: 'net', align: 'right', render: (val) => <span className="font-bold text-gray-900 dark:text-slate-100">{val}</span> },
    { header: 'Deposit Date', key: 'date', align: 'right' },
    { header: 'Days to Deposit', key: 'days', align: 'right', render: (val) => <span className="text-gray-500 font-medium">{val}</span> }
  ];

  return (
    <DataTable 
      title="Cash Flow by Period" 
      subtitle="Weekly breakdown across all sales channels"
      columns={columns}
      data={cashFlowByPeriodData}
    />
  );
};

export default CashFlowTable;
