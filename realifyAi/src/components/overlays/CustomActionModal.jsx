import { motion } from 'framer-motion';
import React from 'react';
import Modal from '@/components/overlays/Modal';
import SelectInput from '@/components/ui/SelectInput';

const MODAL_SELECT_CLASS = 'w-full px-4 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:border-transparent outline-none cursor-pointer dark:text-slate-200';

const CustomActionModal = ({ isOpen, onClose }) => (
  <Modal isOpen={isOpen} onClose={onClose}>
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      onClick={e => e.stopPropagation()}
    >
      <div className="p-6 border-b border-gray-200 dark:border-slate-800 sticky top-0 bg-white dark:bg-slate-900 z-10">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Create Custom Action</h3>
            <p className="text-sm text-gray-600 dark:text-slate-400 mt-1">Add a new action to your action center</p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition"
          >
            <i className="fa-solid fa-xmark text-gray-600 dark:text-slate-400 text-xl"></i>
          </button>
        </div>
      </div>

      <div className="p-6">
        <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
          <div>
            <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Action Title</label>
            <input
              type="text"
              placeholder="e.g., Negotiate better payment terms"
              className="w-full px-4 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:border-transparent outline-none dark:text-slate-200"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Description</label>
            <textarea
              rows="3"
              placeholder="Describe the action and its purpose..."
              className="w-full px-4 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:border-transparent outline-none resize-none dark:text-slate-200"
            ></textarea>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Priority</label>
              <SelectInput className={MODAL_SELECT_CLASS}>
                <option>Critical</option>
                <option>High</option>
                <option selected>Medium</option>
                <option>Low</option>
              </SelectInput>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Category</label>
              <SelectInput className={MODAL_SELECT_CLASS}>
                <option>Cash Management</option>
                <option>Payments</option>
                <option>Collections</option>
                <option>Forecasting</option>
                <option>Other</option>
              </SelectInput>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Due Date</label>
              <input
                type="date"
                className="w-full px-4 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:border-transparent outline-none dark:text-slate-200"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Assignee</label>
              <SelectInput className={MODAL_SELECT_CLASS}>
                <option>Sarah Johnson</option>
                <option>Michael Chen</option>
                <option>Emily Rodriguez</option>
                <option selected>Myself</option>
              </SelectInput>
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Expected Impact</label>
            <input
              type="text"
              placeholder="e.g., Save $5,000 monthly, Improve cash flow by 15%"
              className="w-full px-4 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:border-transparent outline-none dark:text-slate-200"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">Action Steps (Optional)</label>
            <textarea
              rows="4"
              placeholder="List the steps needed to complete this action..."
              className="w-full px-4 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:border-transparent outline-none resize-none dark:text-slate-200"
            ></textarea>
          </div>

          <div className="flex items-center gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-brand text-white rounded-xl font-medium hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition shadow-sm"
            >
              <i className="fa-solid fa-plus mr-2"></i>Create Action
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-xl text-gray-700 dark:text-slate-300 font-medium transition"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  </Modal>
);

export default CustomActionModal;
