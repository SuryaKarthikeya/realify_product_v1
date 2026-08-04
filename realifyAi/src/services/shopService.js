import httpClient from '@/services/httpClient';
import { storage } from '@/utils/storage';

/**
 * Fetches the connected shop's profile.
 * Returns null when no shop is connected, so callers don't have to re-check.
 */
export const getShopProfile = async () => {
  const shop = storage.getActiveShop();
  if (!shop) return null;
  const platform = storage.getActivePlatform();
  const res = await httpClient.get(`/${platform}/shop-profile`);
  return res.data;
};
