import React from 'react';
import DataTable from '@/components/data-display/DataTable';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { bleedingMarginData } from '@/features/workspace/domains/margin/data/marginData';
import { formatCurrency, formatPercentage } from '@/utils/formatters';

const BleedingMarginTable = ({ onRowClick, hideTitleBar }) => {
  const columns = [
    { header: 'SKU', key: 'sku', render: (val) => <span className="font-sans text-xs text-gray-500 dark:text-slate-400">{val}</span> },
    { header: 'Product', key: 'title', bold: true },
    { header: 'CM2', key: 'cm2', align: 'right', render: (val) => (
      <span className="text-xs text-gray-700 dark:text-slate-300">{formatCurrency(val)}</span>
    )},
    { header: 'CM%', key: 'cmpct', align: 'right', render: (val) => (
      <span className={val < 0 ? 'text-red-500' : ''}>{formatPercentage(val)}</span>
    )},
    { header: '$ at Risk', key: 'risk', align: 'right', render: (val) => (
      <span className="text-xs text-gray-700 dark:text-slate-300">{formatCurrency(val)}</span>
    )},
    { header: 'BB%', key: 'bb', align: 'center', render: (val) => (
      <Badge variant={val < 0.5 ? 'danger' : 'default'}>
        {formatPercentage(val, 0)}
      </Badge>
    )},
    { header: 'Action', key: 'action', align: 'center', render: (val) => (
      <Button variant={val === 'Reprice' ? 'primary' : 'secondary'} size="sm" className="!py-1 !px-2 !text-[10px]">
        {val}
      </Button>
    )}
  ];

  return (
    <DataTable
      title={hideTitleBar ? null : 'Bleeding Margin SKUs'}
      subtitle={hideTitleBar ? null : 'Sorted by $ at risk descending'}
      columns={columns}
      data={bleedingMarginData}
      onRowClick={onRowClick}
    />
  );
};

export default BleedingMarginTable;
