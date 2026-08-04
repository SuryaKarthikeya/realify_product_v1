/**
 * Utility helper functions for mapping Inventory Insight Action Buttons & Severity Filtering.
 */

/**
 * Maps an insight to its relevant action button(s).
 * 
 * Mapping rules:
 * - Stock-out risk / understock → "Create Purchase Order"
 * - Overstock / excess inventory → "Pause Purchase Order" (optionally paired with "Liquidate" if aging/dead stock)
 * - Supplier delay → "Schedule Purchase"
 * - Cross-channel imbalance → "Transfer Inventory"
 * - Dead stock / aging inventory → "Liquidate"
 */
export const getInsightActionButtons = (insight) => {
  if (!insight) {
    return [{ label: 'Create Purchase Order', action: 'create_po', primary: true }];
  }

  const type = (insight.issue || insight.actionType || insight.type || '').toLowerCase();
  const text = `${insight.headline || ''} ${insight.title || ''} ${insight.heading || ''} ${insight.tagCategory || ''} ${insight.body || ''} ${insight.description || ''} ${insight.whyMattersText || ''}`.toLowerCase();

  // Keyword flags
  const isDeadStock = type.includes('dead') || text.includes('dead stock') || text.includes('discontinue') || text.includes('aging stock');
  const isAging = type.includes('aging') || text.includes('aging') || text.includes('90+ days') || text.includes('180-day') || text.includes('aging inventory');

  const isUnderstock = type.includes('understock') || type.includes('stockout') || 
    text.includes('stockout') || text.includes('stock-out') || text.includes('understock') || 
    text.includes('low stock') || text.includes('critical restock') || text.includes('days of cover is down') || 
    text.includes('days cover remaining') || text.includes('expedite required') || text.includes('reorder required') || text.includes('restock');

  const isOverstock = type.includes('overstock') || type.includes('excess') || 
    text.includes('overstock') || text.includes('excess inventory') || text.includes('stock building up') || text.includes('excess stock');

  const isSupplierDelay = type.includes('supplier') || type.includes('delay') || 
    text.includes('supplier delay') || text.includes('supplier lead time') || text.includes('lead time increase') || text.includes('supplier minimum order') || text.includes('po delayed');

  const isChannelImbalance = type.includes('channel') || type.includes('imbalance') || 
    text.includes('cross-channel') || text.includes('channel imbalance') || text.includes('allocation imbalance') || 
    text.includes('fba inventory running low') || text.includes('rebalancing allocation') || text.includes('move 200 units') || text.includes('returns pipeline');

  // Priority mapping resolution
  if (isDeadStock && !isOverstock) {
    return [
      { label: 'Liquidate', action: 'liquidate', primary: true }
    ];
  }

  if (isUnderstock) {
    return [
      { label: 'Create Purchase Order', action: 'create_po', primary: true }
    ];
  }

  if (isOverstock) {
    if (isAging || isDeadStock || text.includes('liquidat')) {
      return [
        { label: 'Pause Purchase Order', action: 'pause_po', primary: true },
        { label: 'Liquidate', action: 'liquidate', primary: false }
      ];
    }
    return [
      { label: 'Pause Purchase Order', action: 'pause_po', primary: true }
    ];
  }

  if (isSupplierDelay) {
    return [
      { label: 'Schedule Purchase', action: 'schedule_purchase', primary: true }
    ];
  }

  if (isChannelImbalance) {
    return [
      { label: 'Transfer Inventory', action: 'transfer_inventory', primary: true }
    ];
  }

  if (isAging) {
    return [
      { label: 'Liquidate', action: 'liquidate', primary: true }
    ];
  }

  // Fallback to Create Purchase Order
  return [
    { label: insight.actionLabel || 'Create Purchase Order', action: 'create_po', primary: true }
  ];
};

/**
 * Normalizes and filters an array of insights by severity level.
 * Accepts: 'All', 'Critical', 'High', 'Medium', 'Low'.
 */
export const filterInsightsBySeverity = (insights = [], severityFilter = 'All') => {
  if (!severityFilter || severityFilter === 'All') return insights;

  const target = severityFilter.toLowerCase();

  return insights.filter((insight) => {
    const rawSeverity = (
      insight.severity || 
      insight.priority || 
      insight.type || 
      insight.confidenceLabel || 
      ''
    ).toLowerCase();

    if (target === 'critical') {
      return rawSeverity.includes('critical');
    }
    if (target === 'high') {
      return rawSeverity.includes('high');
    }
    if (target === 'medium') {
      return rawSeverity.includes('medium') || rawSeverity.includes('warning') || rawSeverity.includes('opportunity');
    }
    if (target === 'low') {
      return rawSeverity.includes('low') || rawSeverity.includes('insight') || rawSeverity.includes('market') || rawSeverity.includes('info');
    }
    return rawSeverity.includes(target);
  });
};
