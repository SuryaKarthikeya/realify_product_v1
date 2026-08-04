import React, { useState, useRef } from 'react';
import Modal from '@/components/overlays/Modal';

const KPISelectorModal = ({ isOpen, onClose, allKpis, selectedIndices, onSave }) => {
  const [selected, setSelected] = useState(selectedIndices);
  const [error, setError] = useState('');
  const [displayOrder, setDisplayOrder] = useState(() => allKpis.map((_, i) => i));
  const [draggingKpiIdx, setDraggingKpiIdx] = useState(null);
  const dragPosRef = useRef(null);

  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  const [prevSelectedIndices, setPrevSelectedIndices] = useState(selectedIndices);
  if (isOpen !== prevIsOpen || selectedIndices !== prevSelectedIndices) {
    setPrevIsOpen(isOpen);
    setPrevSelectedIndices(selectedIndices);
    if (isOpen) {
      setSelected(selectedIndices);
      const unselected = allKpis.map((_, i) => i).filter(i => !selectedIndices.includes(i));
      setDisplayOrder([...selectedIndices, ...unselected]);
      setError('');
    }
  }

  const toggle = (idx) => {
    if (selected.includes(idx)) {
      setSelected(selected.filter(i => i !== idx));
      setError('');
    } else {
      if (selected.length >= 6) {
        setError("Only 6 KPIs allowed to display at a time.");
        return;
      }
      setSelected([...selected, idx]);
      setError('');
    }
  };

  const handleDragStart = (e, pos, kpiIdx) => {
    dragPosRef.current = pos;
    setDraggingKpiIdx(kpiIdx);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, pos) => {
    e.preventDefault();
    const from = dragPosRef.current;
    if (from === null || from === pos) return;
    setDisplayOrder(prev => {
      const next = [...prev];
      const [removed] = next.splice(from, 1);
      next.splice(pos, 0, removed);
      return next;
    });
    dragPosRef.current = pos;
  };

  const handleDragEnd = () => {
    dragPosRef.current = null;
    setDraggingKpiIdx(null);
  };

  const handleSave = () => {
    if (selected.length < 6) {
      setError("Please select at least 6 KPIs.");
      return;
    }
    onSave(displayOrder.filter(i => selected.includes(i)));
    onClose();
  };

  const handleClose = () => {
    setSelected(selectedIndices);
    const unselected = allKpis.map((_, i) => i).filter(i => !selectedIndices.includes(i));
    setDisplayOrder([...selectedIndices, ...unselected]);
    setError('');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose}>
      <div
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-md border border-gray-100 dark:border-slate-800"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 pt-5 pb-4 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900 dark:text-slate-100 text-lg">Select KPIs to Display</h3>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Choose 6 KPIs to display · <span className={`font-semibold ${selected.length === 6 ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-slate-100'}`}>{selected.length}/6 selected</span></p>
          </div>
          <button onClick={handleClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition">
            <i className="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        {/* KPI List */}
        <div className="px-4 py-3 max-h-[55vh] overflow-y-auto custom-scrollbar space-y-1.5">
          {displayOrder.map((kpiIdx, pos) => {
            const kpi = allKpis[kpiIdx];
            const isChecked = selected.includes(kpiIdx);
            const isDragging = kpiIdx === draggingKpiIdx;
            return (
              <div
                key={kpiIdx}
                draggable
                onDragStart={e => handleDragStart(e, pos, kpiIdx)}
                onDragOver={e => handleDragOver(e, pos)}
                onDragEnd={handleDragEnd}
                className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all select-none ${
                  isDragging ? 'opacity-40 scale-[0.98]' : ''
                } ${
                  isChecked
                    ? 'bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700'
                    : 'hover:bg-gray-50 dark:hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                {/* Grip handle */}
                <div className="flex-shrink-0 cursor-grab active:cursor-grabbing text-gray-300 dark:text-slate-600 hover:text-gray-400 dark:hover:text-slate-500 transition-colors">
                  <i className="fa-solid fa-grip-vertical text-sm" />
                </div>
                {/* Checkbox */}
                <div
                  onClick={() => toggle(kpiIdx)}
                  className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 border-2 transition-all cursor-pointer ${
                    isChecked
                      ? 'bg-gray-900 dark:bg-slate-100 border-gray-900 dark:border-slate-100'
                      : 'border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-900'
                  }`}
                >
                  {isChecked && <i className="fa-solid fa-check text-white dark:text-gray-900 text-[9px]" />}
                </div>
                {/* KPI info */}
                <div className="flex-1 min-w-0 cursor-pointer" onClick={() => toggle(kpiIdx)}>
                  <div className="font-semibold text-sm text-gray-900 dark:text-slate-100 leading-tight">{kpi.title}</div>
                  {(kpi.subtext || kpi.change) && (
                    <div className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">{kpi.subtext || kpi.change}</div>
                  )}
                </div>
                {/* Value */}
                <div className="flex flex-col items-end flex-shrink-0">
                  <span className="text-sm font-bold text-gray-800 dark:text-slate-200">{kpi.value}</span>
                  <span className={`text-[11px] font-semibold ${kpi.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>{kpi.change}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-4 mb-2 px-3 py-2 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-xl flex items-center gap-2">
            <i className="fa-solid fa-circle-exclamation text-red-500 text-xs flex-shrink-0"></i>
            <p className="text-xs text-red-600 dark:text-red-400 font-medium">{error}</p>
          </div>
        )}

        {/* Footer */}
        <div className="px-4 pb-5 pt-3 border-t border-gray-100 dark:border-slate-800 flex gap-3">
          <button
            onClick={handleSave}
            className="flex-1 py-3 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-xl font-bold text-sm hover:bg-gray-700 dark:hover:bg-slate-200 transition active:scale-95 shadow-sm"
          >
            Save
          </button>
          <button
            onClick={handleClose}
            className="flex-1 py-3 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-xl font-bold text-sm hover:bg-gray-200 dark:hover:bg-slate-700 transition"
          >
            Cancel
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default KPISelectorModal;
