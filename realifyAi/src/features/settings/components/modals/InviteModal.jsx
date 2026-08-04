import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedModal from '@/components/overlays/AnimatedModal';

const InviteModal = ({ isOpen, onClose }) => {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');

  const handleSend = () => {
    setStep(2);
    setTimeout(() => {
      onClose();
      setStep(1);
      setEmail('');
    }, 2000);
  };

  return (
    <AnimatedModal isOpen={isOpen} onClose={onClose}>
        <div className="p-6">
          <AnimatePresence mode="wait">
            {step === 1 ? (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-2xl flex items-center justify-center mb-6">
                  <i className="fa-solid fa-user-plus text-blue-600 dark:text-blue-400 text-2xl"></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Invite Team Member</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400 mb-5">They will receive an email to join your workspace.</p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-400 dark:text-slate-500 tracking-wider mb-2">Email Address</label>
                    <input 
                      type="email" 
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="e.g. sarah@company.com" 
                      className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-400 dark:text-slate-500 tracking-wider mb-2">Role</label>
                    <select className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-bold dark:text-slate-200">
                      <option>Analyst</option>
                      <option>Admin</option>
                      <option>Viewer</option>
                    </select>
                  </div>
                </div>

                <div className="flex gap-3 mt-5">
                  <button 
                    onClick={onClose}
                    className="flex-1 py-3 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-bold hover:bg-gray-200 transition-all active:scale-95"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={handleSend}
                    disabled={!email}
                    className="flex-1 py-3 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 shadow-lg shadow-black/10 dark:shadow-gray-700/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
                  >
                    Send Invite
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-center py-5"
              >
                <div className="w-20 h-20 bg-green-50 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                  <i className="fa-solid fa-check text-green-600 dark:text-green-400 text-3xl"></i>
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Invitation Sent!</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400">We've sent an invite to {email}.</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
    </AnimatedModal>
  );
};

export default InviteModal;
