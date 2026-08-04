import { create } from 'zustand';

export const useExplainStore = create((set) => ({
  explainMode: false,
  setExplainMode: (val) => set({ explainMode: val }),
}));
