

export const formatCurrency = (value, currency = 'USD', locale = 'en-US') => {
  const safeValue = isNaN(value) || value === null || value === undefined ? 0 : value;
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
  }).format(safeValue);
};

export const formatNumber = (value, locale = 'en-US') => {
  return new Intl.NumberFormat(locale).format(value);
};

export const formatCompactNumber = (value, locale = 'en-US') => {
  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
};

export const formatDate = (date, options = {}, locale = 'en-US') => {
  const defaultOptions = { month: 'short', day: 'numeric', year: 'numeric' };
  return new Intl.DateTimeFormat(locale, { ...defaultOptions, ...options }).format(new Date(date));
};

export const formatPercentage = (value, decimals = 1, locale = 'en-US') => {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

// Compact currency in thousands, e.g. $12K / $12.3K. Always uppercase K so it
// matches formatCompactMoney elsewhere in the app.
export const formatCompactCurrency = (val, { decimals = 0, suffix = 'K' } = {}) =>
  `$${(val / 1000).toFixed(decimals)}${suffix}`;

/** Drops a trailing `.0` so 1.0M reads as 1M. */
const trimZero = (s) => s.replace(/\.0$/, '');

/**
 * Compact magnitude with K / M suffixes only — never lakh or crore.
 *
 * Keeps one decimal on K and two on M, trimming trailing zeros, so headline
 * figures stay exact ($248.5K, $1.82M) instead of rounding to $249K / $1.8M.
 *
 * 940 -> "940" · 22000 -> "22K" · 248500 -> "248.5K" · 1820000 -> "1.82M"
 */
export const formatCompactMagnitude = (value) => {
  const abs = Math.abs(value || 0);
  const sign = (value || 0) < 0 ? '-' : '';
  if (abs >= 1_000_000) return `${sign}${trimZero((abs / 1_000_000).toFixed(2).replace(/0$/, ''))}M`;
  if (abs >= 1_000) return `${sign}${trimZero((abs / 1_000).toFixed(1))}K`;
  return `${sign}${Math.round(abs)}`;
};

/** Compact money in dollars, K / M only. 240000 -> "$240K" */
export const formatCompactMoney = (value) => {
  const abs = Math.abs(value || 0);
  const sign = (value || 0) < 0 ? '-' : '';
  return `${sign}$${formatCompactMagnitude(abs)}`;
};

/** Sign-aware compact money for deltas. 240000 -> "+$240K" */
export const formatSignedMoney = (value) =>
  `${(value || 0) < 0 ? '-' : '+'}$${formatCompactMagnitude(Math.abs(value || 0))}`;

// Cuts text to the longest whole-word prefix that fits within maxChars — no
// ellipsis, no partial trailing word (unlike CSS text-overflow: ellipsis).
export const truncateAtWordBoundary = (text, maxChars = 20) => {
  if (!text || text.length <= maxChars) return text;
  const words = text.split(' ');
  let result = '';
  for (const word of words) {
    const next = result ? `${result} ${word}` : word;
    if (next.length > maxChars) break;
    result = next;
  }
  return result || text.slice(0, maxChars);
};
