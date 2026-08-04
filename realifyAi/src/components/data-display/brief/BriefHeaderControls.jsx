import React, { useState, useRef } from 'react';
import useClickOutside from '@/hooks/useClickOutside';

/* ── Available Channel Platforms ── */
const AVAILABLE_CHANNELS = [
  { id: 'shopify', name: 'Shopify', icon: 'fa-brands fa-shopify', color: 'text-emerald-500' },
  { id: 'amazon', name: 'Amazon', icon: 'fa-brands fa-amazon', color: 'text-amber-500' },
];

/* ── Mini Calendar Popover for Custom Date Selection (SS2) ── */
const CalendarPicker = ({ selectedDate, onSelectDate, onClose, alignRight = false }) => {
  const [currentDate, setCurrentDate] = useState(() => {
    if (selectedDate && !isNaN(new Date(selectedDate).getTime())) {
      return new Date(selectedDate);
    }
    return new Date();
  });

  const month = currentDate.getMonth();
  const year = currentDate.getFullYear();

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, month, 1).getDay();

  const daysGrid = [];
  const prevMonthDays = new Date(year, month, 0).getDate();

  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    daysGrid.push({ day: prevMonthDays - i, currentMonth: false });
  }

  for (let d = 1; d <= daysInMonth; d++) {
    daysGrid.push({ day: d, currentMonth: true });
  }

  const remaining = 35 - daysGrid.length;
  for (let d = 1; d <= (remaining > 0 ? remaining : 0); d++) {
    daysGrid.push({ day: d, currentMonth: false });
  }

  return (
    <div className={`absolute ${alignRight ? 'right-0 left-auto' : 'left-0'} top-full mt-1.5 w-64 bg-white dark:bg-slate-900 border border-gray-300 dark:border-slate-700 rounded-xl shadow-2xl z-[100] p-3 text-gray-900 dark:text-slate-100`}>
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-1">
          <span className="text-sm font-bold">{monthNames[month]} {year}</span>
          <i className="fa-solid fa-caret-down text-xs text-gray-500" />
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handlePrevMonth} className="p-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded text-gray-600 dark:text-slate-300">
            <i className="fa-solid fa-arrow-up text-xs" />
          </button>
          <button onClick={handleNextMonth} className="p-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded text-gray-600 dark:text-slate-300">
            <i className="fa-solid fa-arrow-down text-xs" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 text-center text-xs font-semibold text-gray-600 dark:text-slate-400 mb-1">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((d, i) => (
          <div key={i} className="py-1">{d}</div>
        ))}
      </div>

      <div className="grid grid-cols-7 text-center text-xs gap-y-1">
        {daysGrid.map((item, idx) => {
          const isSelected = item.currentMonth && selectedDate && new Date(selectedDate).getDate() === item.day && new Date(selectedDate).getMonth() === month && new Date(selectedDate).getFullYear() === year;
          const isToday = item.currentMonth && new Date().getDate() === item.day && new Date().getMonth() === month && new Date().getFullYear() === year;

          return (
            <button
              key={idx}
              disabled={!item.currentMonth}
              onClick={() => {
                if (item.currentMonth) {
                  const formatted = `${year}-${String(month + 1).padStart(2, '0')}-${String(item.day).padStart(2, '0')}`;
                  onSelectDate(formatted);
                  onClose();
                }
              }}
              className={`h-7 w-7 mx-auto flex items-center justify-center rounded-lg font-medium transition-all ${!item.currentMonth
                ? 'text-gray-300 dark:text-slate-600 cursor-not-allowed'
                : isSelected
                  ? 'bg-blue-600 text-white font-bold shadow-xs'
                  : isToday
                    ? 'border border-blue-500 text-blue-600 dark:text-blue-400 font-bold'
                    : 'text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800'
                }`}
            >
              {item.day}
            </button>
          );
        })}
      </div>

      <div className="mt-3 pt-2 border-t border-gray-100 dark:border-slate-800 flex items-center justify-between text-xs font-semibold">
        <button
          onClick={() => {
            onSelectDate('');
            onClose();
          }}
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          Clear
        </button>
        <button
          onClick={() => {
            const today = new Date();
            const formatted = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
            onSelectDate(formatted);
            onClose();
          }}
          className="text-gray-600 dark:text-slate-400 hover:underline"
        >
          Today
        </button>
      </div>
    </div>
  );
};

