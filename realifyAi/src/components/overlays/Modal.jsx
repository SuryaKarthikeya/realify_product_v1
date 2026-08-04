import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';

/**
 * The single scrim/portal primitive for every overlay in the app.
 *
 * It renders the full-screen click-catcher and the backdrop, and nothing else —
 * the caller supplies its own panel as `children`. For the standard bordered
 * panel with a scrollable body and sticky footer, use `ModalPanel`, which is
 * built on top of this.
 *
 * Every visual knob is a prop because the app genuinely uses several different
 * scrims and stacking tiers, and those differences are load-bearing. Defaults
 * match the most common usage; callers override only what differs.
 *
 * `scrimMode` reflects a real DOM difference rather than a style preference:
 *   'container' — backdrop classes sit on the click-catcher itself (one node)
 *   'element'   — backdrop is a separate absolutely-positioned child, which
 *                 lets it animate opacity independently of the panel
 *
 * `closeOn='none'` leaves the container without a click handler, for callers
 * that render their own backdrop and wire dismissal to it (see AnimatedModal).
 */
const Modal = ({
  isOpen,
  onClose,
  children,
  portal = true,
  zIndex = 'z-[99999]',
  align = 'items-start sm:items-center',
  padding = 'px-4 py-5 sm:p-4',
  overflow = 'overflow-y-auto',
  scrim = 'bg-black/50 backdrop-blur-sm',
  scrimMode = 'container',
  lockScroll = false,
  closeOn = 'container',
}) => {
  useEffect(() => {
    if (!lockScroll) return undefined;
    document.body.style.overflow = isOpen ? 'hidden' : 'unset';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, lockScroll]);

  if (!isOpen) return null;

  const shellClass = [
    'fixed inset-0',
    zIndex,
    'flex',
    align,
    'justify-center',
    padding,
    overflow,
    scrimMode === 'container' ? scrim : '',
  ]
    .filter(Boolean)
    .join(' ');

  const shell = (
    <div className={shellClass} onClick={closeOn === 'container' ? onClose : undefined}>
      {scrimMode === 'element' && <div className={`absolute inset-0 ${scrim}`}></div>}
      {children}
    </div>
  );

  return portal ? createPortal(shell, document.body) : shell;
};

export default Modal;
