import { useEffect } from 'react';

/**
 * Custom hook to handle OAuth redirect parameters globally.
 * This separates business logic from the UI (App.jsx).
 */
export const useOAuth = () => {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const shop = urlParams.get('shop');
    const status = urlParams.get('status');
    
    if (shop && status === 'connected') {
      const platform = urlParams.get('platform') || 'shopify';
      
      // Store connection data
      localStorage.setItem('active_shop', shop);
      localStorage.setItem('active_platform', platform);
      
      // Backward compatibility (if needed)
      localStorage.setItem('shopify_shop', shop);
      localStorage.setItem('shopify_status', 'connected');
      
      // Clean up the URL to prevent re-triggering logic on refresh
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, []);
};
