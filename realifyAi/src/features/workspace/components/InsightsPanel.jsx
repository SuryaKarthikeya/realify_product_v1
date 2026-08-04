import React from 'react';
import SignalsTable from '@/features/workspace/components/SignalsTable';
import FilterBar from '@/features/workspace/components/FilterBar';
import {
  matchesChannel,
  matchesCategory,
  matchesStatus,
} from '@/features/workspace/signalFilters';
import { useWorkspaceFilterStore } from '@/store/useWorkspaceFilterStore';
import { SIGNALS_BY_TAB } from '@/data/insightsData';
import { DEFAULT_DOMAIN, toDomainKey } from '@/features/workspace/workspaceRoutes';

/**
 * Actions panel — a single flat table of every action for the active module.
 *
 * No SKU/Category view toggle and no grouping: the table always loads all
 * SKUs and all categories, ranked by score. The filters in FilterBar are the
 * only way to narrow it, and they all default to "All".
 */
const InsightsPanel = ({
  domain = DEFAULT_DOMAIN,
  onOpenSimulateModal,
  onOpenTakeActionModal,
  onSelectInsight,
  expandedInsightId,
  isCollapsed = false,
}) => {
  // Connected to session-persistent filter store
  const {
    marketplace,
    categoryCut,
    priceBand,
    priority,
    statusFilter,
    executedSignalIds,
    markSignalExecuted,
  } = useWorkspaceFilterStore();

  const handleTakeAction = (signal) => {
    markSignalExecuted(signal.id);
    if (onOpenTakeActionModal) {
      onOpenTakeActionModal(signal);
    }
  };

  const tabKey = toDomainKey(domain);
  const rawSignals = SIGNALS_BY_TAB[tabKey] || SIGNALS_BY_TAB.sales;

  // Filter signals based on exposure guardrail (>= 1,000) AND active filters
  const filteredSignals = rawSignals.filter((s) => {
    if ((s.exposure || 0) < 1000) return false;

    // Channel / category / status are multi-select — see signalFilters.js.
    if (!matchesChannel(s, marketplace)) return false;
    if (!matchesCategory(s, categoryCut)) return false;
    if (!matchesStatus(s, statusFilter, executedSignalIds)) return false;

    // Priority Filter
    if (priority !== 'all' && s.priority !== priority) return false;

    // Price Band Filter
    if (priceBand === 'under1000' && (s.exposure || 0) >= 100000) return false;
    if (priceBand === 'above5000' && (s.exposure || 0) < 500000) return false;

    return true;
  });

  // Sort signals by Score descending (Prioritization Formula)
  const sortedSignals = [...filteredSignals].sort((a, b) => (b.score || 0) - (a.score || 0));

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 shadow-card dark:shadow-none rounded-xl overflow-hidden flex flex-col h-full font-sans">

      {/* ── 1. Header & Filter Bar ── */}
      <div className={`flex-shrink-0 bg-white dark:bg-slate-900 px-4 py-3 border-b border-gray-100 dark:border-slate-800 flex flex-col gap-2.5 ${
        isCollapsed ? '' : 'lg:flex-row lg:items-center lg:justify-between'
      }`}>

        <div className="flex items-baseline gap-2 flex-shrink-0">
          <h3 className="text-[20px] font-bold text-gray-900 dark:text-slate-100 tracking-tight">
            Actions
          </h3>
          <span className="font-mono text-[11.5px] text-gray-400 dark:text-slate-500">
            · {sortedSignals.length} signals
          </span>
        </div>

        {/* Signal Filters Bar */}
        <FilterBar isCollapsed={isCollapsed} />

      </div>

      {/* ── 2. Scrollable actions table — all signals, flat ── */}
      <div className="flex-1 overflow-y-auto custom-scrollbar bg-white dark:bg-slate-900">
        {sortedSignals.length === 0 ? (
          <div className="py-8 text-center text-xs text-gray-400 dark:text-slate-500 font-mono">
            No signals match active filters. Try adjusting your search or resetting filters.
          </div>
        ) : (
          <SignalsTable
            signals={sortedSignals}
            selectedId={expandedInsightId}
            onSelect={onSelectInsight}
            onSimulate={onOpenSimulateModal}
            onTakeAction={handleTakeAction}
            isCollapsed={isCollapsed}
            executedSignalIds={executedSignalIds}
          />
        )}
      </div>
    </div>
  );
};

export default React.memo(InsightsPanel);
