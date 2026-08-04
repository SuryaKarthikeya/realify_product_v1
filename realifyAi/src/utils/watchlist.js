import { salesWatchlistItems } from '@/data/watchlistData';

/** Looks up a watchlist entry by product name; null when there is no match. */
export const findWatchlistItem = (name) =>
  salesWatchlistItems.find((w) => w.title?.toLowerCase() === name?.toLowerCase()) || null;
