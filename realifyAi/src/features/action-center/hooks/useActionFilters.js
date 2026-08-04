import { useState, useMemo } from 'react';
import { actionItems } from '@/features/action-center/data/actionsData';

/**
 * There is deliberately no SKU or Category filter here — the table always
 * loads every action across every SKU and category. Only priority, status and
 * free-text search narrow the list, and all three start wide open.
 */
const NO_FILTERS = { priority: 'all', status: 'all' };

export const useActionFilters = () => {
  const [activeTab, setActiveTab] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState(NO_FILTERS);

  const filteredActions = useMemo(() => {
    return actionItems.filter(item => {
      const priorityMatch = filters.priority === 'all' || item.priority.toLowerCase() === filters.priority;
      const statusMatch = filters.status === 'all' || item.status.toLowerCase() === filters.status;
      const tabMatch = activeTab.toLowerCase() === 'all' || item.priority.toLowerCase() === activeTab.toLowerCase();
      const searchMatch = searchQuery === '' ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.skuCode || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.category || '').toLowerCase().includes(searchQuery.toLowerCase());

      return priorityMatch && statusMatch && tabMatch && searchMatch;
    });
  }, [filters, activeTab, searchQuery]);

  const resetFilters = () => {
    setFilters(NO_FILTERS);
    setSearchQuery('');
    setActiveTab('All');
  };

  return {
    activeTab,
    setActiveTab,
    searchQuery,
    setSearchQuery,
    filters,
    setFilters,
    filteredActions,
    resetFilters,
  };
};
