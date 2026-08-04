import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedModal from '@/components/overlays/AnimatedModal';

const ConnectModal = ({ platform, onClose }) => {
  const [step, setStep] = useState(1);

  const handleConnect = () => {
    setStep(2);
    setTimeout(() => {
      setStep(3);
    }, 2000);
  };

  if (!platform) return null;

  return (
    <AnimatedModal isOpen={!!platform} onClose={onClose}>
        <div className="p-6 text-center">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
              >
                <div className={`w-20 h-20 ${platform.bgColor} rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg`}>
                  <i className={`fa-brands ${platform.icon} ${platform.color} text-4xl`}></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Connect {platform.name}</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400 mb-5">
                  Authorize Realify to sync your performance data and automate actions.
                </p>
                
                <div className="p-4 bg-gray-50 dark:bg-slate-800/50 rounded-2xl mb-5 text-left border border-gray-100 dark:border-slate-800">
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-3">We will access:</p>
                  <ul className="space-y-2">
                    {['Product Catalog', 'Orders & Revenue', 'Ad Campaign Data'].map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-xs text-gray-700 dark:text-slate-300 font-medium">
                        <i className="fa-solid fa-circle-check text-green-500"></i>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex gap-3">
                  <button onClick={onClose} className="flex-1 py-3 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-bold active:scale-95">Cancel</button>
                  <button onClick={handleConnect} className="flex-1 py-3 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 shadow-lg active:scale-95">Authorize</button>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="py-8"
              >
                <div className="w-16 h-16 border-4 border-brand dark:border-gray-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Syncing Data...</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400">Establishing secure handshake with {platform.name}.</p>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="py-5"
              >
                <div className="w-20 h-20 bg-green-50 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                  <i className="fa-solid fa-check text-green-600 dark:text-green-400 text-3xl"></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Connected!</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400 mb-5">{platform.name} is now successfully integrated.</p>
                <button onClick={onClose} className="w-full py-3 bg-slate-900 dark:bg-slate-800 text-white rounded-xl text-sm font-bold active:scale-95">Back to Settings</button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
    </AnimatedModal>
  );
};

export default ConnectModal;