const BriefHeaderControls = ({ onDashboardToggle, isDashboardViewActive, isKpiVisible, onKpiToggle }) => {
  // Channel state
  const [channelOpen, setChannelOpen] = useState(false);
  const [selectedChannels, setSelectedChannels] = useState(['shopify', 'amazon']);
  const [pendingSelected, setPendingSelected] = useState(['shopify', 'amazon']);

  const channelBtnRef = useRef(null);
  const channelPanelRef = useRef(null);
  useClickOutside(channelPanelRef, channelOpen, () => setChannelOpen(false), channelBtnRef);

  // Date state
  const [dateOpen, setDateOpen] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState('30d');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [activeCalTarget, setActiveCalTarget] = useState(null);

  const dateBtnRef = useRef(null);
  const datePanelRef = useRef(null);
  useClickOutside(datePanelRef, dateOpen, () => { setDateOpen(false); setActiveCalTarget(null); }, dateBtnRef);

  const handleOpenChannels = () => {
    setPendingSelected([...selectedChannels]);
    setChannelOpen(o => !o);
  };

  const handleTogglePending = (id) => {
    if (pendingSelected.includes(id)) {
      setPendingSelected(pendingSelected.filter(c => c !== id));
    } else {
      setPendingSelected([...pendingSelected, id]);
    }
  };

  const handleSelectAll = () => {
    if (pendingSelected.length === AVAILABLE_CHANNELS.length) {
      setPendingSelected([]);
    } else {
      setPendingSelected(AVAILABLE_CHANNELS.map(c => c.id));
    }
  };

  const handleApplyChannels = () => {
    setSelectedChannels([...pendingSelected]);
    setChannelOpen(false);
  };

  /* Closed State Button Content (SS3 & SS4 specifications) */
  const renderClosedStateButton = () => {
    const count = selectedChannels.length;
    const total = AVAILABLE_CHANNELS.length;

    // Case 1: Only 1 channel selected
    if (count === 1) {
      const singleChannel = AVAILABLE_CHANNELS.find(c => c.id === selectedChannels[0]) || AVAILABLE_CHANNELS[0];
      return (
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-md bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 flex items-center justify-center text-xs">
            <i className={`${singleChannel.icon} ${singleChannel.color}`} />
          </div>
          <span className="text-[14px] font-semibold text-gray-900 dark:text-slate-100">{singleChannel.name}</span>
          <i className="fa-solid fa-chevron-down text-[9px] text-gray-400" />
        </div>
      );
    }

    // Case 3: All channels selected
    if (count === total || count === 0) {
      return (
        <div className="flex items-center gap-2">
          <div className="w-5.5 h-5.5 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xs">
            {/* <i className="fa-solid fa-house text-[11px]" /> */}
          </div>
          <span className="text-[14px] font-bold text-gray-900 dark:text-slate-100">Channels ({total})</span>
          <i className="fa-solid fa-chevron-down text-[9px] text-gray-400" />
        </div>
      );
    }

    // Case 2: Multiple channels selected (> 1 and < total)
    return (
      <div className="flex items-center gap-2">
        <div className="w-5.5 h-5.5 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xs">
          <i className="fa-solid fa-house text-[11px]" />
        </div>
        <span className="text-[14px] font-bold text-gray-900 dark:text-slate-100">{count} stores selected</span>
        <i className="fa-solid fa-chevron-down text-[9px] text-gray-400" />
      </div>
    );
  };

  return (
    <div className="flex items-center gap-2.5">

      {/* ── Channel Dropdown (SS3 & SS4) ── */}
      <div className="relative" ref={channelPanelRef}>
        <button
          ref={channelBtnRef}
          onClick={handleOpenChannels}
          className="flex items-center justify-center h-8 px-3 bg-[#f0f4f8] dark:bg-slate-800/90 hover:bg-[#e4ebf3] dark:hover:bg-slate-700/90 rounded-2xl transition-all border border-transparent shadow-2xs"
        >
          {renderClosedStateButton()}
        </button>

        {/* Dropdown Content Popover */}
        {channelOpen && (
          <div className="absolute right-0 top-full mt-1.5 w-60 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-3xl shadow-2xl z-[100] p-4 space-y-3 animate-in fade-in zoom-in-95 duration-200">

            {/* Header with SELECT ALL checkbox */}
            <div
              onClick={handleSelectAll}
              className="flex items-center gap-2 cursor-pointer select-none"
            >
              <span className="w-4 flex-shrink-0 text-gray-900 dark:text-white">
                {pendingSelected.length === AVAILABLE_CHANNELS.length && (
                  <i className="fa-solid fa-check text-[11px]" />
                )}
              </span>
              <span className="text-[11px] font-sans font-bold tracking-wider uppercase text-gray-600 dark:text-slate-400">
                SELECT ALL • {AVAILABLE_CHANNELS.length}
              </span>
            </div>

            <hr className="border-dashed border-gray-200 dark:border-slate-800" />

            {/* Scrollable list of channels */}
            <div className="max-h-48 overflow-y-auto scrollbar-thin space-y-1.5 pr-1">
              {AVAILABLE_CHANNELS.map(ch => {
                const isChecked = pendingSelected.includes(ch.id);
                return (
                  <div
                    key={ch.id}
                    onClick={() => handleTogglePending(ch.id)}
                    className="flex items-center gap-2.5 p-1.5 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-800/60 cursor-pointer transition-colors"
                  >
                    <span className="w-4 flex-shrink-0 text-gray-900 dark:text-white">
                      {isChecked && <i className="fa-solid fa-check text-[11px]" />}
                    </span>
                    <span className="text-xs font-semibold text-gray-800 dark:text-slate-200">
                      {ch.name}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Fixed Apply Button */}
            <div className="pt-2 border-t border-gray-100 dark:border-slate-800 flex justify-end">
              <button
                onClick={handleApplyChannels}
                className="px-5 py-1.5 bg-[#0c101a] hover:bg-[#1a202c] dark:bg-slate-100 dark:hover:bg-white dark:text-gray-900 text-white rounded-xl text-xs font-bold transition-all shadow-xs"
              >
                Apply
              </button>
            </div>

          </div>
        )}
      </div>

      {/* ── Date Picker Dropdown ── */}
      <div className="relative" ref={datePanelRef}>
        <button
          ref={dateBtnRef}
          onClick={() => {
            setDateOpen(o => !o);
            setActiveCalTarget(null);
          }}
          className="flex items-center gap-1.5 h-8 px-3 bg-slate-100/90 dark:bg-slate-800/90 hover:bg-slate-200/90 dark:hover:bg-slate-700/90 rounded-full text-[14px] font-semibold text-gray-700 dark:text-slate-200 transition-colors border border-transparent shadow-xs"
        >
          <span>
            {selectedPreset === '7d' ? '7D' : selectedPreset === '60d' ? '60D' : '30D'}
          </span>
          <i className="fa-solid fa-chevron-down text-[9px] text-gray-400" />
        </button>

        {dateOpen && (
          <div className="absolute right-0 top-full mt-1.5 w-72 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-xl z-[100] p-4 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-slate-500 mb-2">Preset Ranges</p>
              <div className="grid grid-cols-3 gap-2">
                {['7d', '30d', '60d'].map(preset => (
                  <button
                    key={preset}
                    onClick={() => {
                      setSelectedPreset(preset);
                      setDateOpen(false);
                      setActiveCalTarget(null);
                    }}
                    className={`py-1.5 rounded-xl text-xs font-bold transition-colors ${selectedPreset === preset
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-700'
                      }`}
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            <hr className="border-gray-100 dark:border-slate-800" />

            <div className="relative">
              <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-slate-500 mb-1.5">Custom Date Range</p>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="relative">
                  <label className="text-[9px] font-bold uppercase text-gray-400 dark:text-slate-500 mb-1 block">Start Date</label>
                  <div
                    onClick={() => setActiveCalTarget(activeCalTarget === 'start' ? null : 'start')}
                    className="relative cursor-pointer"
                  >
                    <input
                      type="text"
                      readOnly
                      placeholder="dd/mm/yyyy"
                      value={startDate}
                      className="w-full pl-2.5 pr-7 py-1.5 text-xs bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none text-gray-800 dark:text-slate-200 font-medium cursor-pointer"
                    />
                    <i className="fa-regular fa-calendar absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none" />
                  </div>

                  {activeCalTarget === 'start' && (
                    <CalendarPicker
                      selectedDate={startDate}
                      onSelectDate={(d) => setStartDate(d)}
                      onClose={() => setActiveCalTarget(null)}
                    />
                  )}
                </div>

                <div className="relative">
                  <label className="text-[9px] font-bold uppercase text-gray-400 dark:text-slate-500 mb-1 block">End Date</label>
                  <div
                    onClick={() => setActiveCalTarget(activeCalTarget === 'end' ? null : 'end')}
                    className="relative cursor-pointer"
                  >
                    <input
                      type="text"
                      readOnly
                      placeholder="dd/mm/yyyy"
                      value={endDate}
                      className="w-full pl-2.5 pr-7 py-1.5 text-xs bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none text-gray-800 dark:text-slate-200 font-medium cursor-pointer"
                    />
                    <i className="fa-regular fa-calendar absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none" />
                  </div>

                  {activeCalTarget === 'end' && (
                    <CalendarPicker
                      selectedDate={endDate}
                      onSelectDate={(d) => setEndDate(d)}
                      onClose={() => setActiveCalTarget(null)}
                      alignRight={true}
                    />
                  )}
                </div>
              </div>

              {(startDate || endDate) && (
                <button
                  onClick={() => {
                    setSelectedPreset('custom');
                    setDateOpen(false);
                    setActiveCalTarget(null);
                  }}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors"
                >
                  Apply Custom Range
                </button>
              )}
            </div>
          </div>
        )}
      </div>


      {/* ── Dashboard View Toggle ── */}
      {onDashboardToggle && (
        <>
          <div className="h-4 w-px bg-gray-200 dark:bg-slate-700 hidden md:block mx-1"></div>
          <div className="hidden md:flex items-center gap-2">
            <span className="text-[14px] font-semibold text-gray-900 dark:text-slate-100 whitespace-nowrap">
              Dashboard
            </span>
            <button
              onClick={onDashboardToggle}
              className={`relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full transition-colors ${isDashboardViewActive
                ? 'bg-gray-900 dark:bg-slate-100 hover:opacity-80'
                : 'bg-gray-300 dark:bg-slate-600 hover:bg-gray-400 dark:hover:bg-slate-500'
                }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-gray-900 transition-transform ${isDashboardViewActive ? 'translate-x-4' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>
        </>
      )}

    </div>
  );
};

export default BriefHeaderControls;
