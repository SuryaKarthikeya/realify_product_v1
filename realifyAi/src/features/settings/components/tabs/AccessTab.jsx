import React from 'react';

const AccessTab = ({ onInputChange, onOpenRoleModal }) => {
  const permissions = [
    { id: 'view_intel', label: 'View Intelligence', owner: true, admin: true, analyst: true, viewer: true },
    { id: 'view_cmd', label: 'View Command Center', owner: true, admin: true, analyst: true, viewer: false },
    { id: 'approve_actions', label: 'Approve Actions', owner: true, admin: true, analyst: false, viewer: false },
    { id: 'use_prompt', label: 'Use CMD Prompt', owner: true, admin: true, analyst: true, viewer: false },
    { id: 'manage_integrations', label: 'Manage Integrations', owner: true, admin: true, analyst: false, viewer: false },
    { id: 'edit_guardrails', label: 'Edit Guardrails', owner: true, admin: true, analyst: false, viewer: false },
    { id: 'edit_settings', label: 'Edit Settings', owner: true, admin: true, analyst: false, viewer: false },
    { id: 'manage_billing', label: 'Manage Billing', owner: true, admin: false, analyst: false, viewer: false },
  ];

  const roles = [
    { id: 'owner', label: 'Owner', locked: true },
    { id: 'admin', label: 'Admin', locked: false },
    { id: 'analyst', label: 'Analyst', locked: false },
    { id: 'viewer', label: 'Viewer', locked: false },
  ];

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Access Management</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Define role-based permissions and custom roles</p>
      </div>

      <div className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-gray-200 dark:border-slate-800">
                <th className="pb-4 pr-4 font-bold text-gray-900 dark:text-slate-100 w-48">Permission</th>
                {roles.map(role => (
                  <th key={role.id} className="pb-4 px-4 font-bold text-center text-gray-900 dark:text-slate-100 w-24">
                    {role.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {permissions.map((perm) => (
                <tr key={perm.id} className="border-b border-gray-50 dark:border-slate-800/50 last:border-0 group hover:bg-gray-50/50 dark:hover:bg-slate-800/30 transition-colors">
                  <td className="py-4 pr-4 font-medium text-gray-700 dark:text-slate-300">
                    {perm.label}
                  </td>
                  {roles.map(role => (
                    <td key={role.id} className="py-4 px-4 text-center">
                      <input 
                        type="checkbox" 
                        defaultChecked={perm[role.id]} 
                        disabled={role.locked}
                        onChange={onInputChange}
                        className={`w-5 h-5 rounded border-gray-300 dark:border-slate-700 text-blue-600 focus:ring-blue-500/20 transition-all ${
                          role.locked ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400'
                        }`}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-5 p-6 bg-gray-50 dark:bg-slate-800/40 rounded-2xl border border-gray-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100">Custom Roles</h4>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Need something specific? Create a custom role with granular permissions.</p>
          </div>
          <button 
            onClick={onOpenRoleModal}
            className="px-4 py-2 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition-all shadow-md active:scale-95"
          >
            <i className="fa-solid fa-plus mr-2"></i>Add Custom Role
          </button>
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-gray-400 dark:text-slate-500 italic">
          <i className="fa-solid fa-lock"></i>
          <span>Owner permissions are locked for security. Changes to other roles require explicit save.</span>
        </div>
      </div>
    </div>
  );
};

export default AccessTab;
