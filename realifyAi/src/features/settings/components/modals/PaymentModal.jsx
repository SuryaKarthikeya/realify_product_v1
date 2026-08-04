import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedModal from '@/components/overlays/AnimatedModal';

const PaymentModal = ({ isOpen, onClose }) => {
  const [step, setStep] = useState(1);

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    if (step === 2) {
      setTimeout(() => {
        onClose();
        setStep(1);
      }, 2000);
    }
  };

  return (
    <AnimatedModal isOpen={isOpen} onClose={onClose}>
        {/* Progress Bar */}
        <div className="h-1 w-full bg-gray-100 dark:bg-slate-800">
          <motion.div
            className="h-full bg-blue-600"
            initial={{ width: '33.3%' }}
            animate={{ width: `${(step / 3) * 100}%` }}
          ></motion.div>
        </div>

        <div className="p-6">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-2xl flex items-center justify-center mb-6">
                  <i className="fa-solid fa-credit-card text-blue-600 dark:text-blue-400 text-2xl"></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Add Payment Method</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400 mb-5">Enter your card details to secure your subscription.</p>

                <div className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-1.5">Card Number</label>
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="0000 0000 0000 0000"
                        className="w-full pl-4 pr-12 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30/20 dark:text-slate-200"
                      />
                      <i className="fa-brands fa-cc-visa absolute right-4 top-1/2 -translate-y-1/2 text-blue-700 text-xl"></i>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-1.5">Expiry</label>
                      <input type="text" placeholder="MM/YY" className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none dark:text-slate-200" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-1.5">CVC</label>
                      <input type="text" placeholder="***" className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none dark:text-slate-200" />
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mt-5">
                  <button onClick={onClose} className="flex-1 py-3 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-bold active:scale-95 transition-all">Cancel</button>
                  <button onClick={handleNext} className="flex-1 py-3 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 active:scale-95 transition-all shadow-lg shadow-black/10 dark:shadow-gray-700/20">Next</button>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="text-center py-6"
              >
                <div className="w-20 h-20 border-4 border-brand dark:border-gray-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Verifying Card</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400">Please wait while we authorize your payment method with Stripe.</p>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-6"
              >
                <div className="w-20 h-20 bg-green-50 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                  <i className="fa-solid fa-check text-green-600 dark:text-green-400 text-3xl"></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Card Added!</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400">Visa ending in 4242 has been set as your default.</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
    </AnimatedModal>
  );
};

export default PaymentModal;
