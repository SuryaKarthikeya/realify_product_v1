import React from 'react';
import DistributionBarChart from '@/components/data-display/charts/DistributionBarChart';

const data = [
  { name: '< 0%', count: 12 },
  { name: '0-10%', count: 18 },
  { name: '10-20%', count: 22 },
  { name: '20-30%', count: 26 },
  { name: '30-40%', count: 20 },
  { name: '> 40%', count: 6 },
];

const MarginDistributionChart = () => (
  <DistributionBarChart
    title="Margin Distribution"
    subtitle="SKU count by margin bucket"
    data={data}
    height="h-[280px]"
    toggleOptions={['By SKU', '% of Rev']}
  />
);

export default MarginDistributionChart;
