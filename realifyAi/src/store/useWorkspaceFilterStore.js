import { create } from 'zustand';

/**
 * Workspace filter state, kept across domain-tab switches
 * Persists filter state across domain tab switches (Revenue <-> Margin <-> Cash <-> Inventory <-> Ads)
 */
export const useWorkspaceFilterStore = create((set) => ({
  // Default 3 Inline Filters
  timeRange: '30D', // '7D' | '14D' | '30D' | '60D' | '90D' | 'ALL' | 'Custom'
  // Multi-select: an empty array means the filter is off. See signalFilters.js.
  marketplace: [], // subset of 'amazon' | 'walmart' | 'shopify'
  categoryCut: [], // subset of PRODUCT_CATEGORIES values — see src/constants/filterOptions.js

  // Ads domain only — which ad platform the campaigns ran on.
  adPlatform: 'all', // 'all' | 'amazon-ads' | 'meta-ads' | 'google-ads'

  // Inventory domain only
  fulfillmentType: 'all',
  stockoutTime: 'all',
  confidence: 'all',

  // Cash domain only
  urgency: 'all',
  cashDirection: 'all',

  // Advanced Filters (Behind More Filters)
  brand: 'all',
  priceBand: 'all', // 'all' | 'under1000' | '1000to5000' | 'above5000'
  priority: 'all', // 'all' | 'HIGH' | 'MED' | 'LOW'
  performanceTier: 'all', // 'all' | 'top20' | 'mid60' | 'bottom20'
  subCategory: 'all',
  isMoreFiltersOpen: false,

  // Executed Actions tracking
  executedSignalIds: [],
  markSignalExecuted: (id) => set((state) => ({
    executedSignalIds: state.executedSignalIds.includes(id)
      ? state.executedSignalIds
      : [...state.executedSignalIds, id],
  })),

  // Status Filter — multi-select subset of 'executed' | 'not_executed'
  statusFilter: [],
  setStatusFilter: (statusFilter) => set({ statusFilter }),

  // Setters
  setTimeRange: (timeRange) => set({ timeRange }),
  setMarketplace: (marketplace) => set({ marketplace }),
  setCategoryCut: (categoryCut) => set({ categoryCut }),
  setAdPlatform: (adPlatform) => set({ adPlatform }),
  setFulfillmentType: (fulfillmentType) => set({ fulfillmentType }),
  setStockoutTime: (stockoutTime) => set({ stockoutTime }),
  setConfidence: (confidence) => set({ confidence }),
  setUrgency: (urgency) => set({ urgency }),
  setCashDirection: (cashDirection) => set({ cashDirection }),
  setBrand: (brand) => set({ brand }),
  setPriceBand: (priceBand) => set({ priceBand }),
  setPriority: (priority) => set({ priority }),
  setPerformanceTier: (performanceTier) => set({ performanceTier }),
  setSubCategory: (subCategory) => set({ subCategory }),
  setIsMoreFiltersOpen: (isOpen) => set({ isMoreFiltersOpen: isOpen }),

  resetAdvancedFilters: () => set({
    brand: 'all',
    priceBand: 'all',
    priority: 'all',
    performanceTier: 'all',
    subCategory: 'all',
  }),

  resetAllFilters: () => set({
    timeRange: '30D',
    marketplace: [],
    categoryCut: [],
    statusFilter: [],
    adPlatform: 'all',
    fulfillmentType: 'all',
    stockoutTime: 'all',
    confidence: 'all',
    urgency: 'all',
    cashDirection: 'all',
    brand: 'all',
    priceBand: 'all',
    priority: 'all',
    performanceTier: 'all',
    subCategory: 'all',
  }),
}));
