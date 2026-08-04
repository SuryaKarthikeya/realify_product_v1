import { motion } from 'framer-motion';
import React, { useState } from 'react';
import Modal from '@/components/overlays/Modal';

const CustomRoleModal = ({ isOpen, onClose }) => {
  const [roleName, setRoleName] = useState('');

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-gray-100 dark:border-slate-800"
      >
        <div className="p-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Create Custom Role</h3>
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-5">Define a new set of permissions for specific team members.</p>

          <div className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-gray-400 dark:text-slate-500 tracking-wider mb-2">Role Name</label>
              <input
                type="text"
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
                placeholder="e.g. Inventory Manager"
                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30/20 dark:text-slate-200"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-400 dark:text-slate-500 tracking-wider mb-4">Base Permissions</label>
              <div className="space-y-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                {[
                  'View Financial Data',
                  'Execute API Actions',
                  'Modify Guardrails',
                  'Access CMD Prompt',
                  'Export Workspace Data',
                  'Manage Team Invites'
                ].map((p, i) => (
                  <label key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-800 cursor-pointer hover:bg-gray-100 transition-colors">
                    <span className="text-sm font-medium text-gray-700 dark:text-slate-300">{p}</span>
                    <input type="checkbox" className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500/20" />
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-3 mt-5">
            <button onClick={onClose} className="flex-1 py-3 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-bold active:scale-95 transition-all">Cancel</button>
            <button
              onClick={onClose}
              disabled={!roleName}
              className="flex-1 py-3 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 shadow-lg shadow-black/10 dark:shadow-gray-700/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            >
              Create Role
            </button>
          </div>
        </div>
      </motion.div>
    </Modal>
  );
};

export default CustomRoleModal;
