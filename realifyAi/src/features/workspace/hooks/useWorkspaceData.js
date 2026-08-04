import { useState, useEffect, useRef } from 'react';
import { fetchSalesIntelligence } from '@/services/workspaceService';

/**
 * Kicks off the Workspace data fetch once per mount and reports when the
 * page may stop showing skeletons.
 *
 * `loading` clears whether the request succeeds, fails, or is skipped because
 * no shop is connected — the page always renders its local datasets.
 */
export const useWorkspaceData = () => {
  const [loading, setLoading] = useState(true);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;

    fetchSalesIntelligence()
      .catch((error) => console.error('Failed to fetch intelligence data:', error))
      .finally(() => setLoading(false));
  }, []);

  return { loading };
};
