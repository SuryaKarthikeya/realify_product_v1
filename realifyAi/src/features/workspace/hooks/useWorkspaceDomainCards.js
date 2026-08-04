import { useEffect, useRef, useState } from 'react';
import { getWorkspaceDomainCards, getWorkspaceDomainActions } from '@/services/workspaceService';

/**
 * Loads the 5 sub-stat cards (GET /api/workspace/{domain}) and the domain's
 * action table rows (GET /api/workspace/{domain}/actions) for one domain,
 * shown once a main KPI card is selected. Skipped entirely while no domain
 * is chosen.
 *
 * The two are separate routes but fetched together and cached as one
 * (domain, window) entry — they're always shown side by side, so they swap
 * in the same render rather than one landing a beat ahead of the other.
 * Revisiting a tab you've already loaded (the common case — users
 * bounce between Revenue/Margin/Inventory/... repeatedly) renders the cached
 * cards immediately with no loading flash, then silently revalidates in the
 * background and swaps in fresh numbers when they land — a plain fetch on
 * every switch was forcing a "…" skeleton flash on every tab click, even for
 * tabs already seen this session, which read as laggy/blinking. Only a
 * domain+window combination that has never been fetched shows the skeleton,
 * since there's genuinely nothing to show yet.
 *
 * `loading` is derived from comparing the in-flight (domain, window) key
 * against the last resolved one, rather than a separate flag flipped inside
 * the effect — see useWorkspaceOverview for why.
 */
export const useWorkspaceDomainCards = (domain, windowDays) => {
  const cacheRef = useRef(new Map());
  const key = domain ? `${domain}:${windowDays}` : null;

  const [result, setResult] = useState({ cards: [], actions: [], forKey: null });
  const [prevKey, setPrevKey] = useState(key);
  const requestIdRef = useRef(0);

  // Switching domain or window would otherwise keep showing the *previous*
  // key's cards under the new tab/range until the new fetch resolves, since
  // `cards` only gets replaced once a response lands. Adjusted here during
  // render (React's sanctioned way to reset state on a prop change) rather
  // than in the effect below, so it commits in the same render as the key
  // change instead of one tick later. A cache hit seeds the new cards
  // straight away instead of clearing to an empty skeleton.
  if (key !== prevKey) {
    setPrevKey(key);
    const cached = key ? cacheRef.current.get(key) : undefined;
    setResult(cached ? { ...cached, forKey: key } : { cards: [], actions: [], forKey: null });
  }

  useEffect(() => {
    if (!domain) return undefined;
    const requestId = ++requestIdRef.current;
    Promise.all([
      getWorkspaceDomainCards(domain, windowDays),
      getWorkspaceDomainActions(domain, windowDays),
    ])
      .then(([cardsRes, actionsRes]) => {
        const data = { cards: cardsRes?.cards ?? [], actions: actionsRes?.actions ?? [] };
        cacheRef.current.set(key, data);
        if (requestIdRef.current === requestId) setResult({ ...data, forKey: key });
      })
      .catch((error) => {
        console.error('Failed to fetch workspace domain cards/actions:', error);
        if (requestIdRef.current !== requestId) return;
        // A background revalidation failing shouldn't erase a cache hit
        // already on screen — only clear when this key has never resolved
        // successfully, so there's nothing legitimate to keep showing.
        if (!cacheRef.current.has(key)) setResult({ cards: [], actions: [], forKey: key });
      });
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` is derived from domain+windowDays every render, not an independent dep
  }, [domain, windowDays]);

  return {
    cards: domain ? result.cards : [],
    actions: domain ? result.actions : [],
    loading: Boolean(domain) && result.forKey !== key,
  };
};
