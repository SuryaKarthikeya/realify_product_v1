import { motion } from 'framer-motion';
import React from 'react';

const ActionDetail = ({ action, onClose }) => {
  if (!action) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-20 h-20 bg-gray-50 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
          <i className="fa-solid fa-hand-pointer text-4xl text-gray-300 dark:text-slate-600"></i>
        </div>
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-1">Action Details</h3>
        <p className="text-gray-500 dark:text-slate-400 max-w-[200px]">Select an action from the list to view granular details</p>
      </div>
    );
  }

  const priorityColors = {
    'red': { bg: 'bg-red-600', light: 'bg-red-50 dark:bg-red-900/10', text: 'text-red-700 dark:text-red-400', border: 'border-red-200 dark:border-red-900/30' },
    'orange': { bg: 'bg-orange-600', light: 'bg-orange-50 dark:bg-orange-900/10', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-200 dark:border-orange-900/30' },
    'yellow': { bg: 'bg-yellow-600', light: 'bg-yellow-50 dark:bg-yellow-900/10', text: 'text-yellow-700 dark:text-yellow-400', border: 'border-yellow-200 dark:border-yellow-900/30' },
    'blue': { bg: 'bg-blue-600', light: 'bg-blue-50 dark:bg-blue-900/10', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-900/30' }
  };

  const colors = priorityColors[action.priorityColor] || priorityColors.yellow;

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Action Analysis</h3>
        <button 
          onClick={onClose}
          className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition"
        >
          <i className="fa-solid fa-xmark text-gray-600 dark:text-slate-400"></i>
        </button>
      </div>
      
      <div className={`mb-6 p-4 ${colors.light} rounded-xl border ${colors.border}`}>
        <div className="flex items-center gap-2 mb-3">
          <span className={`px-3 py-1 ${colors.bg} text-white text-[10px] rounded-lg font-bold tracking-wider`}>{action.priority}</span>
          <span className="text-xs text-gray-500 dark:text-slate-500 font-medium">{action.actionId}</span>
        </div>
        <h4 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-4">{action.title}</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold mb-0.5 tracking-tight">Due Date</p>
            <p className="text-gray-900 dark:text-slate-100 font-bold">{action.due}</p>
          </div>
          <div>
            <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold mb-0.5 tracking-tight">Status</p>
            <p className="text-gray-900 dark:text-slate-100 font-bold">{action.status}</p>
          </div>
          <div>
            <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold mb-0.5 tracking-tight">Category</p>
            <p className="text-gray-900 dark:text-slate-100 font-bold">{action.category}</p>
          </div>
          <div>
            <p className="text-[10px] text-gray-500 dark:text-slate-500 font-bold mb-0.5 tracking-tight">Assignee</p>
            <p className="text-gray-900 dark:text-slate-100 font-bold">{action.assignee}</p>
          </div>
        </div>
      </div>
      
      <div className="mb-6">
        <h5 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-3">Description</h5>
        <p className="text-sm text-gray-600 dark:text-slate-400 leading-relaxed">{action.description}</p>
      </div>
      
      <div className="mb-6 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10 rounded-xl border border-blue-200 dark:border-blue-900/30">
        <h5 className="font-bold text-gray-900 dark:text-slate-100 mb-2 flex items-center gap-2">
          <i className="fa-solid fa-chart-simple text-blue-600 dark:text-blue-400"></i>
          Impact Assessment
        </h5>
        <p className="text-sm text-gray-700 dark:text-slate-300 font-medium italic">"{action.impact}"</p>
      </div>
      
      <div className="mb-6">
        <h5 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-3 tracking-wider">Action Steps</h5>
        <div className="space-y-2">
          {action.steps.map((step, index) => (
            <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-gray-100 dark:border-slate-800 transition-all hover:border-blue-200 dark:hover:border-blue-900/30">
              <div className="w-6 h-6 bg-brand text-white rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 dark:bg-gray-600">
                {index + 1}
              </div>
              <p className="text-sm text-gray-700 dark:text-slate-300 font-medium">{step}</p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mb-5">
        <h5 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-3">Related Actions</h5>
        <div className="space-y-2">
          {action.relatedActions.map((relatedAction, idx) => (
            <div key={idx} className="p-3 bg-gray-50 dark:bg-slate-800/50 rounded-lg text-xs text-gray-700 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800 transition cursor-pointer flex items-center gap-2 border border-transparent hover:border-gray-200 dark:hover:border-slate-700">
              <i className="fa-solid fa-link text-blue-500"></i>
              {relatedAction}
            </div>
          ))}
        </div>
      </div>
      
      <div className="mb-5 p-4 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-200 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600 dark:text-slate-400 font-bold tracking-widest">Timeline Status</span>
          <span className={`text-sm font-bold ${colors.text}`}>{action.timeline}</span>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <button className={`flex-1 px-4 py-3 ${colors.bg} text-white rounded-xl font-bold hover:opacity-90 transition shadow-lg active:scale-95 flex items-center justify-center gap-2`}>
          <i className="fa-solid fa-check"></i>
          Mark Complete
        </button>
        <button className="w-12 h-12 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-xl text-gray-700 dark:text-slate-300 transition flex items-center justify-center border border-gray-200 dark:border-slate-700 active:scale-95">
          <i className="fa-solid fa-edit"></i>
        </button>
        <button className="w-12 h-12 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-xl text-gray-700 dark:text-slate-300 transition flex items-center justify-center border border-gray-200 dark:border-slate-700 active:scale-95">
          <i className="fa-solid fa-share"></i>
        </button>
      </div>
    </motion.div>
  );
};

export default ActionDetail;
