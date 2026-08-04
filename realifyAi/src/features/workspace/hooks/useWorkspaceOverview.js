import { useEffect, useRef, useState } from 'react';
import { getWorkspaceOverview } from '@/services/workspaceService';

/**
 * Loads GET /api/workspace — the brief + 5 main KPI cards shown when the
 * Workspace page opens. Refetches whenever the selected date window changes.
 *
 * `loading` is derived from comparing the in-flight window against the last
 * resolved one, rather than a separate flag flipped inside the effect — that
 * would mean calling setState synchronously in the effect body on every
 * window change, which triggers an extra cascading render.
 */
export const useWorkspaceOverview = (windowDays) => {
  const [result, setResult] = useState({ data: null, forWindow: null });
  const requestIdRef = useRef(0);

  useEffect(() => {
    const requestId = ++requestIdRef.current;
    getWorkspaceOverview(windowDays)
      .then((res) => {
        if (requestIdRef.current === requestId) setResult({ data: res, forWindow: windowDays });
      })
      .catch((error) => {
        console.error('Failed to fetch workspace overview:', error);
        // Clear stale data on failure rather than keeping the previous
        // window's — otherwise `loading` flips false (forWindow now matches
        // windowDays) while `data` is still the old window's, and the UI
        // silently renders one window's numbers under another window's label.
        if (requestIdRef.current === requestId) setResult({ data: null, forWindow: windowDays });
      });
  }, [windowDays]);

  return {
    brief: result.data?.brief ?? null,
    kpis: result.data?.kpis ?? [],
    actions: result.data?.actions ?? [],
    loading: result.forWindow !== windowDays,
  };
};
