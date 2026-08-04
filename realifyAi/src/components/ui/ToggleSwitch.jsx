import React from 'react';

const ToggleSwitch = ({ isOn, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      className={`relative w-11 h-6 rounded-full transition-colors duration-200 outline-none focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:ring-offset-2 ${
        isOn ? 'bg-brand dark:bg-gray-600' : 'bg-gray-300 dark:bg-slate-700'
      }`}
    >
      <div
        className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform duration-200 ${
          isOn ? 'translate-x-5' : 'translate-x-0'
        }`}
      ></div>
    </button>
  );
};

export default ToggleSwitch;
