import React from 'react';
import DistributionBarChart from '@/components/data-display/charts/DistributionBarChart';

const data = [
  { name: '< 14d', count: 8 },
  { name: '14-60d', count: 24 },
  { name: '60-180d', count: 22 },
  { name: '> 180d', count: 16 },
];

const DOCDistributionChart = () => (
  <DistributionBarChart
    title="DOC Distribution"
    subtitle="SKU count by days of cover bucket"
    data={data}
    height="h-[260px]"
    toggleOptions={['By SKU', 'By $ Value']}
  />
);

export default DOCDistributionChart;
