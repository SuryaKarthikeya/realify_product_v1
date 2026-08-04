import React, { useState } from 'react';
import ToggleSwitch from '@/components/ui/ToggleSwitch';

const NotificationsTab = ({ onInputChange }) => {
  const [settings, setSettings] = useState({
    push: true,
    email: true,
    digest: true,
    price: true,
    inventory: true,
    margin: true,
    actions: true
  });

  const handleToggle = (key) => {
    setSettings({ ...settings, [key]: !settings[key] });
    onInputChange();
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm">
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Notifications</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Control how and when you receive alerts from Realify Agent</p>
      </div>

      <div className="p-6 space-y-5">
        {/* Delivery Channels */}
        <section>
          <h4 className="text-xs font-bold text-gray-400 dark:text-slate-500 tracking-wider mb-4">Notification Channels</h4>
          <div className="space-y-3">
            {[
              { id: 'push', title: 'Push Notifications', sub: 'Real-time browser and mobile alerts' },
              { id: 'email', title: 'Email Alerts', sub: 'Important system and security updates' },
              { id: 'digest', title: 'Daily AI Digest', sub: 'A 24-hour summary of your store performance' },
            ].map((item) => (
              <div key={item.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 rounded-2xl">
                <div>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.title}</p>
                  <p className="text-xs text-gray-500 dark:text-slate-500">{item.sub}</p>
                </div>
                <ToggleSwitch isOn={settings[item.id]} onToggle={() => handleToggle(item.id)} />
              </div>
            ))}
          </div>
        </section>

        {/* Alert Types */}
        <section className="pt-5 border-t border-gray-100 dark:border-slate-800">
          <h4 className="text-xs font-bold text-gray-400 dark:text-slate-500 tracking-wider mb-4">Alert Preferences</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { id: 'price', title: 'Price & Buy Box Shifts' },
              { id: 'inventory', title: 'Inventory & Stock Alerts' },
              { id: 'margin', title: 'Margin Decay Alerts' },
              { id: 'actions', title: 'Agent Actions Required' },
            ].map((item) => (
              <div key={item.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 rounded-2xl">
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.title}</p>
                <ToggleSwitch isOn={settings[item.id]} onToggle={() => handleToggle(item.id)} />
              </div>
            ))}
          </div>
        </section>

        {/* Digest Schedule */}
        <section className="pt-5 border-t border-gray-100 dark:border-slate-800">
          <h4 className="text-xs font-bold text-gray-400 dark:text-slate-500 tracking-wider mb-4">Digest Schedule</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 dark:text-slate-500 mb-2">Frequency</label>
              <select 
                onChange={onInputChange}
                className="w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-bold dark:text-slate-300"
              >
                <option>Daily</option>
                <option>Twice Daily</option>
                <option>Weekly</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 dark:text-slate-500 mb-2">Preferred Time</label>
              <select 
                onChange={onInputChange}
                className="w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-bold dark:text-slate-300"
              >
                <option>7:00 AM</option>
                <option selected>8:00 AM</option>
                <option>9:00 AM</option>
                <option>6:00 PM</option>
              </select>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default NotificationsTab;
