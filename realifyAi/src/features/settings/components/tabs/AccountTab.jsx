import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ToggleSwitch from '@/components/ui/ToggleSwitch';
import { useAuthStore } from '@/store/useAuthStore';
import Button from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';

const AccountTab = ({ onInputChange }) => {
  const [is2FA, setIs2FA] = useState(false);
  const { logout } = useAuthStore();
  const navigate = useNavigate();

  const handleToggle2FA = () => {
    setIs2FA(!is2FA);
    onInputChange();
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <>
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Account Settings</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Personal details and security</p>
      </div>
      
      <div className="p-6 space-y-6">
        {/* Profile Photo */}
        <div className="flex items-center gap-6 pb-6 border-b border-gray-100 dark:border-slate-800">
          <div className="w-24 h-24 rounded-2xl bg-slate-800 dark:bg-slate-700 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0 shadow-lg">
            R
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-slate-100">Profile Photo</h4>
            <p className="text-sm text-gray-500 dark:text-slate-400 mb-3">JPG or PNG. Max 2MB.</p>
            <div className="flex gap-2">
              <Button variant="primary" size="sm">Upload New</Button>
              <button className="px-4 py-2 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors active:scale-95">
                Remove
              </button>
            </div>
          </div>
        </div>

        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Full Name</label>
            <Input type="text" defaultValue="Rachel Morgan" onChange={onInputChange} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Email Address</label>
            <Input type="email" defaultValue="rachel@acmepets.com" onChange={onInputChange} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Timezone</label>
            <Select onChange={onInputChange}>
              <option>America/New_York (EST)</option>
              <option>India Standard Time (IST)</option>
              <option>Europe/London (GMT)</option>
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Language</label>
            <Select onChange={onInputChange}>
              <option>English</option>
              <option>Hindi</option>
            </Select>
          </div>
        </div>

        {/* Security Section */}
        <div className="pt-6 border-t border-gray-100 dark:border-slate-800">
          <h4 className="font-semibold text-gray-900 dark:text-slate-100 mb-4">Security</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-800/40 rounded-2xl border border-gray-100 dark:border-slate-800">
              <div>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Password</p>
                <p className="text-xs text-gray-500 dark:text-slate-400">Last changed 45 days ago</p>
              </div>
              <button className="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 transition-colors shadow-sm">
                Change Password
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-800/40 rounded-2xl border border-gray-100 dark:border-slate-800">
              <div>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Two-Factor Authentication</p>
                <p className="text-xs text-gray-500 dark:text-slate-400">Authenticator app or SMS</p>
              </div>
              <ToggleSwitch isOn={is2FA} onToggle={handleToggle2FA} />
            </div>

            <div className="flex items-center justify-between p-4 bg-red-50 dark:bg-red-900/10 rounded-2xl border border-red-100 dark:border-red-900/30">
              <div>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Sign Out</p>
                <p className="text-xs text-gray-500 dark:text-slate-400">Log out of your account on this device</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-bold transition-colors shadow-sm active:scale-95"
              >
                Log Out
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-800/40 rounded-2xl border border-gray-100 dark:border-slate-800">
              <div>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Active Sessions</p>
                <p className="text-xs text-gray-500 dark:text-slate-400">3 devices currently active</p>
              </div>
              <button className="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 transition-colors shadow-sm">
                Manage Sessions
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AccountTab;
