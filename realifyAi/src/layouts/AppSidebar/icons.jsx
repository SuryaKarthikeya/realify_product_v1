import React from 'react';

/* ── Perplexity-style panel icons ── */
export const IconPanelCollapse = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <rect x="1" y="2" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.4" />
    <path d="M5.5 2v12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    <rect x="1" y="2" width="4.5" height="12" rx="2" fill="currentColor" fillOpacity="0.2" />
  </svg>
);

export const IconPanelExpand = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <rect x="1" y="2" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.4" />
    <path d="M5.5 2v12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
  </svg>
);

/* ── History section with group-by, toggle, and 3-dot context menu ── */
