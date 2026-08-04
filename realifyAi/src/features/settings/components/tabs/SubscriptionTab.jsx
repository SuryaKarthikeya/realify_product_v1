import React, { useState } from 'react';
import {
  BILLING_CYCLES,
  SUBSCRIPTION_FOOTNOTES,
  SUBSCRIPTION_PLANS,
  priceFor,
} from '@/features/settings/data/subscriptionPlans';

const SubscriptionTab = () => {
  const [cycle, setCycle] = useState('monthly');

  const plans = SUBSCRIPTION_PLANS;

  return (
    <div className="p-6 space-y-6">
      {/* Plan Selection */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5 gap-4 flex-wrap">
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Choose Your Plan</h3>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Upgrade or downgrade anytime. Changes apply immediately.</p>
          </div>
          <button className="px-4 py-2 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-bold hover:bg-gray-100 transition-all active:scale-95">
            <i className="fa-solid fa-file-invoice-dollar mr-2"></i>Pricing Help
          </button>
        </div>

        {/* Billing cycle — annual prices are derived, so the SAVE badge and the
            numbers below can never disagree. */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex items-center gap-1 p-1 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-full">
            {BILLING_CYCLES.map((c) => {
              const active = cycle === c.key;
              return (
                <button
                  key={c.key}
                  onClick={() => setCycle(c.key)}
                  aria-pressed={active}
                  className={`px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
                    active
                      ? 'bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 shadow-sm'
                      : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'
                  }`}
                >
                  {c.label}
                  {c.badge && (
                    <span className="px-1.5 py-0.5 rounded-full bg-brand text-white dark:bg-gray-600 text-[9px] font-bold tracking-wide">
                      {c.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-stretch">
          {plans.map((plan) => (
            <div
              key={plan.id}
              /* flex column + mt-auto on the button keeps all four CTAs on one
                 line even though the tiers list different numbers of features. */
              className={`relative flex flex-col h-full p-5 rounded-2xl border-2 transition-all group ${
                plan.current
                  ? 'border-brand dark:border-gray-500 bg-blue-50/10 dark:bg-blue-900/10'
                  : 'border-gray-100 dark:border-slate-800 hover:border-gray-200 dark:hover:border-slate-700'
              }`}
            >
              {plan.current && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-brand text-white text-[10px] font-bold rounded-full shadow-lg dark:bg-gray-600">
                  CURRENT
                </div>
              )}

              <div className="flex items-start justify-between gap-2 mb-2">
                <p className={`text-xs font-bold uppercase tracking-wider ${plan.current ? 'text-blue-600' : 'text-gray-500 dark:text-slate-400'}`}>
                  {plan.name}
                </p>
                {plan.recommended && (
                  <span className="px-2 py-0.5 rounded-full bg-brand text-white dark:bg-gray-600 text-[9px] font-bold uppercase tracking-wider whitespace-nowrap flex-shrink-0">
                    Recommended
                  </span>
                )}
              </div>

              {plan.isCustomPrice ? (
                <div className="mb-1">
                  <span className="text-2xl font-bold text-gray-900 dark:text-slate-100">{plan.price}</span>
                </div>
              ) : (
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-3xl font-bold text-gray-900 dark:text-slate-100">
                    {priceFor(plan, cycle)}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-slate-400">/month</span>
                </div>
              )}

              {plan.audience && (
                <p className="text-[11px] font-semibold text-gray-600 dark:text-slate-300 mt-1">{plan.audience}</p>
              )}
              {plan.tagline && (
                <p className="text-[11px] italic text-gray-500 dark:text-slate-400 mt-1 leading-relaxed">{plan.tagline}</p>
              )}

              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-800">
                {plan.inherits && (
                  <p className="text-[11px] font-bold text-gray-800 dark:text-slate-200 mb-3">{plan.inherits}</p>
                )}

                <ul className="space-y-3">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-gray-600 dark:text-slate-400 font-medium">
                      <i className={`fa-solid fa-check mt-0.5 flex-shrink-0 ${plan.current ? 'text-blue-500' : 'text-emerald-500'}`}></i>
                      <span className="leading-relaxed">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-auto pt-4">
                <button
                  className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all active:scale-95 ${
                    plan.current
                      ? 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-500 cursor-default'
                      : 'bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 shadow-md shadow-black/10 dark:shadow-gray-700/20'
                  }`}
                >
                  {plan.current ? 'Active Plan' : plan.cta}
                </button>
                <p className="text-[10.5px] text-gray-400 dark:text-slate-500 text-center mt-2">{plan.trial}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Small print, dot-separated as in the design */}
        <p className="text-[11px] text-gray-500 dark:text-slate-400 text-center mt-6 leading-relaxed">
          {SUBSCRIPTION_FOOTNOTES.map((note, i) => (
            <React.Fragment key={note.text}>
              {i > 0 && <span className="mx-1.5 text-gray-300 dark:text-slate-600">·</span>}
              <span className={note.highlight ? 'font-bold text-emerald-600 dark:text-emerald-400' : ''}>
                {note.text}
              </span>
            </React.Fragment>
          ))}
        </p>
      </div>
    </div>
  );
};

export default SubscriptionTab;
