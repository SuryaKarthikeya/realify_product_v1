/** Option lists and calendar labels used by the header's filter popover. */
import { V2_CAT_OPTS } from '@/constants/filterOptions';

export const CHANNEL_OPTS = [
  ['all', 'All Channels'],
  ['amazon', 'Amazon'],
  ['shopify', 'Shopify'],
  ['tiktok-shop', 'TikTok Shop'],
];
export const CATEGORY_OPTS = V2_CAT_OPTS;
export const QUICK_DATE_OPTS = [
  { label: 'Last 7 Days', value: 'last-7-days' },
  { label: 'Last 30 Days', value: 'last-30-days' },
  { label: 'Last 90 Days', value: 'last-90-days' },
];
