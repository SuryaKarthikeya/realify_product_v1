import { create } from "zustand";
import { storage } from "@/utils/storage";

export const useOnboardingStore = create((set) => ({
  step: 1,
  formValues: {
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    storeName: "",
    gmvRange: "", // range bucket label, set by typing an amount or picking a range
    annualGmv: "", // exact amount typed by the user, digits only

    primaryMarketplaces: [],
    goals: [
      { id: "1", title: "Increase Profitability", description: "Optimize pricing and reduce costs to maximize margins" },
      { id: "2", title: "Scale Revenue", description: "Grow sales across channels with intelligent automation" },
      { id: "3", title: "Optimize Inventory", description: "Reduce stockouts and overstock with predictive insights" },
      { id: "4", title: "Save Time", description: "Automate repetitive tasks and focus on strategy" },
    ],
  },
  connectedMarketplaces: [], // e.g., ["amazon", "shopify"]
  activeModal: null, // "signin", "connection"
  currentMarketplace: null, // for connection modal context
  showFAQ: false,

  setShowFAQ: (val) => set({ showFAQ: val }),
  setStep: (step) => set({ step, showFAQ: false }),
  
  updateFormValues: (values) =>
    set((state) => {
      // The greeting on later screens reads the name back from storage, so it
      // survives a reload even though this store is in-memory only.
      if (values.firstName !== undefined) storage.setUserName(values.firstName.trim());
      return { formValues: { ...state.formValues, ...values } };
    }),

  toggleMarketplace: (marketplace) =>
    set((state) => {
      const current = state.formValues.primaryMarketplaces;
      const updated = current.includes(marketplace)
        ? current.filter((m) => m !== marketplace)
        : [...current, marketplace];
      return { formValues: { ...state.formValues, primaryMarketplaces: updated } };
    }),

  setGoals: (goals) => set((state) => ({ formValues: { ...state.formValues, goals } })),

  addConnectedMarketplace: (marketplace) =>
    set((state) => ({ 
      connectedMarketplaces: [...new Set([...state.connectedMarketplaces, marketplace])] 
    })),

  setActiveModal: (modal) => set({ activeModal: modal }),
  setCurrentMarketplace: (marketplace) => set({ currentMarketplace: marketplace }),

  // Auth steps in connection modal
  connectionStep: 1,
  setConnectionStep: (step) => set({ connectionStep: step }),
}));
