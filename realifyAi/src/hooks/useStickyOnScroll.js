import { useState, useEffect } from 'react';

/** The scroll container every dashboard page renders inside. */
export const SCROLL_CONTAINER_SELECTOR = '.dashboard-main-content';

/**
 * Reports whether `targetRef` has scrolled far enough out of view for a sticky
 * element to take over.
 *
 * @param targetRef  ref to the element being watched
 * @param options.threshold   IntersectionObserver thresholds
 * @param options.isStuck     given the entry, decide the stuck state
 */
export const useStickyOnScroll = (targetRef, { threshold, isStuck }) => {
  const [stuck, setStuck] = useState(false);

  useEffect(() => {
    const scrollEl = document.querySelector(SCROLL_CONTAINER_SELECTOR);
    const target = targetRef.current;
    if (!scrollEl || !target) return undefined;

    const observer = new IntersectionObserver(
      ([entry]) => setStuck(isStuck(entry)),
      { root: scrollEl, threshold }
    );
    observer.observe(target);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- matches the mount-only behaviour of the effects this replaced
  }, []);

  return stuck;
};
