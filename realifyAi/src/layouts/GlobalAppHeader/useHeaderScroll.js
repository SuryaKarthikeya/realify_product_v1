import { useState, useEffect, useRef, useLayoutEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

/** Wider range = smoother gradual collapse while scrolling down */
const COLLAPSE_START = 0;
const COLLAPSE_END = 110;
const COMPRESSED_THRESHOLD = 0.88;
const EXPAND_ANIM_MS = 340;
const RELEASE_EXPAND_SCROLL = 56;

function clamp01(v) {
  return Math.min(1, Math.max(0, v));
}

/** Smoothstep — softer collapse feel tied to scroll position */
function scrollToProgress(scrollY) {
  const t = clamp01((scrollY - COLLAPSE_START) / (COLLAPSE_END - COLLAPSE_START));
  return t * t * (3 - 2 * t);
}

function readSecondaryHeight() {
  return (
    parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue('--header-secondary-height')
    ) || 0
  );
}

function easeOutCubic(t) {
  return 1 - (1 - t) ** 3;
}

function visibleToolbarHeight(toolbar, progress) {
  const p = clamp01(progress);
  return Math.round(toolbar.compressed + (toolbar.expanded - toolbar.compressed) * (1 - p));
}

export function useHeaderScroll(toolbar = { compressed: 64, expanded: 84 }, scrollElRef = null) {
  const [uiProgress, setUiProgress] = useState(0);
  const [isForceExpanded, setIsForceExpanded] = useState(false);

  const progressRef = useRef(0);
  const maxCollapseRef = useRef(0);
  const forceExpandedRef = useRef(false);
  const isAnimatingRef = useRef(false);
  const animFrameRef = useRef(null);
  const rafId = useRef(null);
  const lastScrollY = useRef(0);
  const location = useLocation();
  const [isScrolled, setIsScrolled] = useState(false);

  const publishLayout = useCallback(
    (p) => {
      const root = document.documentElement;
      root.style.setProperty('--header-collapse-progress', String(p));
      root.classList.toggle('header-is-compressed', p > 0.02);
      const secondaryH = readSecondaryHeight();
      const toolbarVisible = visibleToolbarHeight(toolbar, p);
      root.style.setProperty('--header-toolbar-visible', `${toolbarVisible}px`);
      const visible = toolbarVisible + Math.round(secondaryH * (1 - p));
      root.style.setProperty('--page-header-height', `${visible}px`);
    },
    [toolbar]
  );

  const applyProgress = useCallback(
    (p, { updateUi = true } = {}) => {
      const clamped = clamp01(p);
      progressRef.current = clamped;
      publishLayout(clamped);

      if (!updateUi) return;

      setUiProgress((prev) => {
        const wasCompressed = prev >= COMPRESSED_THRESHOLD;
        const nowCompressed = clamped >= COMPRESSED_THRESHOLD;
        if (wasCompressed !== nowCompressed || Math.abs(prev - clamped) > 0.12) {
          return clamped;
        }
        return prev;
      });
    },
    [publishLayout]
  );

  const syncCollapseFromScroll = () => {
    if (isAnimatingRef.current) return;

    const scrollY = scrollElRef?.current?.scrollTop ?? window.scrollY;
    setIsScrolled(scrollY > 0);
    const scrollDiff = scrollY - lastScrollY.current;

    // Auto-expand smoothly when scrolled back to top
    if (scrollY <= 5 && !forceExpandedRef.current && maxCollapseRef.current > 0.02) {
      isAnimatingRef.current = true;
      document.documentElement.classList.add('header-expand-animating');
      const from = progressRef.current;
      const start = performance.now();
      const tick = (now) => {
        const t = clamp01((now - start) / EXPAND_ANIM_MS);
        const p = from * (1 - easeOutCubic(t));
        applyProgress(p);
        if (t < 1) {
          animFrameRef.current = requestAnimationFrame(tick);
        } else {
          isAnimatingRef.current = false;
          document.documentElement.classList.remove('header-expand-animating');
          forceExpandedRef.current = true;
          setIsForceExpanded(true);
          maxCollapseRef.current = 0;
          applyProgress(0);
          animFrameRef.current = null;
        }
      };
      animFrameRef.current = requestAnimationFrame(tick);
      lastScrollY.current = scrollY;
      return;
    }

    if (forceExpandedRef.current) {
      if (scrollDiff > RELEASE_EXPAND_SCROLL) {
        forceExpandedRef.current = false;
        setIsForceExpanded(false);
        maxCollapseRef.current = scrollToProgress(scrollY);
        applyProgress(maxCollapseRef.current);
      } else {
        applyProgress(0, { updateUi: false });
        publishLayout(0);
      }
      lastScrollY.current = scrollY;
      return;
    }

    const scrollProgress = scrollToProgress(scrollY);

    /* Collapse only deepens on scroll — scrolling up never expands */
    if (scrollProgress > maxCollapseRef.current) {
      maxCollapseRef.current = scrollProgress;
    }

    applyProgress(maxCollapseRef.current);
    lastScrollY.current = scrollY;
  };

  const resetHeader = () => {
    forceExpandedRef.current = false;
    isAnimatingRef.current = false;
    const scrollY = scrollElRef?.current?.scrollTop ?? window.scrollY;
    maxCollapseRef.current = scrollToProgress(scrollY);
    setIsForceExpanded(false);
    document.documentElement.classList.remove('header-expand-animating');
    applyProgress(maxCollapseRef.current);
    lastScrollY.current = scrollY;
  };

  useLayoutEffect(() => {
    // Reset internal scroll container to top on route change
    if (scrollElRef?.current) {
      scrollElRef.current.scrollTop = 0;
    }
    setTimeout(() => resetHeader(), 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname, scrollElRef]);

  useEffect(() => {
    const onScroll = () => {
      if (rafId.current != null) return;
      rafId.current = requestAnimationFrame(() => {
        syncCollapseFromScroll();
        rafId.current = null;
      });
    };

    const target = scrollElRef?.current ?? window;
    target.addEventListener('scroll', onScroll, { passive: true });
    setTimeout(() => syncCollapseFromScroll(), 0);

    return () => {
      target.removeEventListener('scroll', onScroll);
      if (rafId.current != null) cancelAnimationFrame(rafId.current);
      if (animFrameRef.current != null) cancelAnimationFrame(animFrameRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scrollElRef]);

  useEffect(
    () => () => {
      const root = document.documentElement;
      root.classList.remove('header-expand-animating');
      root.style.removeProperty('--page-header-height');
      root.style.removeProperty('--header-collapse-progress');
      root.style.removeProperty('--header-secondary-height');
    },
    []
  );

  const forceExpand = useCallback(() => {
    if (isAnimatingRef.current) return;

    const from = progressRef.current;
    if (from <= 0.02) {
      forceExpandedRef.current = true;
      setIsForceExpanded(true);
      maxCollapseRef.current = 0;
      applyProgress(0);
      return;
    }

    isAnimatingRef.current = true;
    document.documentElement.classList.add('header-expand-animating');

    const start = performance.now();

    const tick = (now) => {
      const t = clamp01((now - start) / EXPAND_ANIM_MS);
      const p = from * (1 - easeOutCubic(t));
      applyProgress(p);

      if (t < 1) {
        animFrameRef.current = requestAnimationFrame(tick);
      } else {
        isAnimatingRef.current = false;
        document.documentElement.classList.remove('header-expand-animating');
        forceExpandedRef.current = true;
        setIsForceExpanded(true);
        maxCollapseRef.current = 0;
        applyProgress(0);
        animFrameRef.current = null;
      }
    };

    animFrameRef.current = requestAnimationFrame(tick);
  }, [applyProgress]);

  const isCompressed = uiProgress >= COMPRESSED_THRESHOLD;

  return {
    progress: uiProgress,
    isCompressed,
    isScrolled,
    isForceExpanded,
    forceExpand,
  };
}

export function notifyHeaderMeasured(toolbar = { compressed: 64, expanded: 84 }) {
  const root = document.documentElement;
  const p =
    parseFloat(root.style.getPropertyValue('--header-collapse-progress')) ||
    parseFloat(getComputedStyle(root).getPropertyValue('--header-collapse-progress')) ||
    0;
  const secondaryH = readSecondaryHeight();
  const toolbarVisible = visibleToolbarHeight(toolbar, p);
  root.style.setProperty('--header-toolbar-visible', `${toolbarVisible}px`);
  root.style.setProperty('--page-header-height', `${toolbarVisible + Math.round(secondaryH * (1 - p))}px`);
}
