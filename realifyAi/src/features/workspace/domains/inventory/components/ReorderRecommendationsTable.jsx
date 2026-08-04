import React from 'react';
import DataTable from '@/components/data-display/DataTable';

const ReorderRecommendationsTable = ({ onRowClick }) => {
  const columns = [
    { header: 'SKU', key: 'sku', render: (val) => <span className="font-sans text-xs text-gray-500 dark:text-slate-400">{val}</span> },
    { header: 'Title', key: 'title', bold: true },
    { header: 'DOC', key: 'doc', align: 'right', render: (val) => (
      <span className={`font-bold ${parseInt(val) < 14 ? 'text-red-500' : 'text-amber-500'}`}>{val}</span>
    )},
    { header: 'On-Hand', key: 'onhand', align: 'right' },
    { header: 'Velocity 30d', key: 'vel', align: 'right' },
    { header: 'OOS Risk', key: 'risk', align: 'right', render: (val) => (
      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${parseFloat(val) > 60 ? 'bg-red-50 dark:bg-red-900/20 text-red-600' : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600'}`}>
        {val}
      </span>
    )},
    { header: 'Rec. PO Qty', key: 'qty', align: 'right', render: (val) => (
      <span className="font-sans font-bold text-blue-600">{val}</span>
    )},
    { header: 'Action', key: 'action', align: 'center', render: (val) => (
      <span className={`px-2 py-1 rounded-lg text-[10px] font-bold ${val === 'Reorder' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'bg-gray-100 dark:bg-slate-800 text-gray-600'}`}>
        {val}
      </span>
    )}
  ];

  const data = [
    { sku: 'WH-PRO-2024', title: 'Wireless Headphones', doc: '5d', onhand: '30', vel: '6.1/day', risk: '92%', qty: '240', action: 'Reorder' },
    { sku: 'BT-SPK-99', title: 'Bluetooth Speaker', doc: '8d', onhand: '34', vel: '4.3/day', risk: '78%', qty: '180', action: 'Reorder' },
    { sku: 'FIT-BND-3', title: 'Resistance Band Kit', doc: '12d', onhand: '48', vel: '3.8/day', risk: '64%', qty: '150', action: 'Reorder' },
    { sku: 'CB-DLX-001', title: 'Bamboo Cutting Board', doc: '22d', onhand: '110', vel: '5.2/day', risk: '42%', qty: '120', action: 'Monitor' },
    { sku: 'LED-DK-7', title: 'LED Desk Lamp', doc: '45d', onhand: '171', vel: '3.8/day', risk: '18%', qty: '—', action: 'Healthy' },
  ];

  return (
    <DataTable 
      title="Reorder Recommendations" 
      subtitle="Sorted by OOS risk descending"
      columns={columns}
      data={data}
      onRowClick={onRowClick}
    />
  );
};

export default ReorderRecommendationsTable;
