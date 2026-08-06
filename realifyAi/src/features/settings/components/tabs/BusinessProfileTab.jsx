import React, { useState } from 'react';
import { Input } from '@/components/ui/Input';
import SelectMenu from '@/components/ui/SelectMenu';

const BUSINESS_TYPES = [
  { id: '', label: 'Select Business Type' },
  { id: 'sole-proprietorship', label: 'Sole Proprietorship' },
  { id: 'llc', label: 'LLC' },
  { id: 'corporation', label: 'Corporation' },
  { id: 'partnership', label: 'Partnership' },
];

const GMV_RANGES = [
  { id: '', label: 'Select Range' },
  { id: 'under-100k', label: 'Under $100K' },
  { id: '100k-500k', label: '$100K – $500K' },
  { id: '500k-1m', label: '$500K – $1M' },
  { id: '1m-5m', label: '$1M – $5M' },
  { id: '5m-plus', label: '$5M+' },
];

const DIAL_CODES = ['+1', '+44', '+91'];

/* Matches the text inputs beside them. `!` because SelectMenu's own trigger
   classes would otherwise win on CSS order, not on where they sit in the
   class string. */
const FIELD_TRIGGER = '!bg-gray-50 dark:!bg-slate-800/50 !py-2.5 !text-sm !font-normal';

const BusinessProfileTab = ({ onInputChange }) => {
  /* Controlled, unlike the native selects these replaced — SelectMenu renders
     its own list, so it needs to be told what is chosen. */
  const [businessType, setBusinessType] = useState('');
  const [gmvRange, setGmvRange] = useState('');
  const [dialCode, setDialCode] = useState('+1');

  const pick = (setter) => (next) => {
    setter(next);
    onInputChange?.();
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm">
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Business Profile</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Store details for KYC and personalization</p>
      </div>

      <div className="p-6 space-y-5">
        {/* Store Info */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Store Name</label>
            <div className="relative">
              <input
                type="text"
                defaultValue="Acme Pets"
                disabled
                className="w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-xl text-sm text-gray-500 dark:text-slate-500 outline-none cursor-not-allowed"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded border border-blue-100 dark:border-blue-800">
                SHOPIFY SYNCED
              </span>
            </div>
            <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-1 italic">Store name is automatically managed by your primary integration.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Legal Business Name</label>
              <Input type="text" placeholder="e.g. Acme Corp LLC" onChange={onInputChange} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Business Type</label>
              <SelectMenu
                value={businessType}
                options={BUSINESS_TYPES}
                onChange={pick(setBusinessType)}
                ariaLabel="Business type"
                buttonClassName={FIELD_TRIGGER}
              />
            </div>
          </div>
        </div>

        {/* Address */}
        <div className="space-y-4">
          <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100">Business Address</h4>
          <Input type="text" placeholder="Street Address" onChange={onInputChange} />
          <div className="grid grid-cols-3 gap-4">
            <Input type="text" placeholder="City" onChange={onInputChange} />
            <Input type="text" placeholder="State" onChange={onInputChange} />
            <Input type="text" placeholder="ZIP" onChange={onInputChange} />
          </div>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 rounded-2xl flex items-start gap-3">
            <i className="fa-solid fa-circle-info text-blue-600 dark:text-blue-400 mt-0.5"></i>
            <p className="text-xs text-blue-700 dark:text-blue-300">
              Address information is required for KYC verification before we can process your first automated payout.
            </p>
          </div>
        </div>

        {/* Additional Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-gray-100 dark:border-slate-800">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Annual GMV Range</label>
            <SelectMenu
              value={gmvRange}
              options={GMV_RANGES}
              onChange={pick(setGmvRange)}
              ariaLabel="Annual GMV range"
              buttonClassName={FIELD_TRIGGER}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Business Phone</label>
            <div className="flex gap-2">
              <SelectMenu
                value={dialCode}
                options={DIAL_CODES}
                onChange={pick(setDialCode)}
                ariaLabel="Country dialling code"
                className="w-24 flex-shrink-0"
                buttonClassName={FIELD_TRIGGER}
              />
              <Input type="tel" placeholder="(555) 000-0000" onChange={onInputChange} className="flex-1 w-auto" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessProfileTab;
