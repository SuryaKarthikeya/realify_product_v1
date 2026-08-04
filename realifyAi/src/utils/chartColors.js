export const CHART_PALETTE = {
  // Brand / Primary — keep in sync with --color-brand in src/index.css
  primary: '#383838',
  primaryLight: '#555555',
  primaryDark: '#2a2a2a',

  // Semantic
  success: '#10B981', // Emerald 500
  successLight: '#6EE7B7',
  danger: '#F43F5E', // Rose 500
  dangerLight: '#FDA4AF',
  warning: '#F59E0B', // Amber 500
  warningLight: '#FCD34D',
  info: '#3B82F6', // Blue 500
  infoLight: '#93C5FD',
  
  // Neutral / Foundation
  neutral: '#64748B', // Slate 500
  neutralLight: '#94A3B8',
  neutralDark: '#334155',

  // Categorical (Vibrant but professional)
  indigo: '#6366F1',
  violet: '#8B5CF6',
  cyan: '#06B6D4',
  emerald: '#10B981',
  amber: '#F59E0B',
  rose: '#F43F5E',
  blue: '#3B82F6',
  slate: '#64748B'
};

export const SEMANTIC_COLORS = {
  positive: CHART_PALETTE.success,
  negative: CHART_PALETTE.danger,
  warning: CHART_PALETTE.warning,
  info: CHART_PALETTE.info,
  neutral: CHART_PALETTE.neutral,
  revenue: CHART_PALETTE.dangerLight,
  expense: CHART_PALETTE.dangerLight, // Muted red for expenses in waterfall
  profit: CHART_PALETTE.success,
  forecast: CHART_PALETTE.neutralLight,
  actual: CHART_PALETTE.primary
};

// For charts with multiple categories
export const CHART_CATEGORICAL = [
  CHART_PALETTE.indigo,
  CHART_PALETTE.cyan,
  CHART_PALETTE.violet,
  CHART_PALETTE.emerald,
  CHART_PALETTE.amber,
  CHART_PALETTE.rose,
  CHART_PALETTE.blue,
  CHART_PALETTE.slate
];

// For gradient definitions or sequential data
export const CHART_SEQUENTIAL = [
  CHART_PALETTE.primaryDark,
  CHART_PALETTE.primary,
  CHART_PALETTE.primaryLight,
  '#909090',
  '#c0c0c0'
];
