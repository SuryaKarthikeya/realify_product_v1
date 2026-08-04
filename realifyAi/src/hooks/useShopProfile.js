import { useState, useEffect, useRef } from 'react';
import { getShopProfile } from '@/services/shopService';
import { storage } from '@/utils/storage';

/**
 * Loads the active shop's profile once per mount.
 *
 * The ref guard is deliberate: it survives React StrictMode's double-invoked
 * effects in development so the request fires exactly once.
 */
export const useShopProfile = () => {
  const [shopProfile, setShopProfile] = useState(null);
  const fetchedRef = useRef(false);

  useEffect(() => {
    // Back-compat: older builds stored the shop under a Shopify-specific key.
    if (!storage.getActiveShop() && storage.getShopifyShop()) {
      storage.setActiveShop(storage.getShopifyShop());
      storage.setActivePlatform('shopify');
    }

    if (fetchedRef.current) return;
    fetchedRef.current = true;

    getShopProfile()
      .then((data) => { if (data) setShopProfile(data); })
      .catch((err) => console.error('Failed to fetch shop profile:', err));
  }, []);

  return shopProfile;
};
