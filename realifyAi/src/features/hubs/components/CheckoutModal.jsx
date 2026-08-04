import { memo } from 'react';
import Modal from '@/components/overlays/Modal';

const CheckoutModal = memo(({ plugin, state, onClose, onProcess }) => (
  <Modal isOpen={true} onClose={onClose}>
    <div
      className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
      onClick={e => e.stopPropagation()}
    >
      {/* Modal Header */}
      <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex justify-between items-center bg-gray-50 dark:bg-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Checkout</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors"
        >
          <i className="fa-solid fa-xmark text-xl" />
        </button>
      </div>

      <div className="p-6">
        {/* Plugin Summary */}
        <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-100 dark:border-slate-800">
          <div
            className={`w-12 h-12 ${plugin.iconBg} ${plugin.iconColor} rounded-xl flex items-center justify-center text-xl flex-shrink-0`}
          >
            <i className={`fa-solid ${plugin.icon}`} />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-bold text-gray-900 dark:text-white truncate">{plugin.title}</h4>
            <p className="text-sm text-gray-500 dark:text-slate-400">Monthly Subscription</p>
          </div>
          <span className="font-bold text-gray-900 dark:text-white flex-shrink-0">{plugin.priceModal}</span>
        </div>

        {/* Payment Method */}
        <div className="mb-6">
          <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-3">Payment Method</h4>
          <div className="border border-blue-200 dark:border-blue-700 rounded-xl p-3 flex items-center gap-3 bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-500">
            <i className="fa-brands fa-cc-visa text-2xl text-blue-800 dark:text-blue-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Visa ending in 4242</p>
              <p className="text-xs text-gray-500 dark:text-slate-400">Expires 12/25</p>
            </div>
            <i className="fa-solid fa-circle-check text-blue-600" />
          </div>
          <button className="mt-3 text-sm text-blue-600 font-medium hover:underline flex items-center gap-1">
            <i className="fa-solid fa-plus text-xs" /> Add new payment method
          </button>
        </div>

        {/* Order Summary */}
        <div className="space-y-2 text-sm mb-6 bg-gray-50 dark:bg-slate-800 p-4 rounded-xl">
          <div className="flex justify-between text-gray-600 dark:text-slate-400">
            <span>Subtotal</span><span>{plugin.priceModal}</span>
          </div>
          <div className="flex justify-between text-gray-600 dark:text-slate-400">
            <span>Tax</span><span>$0.00</span>
          </div>
          <div className="flex justify-between text-green-600 font-medium">
            <span>14-Day Trial Discount</span><span>-{plugin.priceModal}</span>
          </div>
          <div className="border-t border-gray-200 dark:border-slate-700 pt-2 mt-2 flex justify-between font-bold text-gray-900 dark:text-white text-base">
            <span>Total Due Today</span><span>$0.00</span>
          </div>
        </div>

        {/* CTA */}
        <button
          onClick={onProcess}
          disabled={state !== 'idle'}
          className={`w-full py-3 text-white font-bold rounded-xl transition shadow-sm flex items-center justify-center gap-2 disabled:cursor-not-allowed ${
            state === 'success' ? 'bg-green-600' : 'bg-brand hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500'
          }`}
        >
          {state === 'idle' && <><i className="fa-solid fa-lock" /> Subscribe &amp; Install</>}
          {state === 'processing' && <><i className="fa-solid fa-spinner fa-spin" /> Processing...</>}
          {state === 'success' && <><i className="fa-solid fa-check" /> Installed Successfully!</>}
        </button>

        <p className="text-xs text-center text-gray-500 dark:text-slate-400 mt-3">
          Your trial starts today. You'll be charged {plugin.priceModal}/month after 14 days. Cancel anytime.
        </p>
      </div>
    </div>
  </Modal>
));

CheckoutModal.displayName = 'CheckoutModal';

export default CheckoutModal;
