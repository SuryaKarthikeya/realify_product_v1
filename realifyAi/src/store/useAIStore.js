import { create } from 'zustand';

export const useAIStore = create((set) => ({
  aiPromptValue: '',
  aiReferences: [],
  isAIResultOpen: false,
  isAiThinking: false,
  aiResultPanelMode: 'half', // 'half' | 'full' | 'minimized'

  setAiPromptValue: (value) => set({ aiPromptValue: value }),

  addAiReference: (ref) => set((state) => ({
    aiReferences: [...state.aiReferences, { ...ref, id: Date.now() + Math.random() }]
  })),
  removeAiReference: (id) => set((state) => ({
    aiReferences: state.aiReferences.filter(r => r.id !== id)
  })),
  clearAiReferences: () => set({ aiReferences: [] }),

  setAiThinking: (value) => set({ isAiThinking: value }),
  setAIResultOpen: (isOpen) => set({ isAIResultOpen: isOpen }),
  setAIResultMode: (mode) => set({ aiResultPanelMode: mode }),
  closeAIResult: () => set({ isAIResultOpen: false, aiResultPanelMode: 'half', aiReferences: [] }),
}));
