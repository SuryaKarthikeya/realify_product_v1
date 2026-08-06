import { useEffect, useRef } from 'react';
import { SCROLL_CONTAINER_SELECTOR } from '@/hooks/useStickyOnScroll';

/** How far down the viewport an element can sit and still count as "in view". */
const COMFORT_BAND = 0.4;

/**
 * Brings the returned ref back into view inside the dashboard's scroll container
 * whenever `changeKey` changes.
 *
 * For step flows: finishing a step usually leaves the page scrolled to the
 * footer button that advanced it, so the next step's heading opens above the
 * fold and the user has to scroll up to find out where they are.
 *
 * Deliberately conditional — it does nothing while the element's top is already
 * in the upper part of the viewport, so a user who can see what changed never
 * has the page moved under them.
 *
 * @param changeKey  re-runs whenever this changes (the step id, usually)
 * @param offset     px to leave above the element — clear the sticky header
 */
export const useScrollIntoViewOnChange = (changeKey, { offset = 16 } = {}) => {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    const scroller = document.querySelector(SCROLL_CONTAINER_SELECTOR);
    if (!el || !scroller) return;

    const elTop = el.getBoundingClientRect().top;
    const box = scroller.getBoundingClientRect();
    const delta = elTop - box.top - offset;

    const alreadyInView = delta >= 0 && elTop < box.top + box.height * COMFORT_BAND;
    if (alreadyInView) return;

    scroller.scrollTo({ top: scroller.scrollTop + delta, behavior: 'smooth' });
  }, [changeKey, offset]);

  return ref;
};

/**
 * Puts the dashboard scroll container back at the top.
 *
 * Instant rather than smooth: this is used when the content underneath has been
 * replaced (a new page, a new wizard screen), and animating a scroll through
 * content the user never asked to see reads as a glitch.
 */
export const scrollDashboardToTop = () => {
  const scroller = document.querySelector(SCROLL_CONTAINER_SELECTOR);
  if (scroller) scroller.scrollTop = 0;
};
