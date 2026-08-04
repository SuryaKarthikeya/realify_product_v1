import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useFilterStore = create(
  persist(
    (set) => ({
      dateRange: 'all',
      country: 'all',
      category: 'all',
      channel: 'all',
      products: [],
      searchQuery: '',

      setDateRange: (range) => set({ dateRange: range }),
      setCountry: (country) => set({ country }),
      setCategory: (category) => set({ category }),
      setChannel: (channel) => set({ channel }),
      setProducts: (products) => set({ products }),
      setSearchQuery: (query) => set({ searchQuery: query }),

      resetFilters: () => set({
        dateRange: 'all',
        country: 'all',
        category: 'all',
        channel: 'all',
        products: [],
        searchQuery: ''
      })
    }),
    {
      name: 'realify-filters',
      partialize: (state) => ({
        dateRange: state.dateRange,
        country: state.country,
        category: state.category,
        channel: state.channel,
        products: state.products,
      }),
    }
  )
);
