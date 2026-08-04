import { downloadFile } from '@/utils/downloadFile';

/**
 * Builds and downloads the Profit & Ads report.
 *
 * The CSV body is still a fixture — swap `buildReportCsv` for the real request
 * when the endpoint exists; the calling components will not need to change.
 */
const REPORT_CSV =
  'SKU,ACOS,BREAK_EVEN,CMAA,RECOVERABLE\n' +
  'SKU-B0BHSZQG3P,41%,17%,340508,158192\n' +
  'SKU-B0DF1ALTZ,38%,16%,155000,58881';

const buildReportCsv = async (_filters = {}) => {
  // Simulated latency so the calling UI exercises its loading state.
  await new Promise((resolve) => setTimeout(resolve, 1500));
  return REPORT_CSV;
};

export const downloadProfitAdsReport = async (filters = {}) => {
  const csv = await buildReportCsv(filters);
  downloadFile(csv, `profit_ads_export_${new Date().getTime()}.csv`, 'text/csv;charset=utf-8;');
  return true;
};
