/**
 * Projects the outcome of a what-if simulation for a given Workspace domain.
 *
 * Pure: same inputs always produce the same projection. Lives outside the
 * page so the numbers can be reasoned about (and tested) without rendering.
 */
/* ── Reactive computation ─────────────────────────────────────────────────── */
export const computeSimulation = (tab, val1, val2, channels) => {
  if (tab === 'inventory') {
    const velocity = 14, unitRev = 45;
    const currentDOC = Math.round(val1 / velocity);
    const projDOC     = Math.round((val1 + val2) / velocity);
    return {
      revenue: Math.round(Math.max(0, 21 - currentDOC) * velocity * unitRev),
      projRevenue: Math.round(Math.max(0, 21 - projDOC) * velocity * unitRev),
      reach: currentDOC,
      projReach: projDOC,
      ltv: Math.max(0, 100 - Math.round(currentDOC / 21 * 100)),
      projLtv: Math.max(0, 100 - Math.round(projDOC / 21 * 100)),
      conversion: val1,
      projConversion: val1 + val2,
    };
  }
  if (tab === 'ads') {
    const baseROAS = 2.8, baseImpr = 2400;
    const baseRevenue = Math.round(val1 * baseROAS);
    const ratio = val2 / val1;
    const projROAS = parseFloat(Math.max(1.8, baseROAS * (1 + 0.25 / ratio)).toFixed(1));
    const projRevenue = Math.round(val2 * projROAS);
    return {
      revenue: baseRevenue, projRevenue,
      reach: Math.round(baseROAS * 10), projReach: Math.round(projROAS * 10),
      ltv: parseFloat(baseROAS.toFixed(1)), projLtv: projROAS,
      conversion: Math.round(baseImpr * 1), projConversion: Math.round(baseImpr * ratio * 0.92),
    };
  }
  if (tab === 'cash') {
    const burnRate = 3000, baseCash = 84000;
    const projCash = baseCash + val1;
    const dailyRate = 5.25 / 100 / 365;
    const baseInterest = Math.round(val1 * dailyRate * 30);
    const projInterest = Math.round(val1 * dailyRate * val2);
    return {
      revenue: baseCash, projRevenue: projCash,
      reach: Math.round(baseCash / burnRate), projReach: Math.round(projCash / burnRate),
      ltv: baseInterest, projLtv: projInterest,
      conversion: 24200, projConversion: 24200 + val1 - projInterest,
    };
  }
  // sales / margin (default)
  const base = { revenue: 6200, reach: 412, ltv: 1.8, conversion: 2.4 };
  const priceDrop     = Math.max(0, (val1 - val2) / val1);
  const priceIncrease = Math.max(0, (val2 - val1) / val1);
  const chBoost       = 1 + (channels.length - 1) * 0.18;
  const marginFactor  = tab === 'margin' ? 0.3 : 0.8;
  return {
    ...base,
    projRevenue:    Math.round(base.revenue * (1 + priceDrop * 4.5 - priceIncrease * marginFactor) * chBoost),
    projReach:      Math.round(base.reach   * (1 + priceDrop * 100 + channels.length * 0.4)),
    projLtv:        parseFloat((base.ltv    * (1 + priceDrop * 5.8 + channels.length * 0.12)).toFixed(1)),
    projConversion: parseFloat((base.conversion * (1 + priceDrop * 7.1 - priceIncrease * 1.2)).toFixed(1)),
  };
};
