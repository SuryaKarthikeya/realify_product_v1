import React, { useState } from 'react';
import AutonomySlider from '@/features/settings/components/AutonomySlider';

const GuardrailsTab = ({ onInputChange }) => {
  const [values, setValues] = useState({
    pricing: 1,
    inventory: 0,
    ads: 1,
    listings: 2
  });

  const handleChange = (key, val) => {
    setValues({ ...values, [key]: val });
    onInputChange();
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm">
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Agent Guardrails</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Control AI autonomy levels for different store actions</p>
      </div>

      <div className="p-6">
        <div className="p-5 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 rounded-2xl mb-5">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-brand rounded-xl flex items-center justify-center shadow-lg shadow-black/10 dark:shadow-gray-700/20 dark:bg-gray-600">
              <i className="fa-solid fa-shield-halved text-white"></i>
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">What are Guardrails?</p>
              <p className="text-xs text-gray-700 dark:text-slate-300 mt-1 leading-relaxed">
                Guardrails define how much freedom the AI agent has. 
                <span className="font-bold ml-1">Observe</span> means it only watches, 
                <span className="font-bold ml-1">Suggest</span> means it asks for approval, 
                <span className="font-bold ml-1">Assist</span> means it drafts the action, 
                <span className="font-bold ml-1">Act</span> means it executes autonomously.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <AutonomySlider 
            title="Price Adjustments" 
            sub="Buy Box repricing & discounts" 
            value={values.pricing} 
            onChange={(val) => handleChange('pricing', val)}
          />
          <AutonomySlider 
            title="Inventory Reorders" 
            sub="PO generation & restock alerts" 
            value={values.inventory} 
            onChange={(val) => handleChange('inventory', val)}
          />
          <AutonomySlider 
            title="Ad Budgets" 
            sub="Scaling & pausing campaigns" 
            value={values.ads} 
            onChange={(val) => handleChange('ads', val)}
          />
          <AutonomySlider 
            title="Listing Optimization" 
            sub="Updating titles, bullets & SEO" 
            value={values.listings} 
            onChange={(val) => handleChange('listings', val)}
          />
        </div>

        <div className="mt-5 pt-5 border-t border-gray-100 dark:border-slate-800">
          <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-4">Hard Constraints</h4>
          <div className="p-5 border border-gray-100 dark:border-slate-800 rounded-2xl bg-gray-50/30 dark:bg-slate-800/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Max Pricing Swing</p>
                <p className="text-xs text-gray-500 dark:text-slate-500">Maximum % change in a single day</p>
              </div>
              <div className="flex items-center gap-2">
                <input 
                  type="text" 
                  defaultValue="5%" 
                  onChange={onInputChange}
                  className="w-16 px-3 py-1.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-sm font-bold text-center outline-none focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30/20 transition-all dark:text-slate-300"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GuardrailsTab;
