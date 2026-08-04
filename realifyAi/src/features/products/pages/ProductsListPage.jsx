import React, { useState, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import MarketplaceSyncBanner from '@/components/feedback/MarketplaceSyncBanner';
import useClickOutside from '@/hooks/useClickOutside';
import useProductNavigation from '@/hooks/useProductNavigation';
import BriefHeaderControls from '@/components/data-display/brief/BriefHeaderControls';
import ProductDetailModal from '@/features/products/components/ProductDetailModal';
import BriefCard from '@/components/data-display/brief/BriefCard';
import { REALIFY_BRIEF } from '@/data/briefData';
import { CHANNEL_TABS, ALL_PRODUCTS, PAGE_SIZE, CATEGORIES, DEFAULT_COLS, STATUS_OPTIONS, STATUS_STYLES } from '@/features/products/data/productsData';
import BinView from '@/features/products/components/BinView';
import ProductEditView from '@/features/products/components/ProductEditView';

const ProductsListPage = () => {
  const _navigate = useNavigate();
  const { goToProduct: _goToProduct, buildFallbackWatchlistItem: _buildFallbackWatchlistItem, NO_SPECIFIC_INSIGHTS } = useProductNavigation();
  const activePlatforms = useMemo(
    () => JSON.parse(localStorage.getItem('active_platforms') || '["shopify"]'),
    []
  );
  const visibleChannelTabs = useMemo(
    () => CHANNEL_TABS.filter(tab => activePlatforms.includes(tab.toLowerCase())),
    [activePlatforms]
  );

  const [_activeTab, _setActiveTab] = useState(visibleChannelTabs[0] || 'Amazon');
  const [search, setSearch] = useState('');
  const [filterCategory, setFilterCategory] = useState('All');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState(null);
  const [sortDir, setSortDir] = useState('asc');
  const [cols, setCols] = useState(DEFAULT_COLS);
  const [_editMode, setEditMode] = useState(false);
  const [_editItems, setEditItems] = useState([]);
  const [editingRowId, setEditingRowId] = useState(null);
  const [editingRowVals, setEditingRowVals] = useState({});
  const [selectedProductForModal, setSelectedProductForModal] = useState(null);

  // Product data state (mutable for delete/draft)
  const [productsData, setProductsData] = useState(ALL_PRODUCTS);
  const [deletedProducts, setDeletedProducts] = useState([]);
  const [deleteConfirmProduct, setDeleteConfirmProduct] = useState(null);
  const [_showBin, _setShowBin] = useState(false);
  const [_bulkDeletePending, setBulkDeletePending] = useState(false);

  /* ── Unified View Controls panel ── */
  const [viewPanelOpen, setViewPanelOpen] = useState(false);
  const [_viewPanelTab, setViewPanelTab] = useState('filters');
  const [pendingCategory, setPendingCategory] = useState('All');
  const [pendingSortBy, setPendingSortBy] = useState(null);
  const [pendingSortDir, setPendingSortDir] = useState('asc');
  const [pendingCols, setPendingCols] = useState(DEFAULT_COLS);
  const viewPanelRef = useRef(null);

  const _openViewPanel = (tab = 'filters') => {
    setPendingCategory(filterCategory);
    setPendingSortBy(sortBy);
    setPendingSortDir(sortDir);
    setPendingCols(cols.map(c => ({ ...c })));
    setViewPanelTab(tab);
    setViewPanelOpen(true);
  };
  const _applyViewPanel = () => {
    setFilterCategory(pendingCategory);
    setSortBy(pendingSortBy);
    setSortDir(pendingSortDir);
    setCols(pendingCols);
    setPage(1);
    setViewPanelOpen(false);
  };
  const _resetViewPanel = () => {
    setPendingCategory('All');
    setPendingSortBy(null);
    setPendingSortDir('asc');
    setPendingCols(DEFAULT_COLS.map(c => ({ ...c })));
  };
  const _togglePendingColVisible = (key) =>
    setPendingCols(prev => prev.map(c => c.key === key ? { ...c, visible: !c.visible } : c));

  useClickOutside(viewPanelRef, viewPanelOpen, () => setViewPanelOpen(false));

  const filtered = useMemo(() => {
    let list = productsData;
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(p => p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q));
    }
    if (filterCategory !== 'All') list = list.filter(p => p.category === filterCategory);
    return list;
  }, [search, filterCategory, productsData]);

  const sortedFiltered = useMemo(() => {
    if (!sortBy) return filtered;
    return [...filtered].sort((a, b) => {
      let aVal, bVal;
      
      const parseNum = (val) => {
        if (typeof val === 'number') return val;
        if (!val) return 0;
        return parseFloat(val.toString().replace(/[^0-9.-]+/g,"")) || 0;
      };

      if (sortBy === 'name') { aVal = a.name.toLowerCase(); bVal = b.name.toLowerCase(); }
      else if (sortBy === 'category') { aVal = a.category.toLowerCase(); bVal = b.category.toLowerCase(); }
      else if (sortBy === 'inventory') { aVal = a.inventory; bVal = b.inventory; }
      else if (sortBy === 'velocity') { aVal = parseInt(a.velocity) || 0; bVal = parseInt(b.velocity) || 0; }
      else if (sortBy === 'intel') { aVal = a.workspaceLabel.toLowerCase(); bVal = b.workspaceLabel.toLowerCase(); }
      else if (['price', 'cogs', 'margin', 'returns', 'bb'].includes(sortBy)) {
        aVal = parseNum(a[sortBy]);
        bVal = parseNum(b[sortBy]);
      }
      
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filtered, sortBy, sortDir]);

  const totalPages = Math.ceil(sortedFiltered.length / PAGE_SIZE);
  const pageProducts = sortedFiltered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const toggleSelect = (id) => setSelectedIds(prev => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });

  const toggleAll = () => {
    if (selectedIds.size === pageProducts.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(pageProducts.map(p => p.id)));
  };

  const _handleEditClick = () => {
    setEditItems(sortedFiltered.filter(p => selectedIds.has(p.id)).map(p => ({ ...p })));
    setEditMode(true);
  };

  const _handleBulkDelete = () => {
    setBulkDeletePending(true);
  };

  const _confirmBulkDelete = () => {
    const toDelete = productsData.filter(p => selectedIds.has(p.id));
    setProductsData(prev => prev.filter(p => !selectedIds.has(p.id)));
    setDeletedProducts(prev => [...prev, ...toDelete]);
    setSelectedIds(new Set());
    setBulkDeletePending(false);
  };

  const _handleDeleteProduct = (product, e) => {
    e.stopPropagation();
    setDeleteConfirmProduct(product);
  };

  const _confirmDelete = () => {
    setProductsData(prev => prev.filter(p => p.id !== deleteConfirmProduct.id));
    setDeletedProducts(prev => [...prev, deleteConfirmProduct]);
    setSelectedIds(prev => { const next = new Set(prev); next.delete(deleteConfirmProduct.id); return next; });
    setDeleteConfirmProduct(null);
  };

  const _handleRestoreProduct = (productId) => {
    const product = deletedProducts.find(p => p.id === productId);
    if (!product) return;
    setDeletedProducts(prev => prev.filter(p => p.id !== productId));
    setProductsData(prev => [...prev, product]);
  };

  const _handleRestoreMany = (ids) => {
    const idSet = new Set(ids);
    const toRestore = deletedProducts.filter(p => idSet.has(p.id));
    setDeletedProducts(prev => prev.filter(p => !idSet.has(p.id)));
    setProductsData(prev => [...prev, ...toRestore]);
  };

  const _handleDraftRow = (product, e) => {
    e.stopPropagation();
    setProductsData(prev => prev.map(p => p.id === product.id ? { ...p, status: 'Draft' } : p));
  };

  const handleProductClick = (product) => {
    setSelectedProductForModal(product);
  };

  const _startEdit = (e, product) => {
    e.stopPropagation();
    setEditingRowId(product.id);
    setEditingRowVals({ ...product });
  };
  const _cancelEdit = (e) => {
    e.stopPropagation();
    setEditingRowId(null);
    setEditingRowVals({});
  };
  const _saveEdit = (e) => {
    e.stopPropagation();
    setProductsData(prev => prev.map(p => p.id === editingRowId ? { ...p, ...editingRowVals } : p));
    setEditingRowId(null);
    setEditingRowVals({});
  };
  const updateEditVal = (field, value) =>
    setEditingRowVals(prev => ({ ...prev, [field]: value }));

  const _renderEditCell = (colKey) => {
    const curStatus = STATUS_STYLES[editingRowVals.status] || STATUS_STYLES.Active;
    switch (colKey) {
      case 'status': return (
        <td key={colKey} className="px-3 py-3">
          <div className={`inline-flex items-center gap-1.5 pl-2 pr-1 py-1 rounded-full ${curStatus.pill}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${curStatus.dot} flex-shrink-0`} />
            <select value={editingRowVals.status} onChange={e => updateEditVal('status', e.target.value)}
              className="text-xs font-semibold bg-transparent border-none outline-none cursor-pointer appearance-none pr-1" style={{ color: 'inherit' }}>
              {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <i className="fa-solid fa-chevron-down text-[8px] opacity-60 flex-shrink-0" />
          </div>
        </td>
      );
      case 'price': return (
        <td key={colKey} className="px-3 py-3">
          <input type="text" value={editingRowVals.price} onChange={e => updateEditVal('price', e.target.value)}
            className="text-xs font-semibold text-gray-700 dark:text-slate-300 bg-transparent border-b border-gray-300 dark:border-slate-600 focus:border-gray-500 dark:focus:border-slate-400 outline-none w-16 py-0.5" />
        </td>
      );
      case 'category': return (
        <td key={colKey} className="px-3 py-3">
          <div className="inline-flex items-center gap-1 px-2.5 py-1 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800/40 rounded-md">
            <select value={editingRowVals.category} onChange={e => updateEditVal('category', e.target.value)}
              className="text-xs font-medium text-purple-700 dark:text-purple-400 bg-transparent border-none outline-none cursor-pointer appearance-none">
              {CATEGORIES.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <i className="fa-solid fa-chevron-down text-purple-400 text-[8px] flex-shrink-0" />
          </div>
        </td>
      );
      case 'inventory': return (
        <td key={colKey} className="px-3 py-3">
          <input type="number" value={editingRowVals.inventory} onChange={e => updateEditVal('inventory', parseInt(e.target.value) || 0)}
            className="text-xs font-semibold text-gray-700 dark:text-slate-300 bg-transparent border-b border-gray-300 dark:border-slate-600 focus:border-gray-500 dark:focus:border-slate-400 outline-none w-20 py-0.5" />
        </td>
      );
      default:
        return renderCell(editingRowVals, colKey);
    }
  };

  // Cell renderer
  const renderCell = (product, colKey) => {
    const ss = STATUS_STYLES[product.status] || STATUS_STYLES.Active;
    switch (colKey) {
      case 'status': return (
        <td key={colKey} className="px-3 py-3">
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${ss.pill}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${ss.dot} flex-shrink-0`} />
            {product.status}
          </span>
        </td>
      );
      case 'price': return (
        <td key={colKey} className="px-3 py-3">
          <span className="text-xs font-semibold text-gray-700 dark:text-slate-300">{product.price}</span>
        </td>
      );
      case 'category': return (
        <td key={colKey} className="px-3 py-3">
          <span className="text-xs text-gray-600 dark:text-slate-400">{product.category}</span>
        </td>
      );
      case 'inventory': return (
        <td key={colKey} className="px-3 py-3">
          <span className={`text-xs font-semibold ${product.inventory === 0 ? 'text-red-600 dark:text-red-400' : product.inventory < 20 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-700 dark:text-slate-300'}`}>
            {product.inventory === 0 ? 'Out of stock' : `${product.inventory.toLocaleString()} in stock`}
          </span>
        </td>
      );
      case 'velocity': return (
        <td key={colKey} className="px-3 py-3">
          <span className="text-xs text-gray-600 dark:text-slate-400">{product.velocity}</span>
        </td>
      );
      default: return null;
    }
  };

  const _visibleCols = cols.filter(c => c.visible);

  const renderSortableHeader = (label, sortKey) => {
    const isActive = sortBy === sortKey;
    const isAsc = sortDir === 'asc';
    return (
      <th 
        className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left cursor-pointer hover:text-gray-600 dark:hover:text-slate-300 transition-colors select-none"
        onClick={() => {
          if (isActive) {
            setSortDir(isAsc ? 'desc' : 'asc');
          } else {
            setSortBy(sortKey);
            setSortDir('desc');
          }
        }}
      >
        <div className="flex items-center gap-1.5">
          {label}
          <div className="flex items-center">
            {isActive ? (
              <i className={`fa-solid fa-arrow-${isAsc ? 'up' : 'down'} text-[9px] text-brand`} />
            ) : (
              <i className="fa-solid fa-arrows-up-down text-[9px] opacity-40 hover:opacity-70 transition-opacity" />
            )}
          </div>
        </div>
      </th>
    );
  };

  return (
    <DashboardLayout
      title="Product Catalog"
      subtitle="1447 SKUs &middot; avg 5.3/7 fields filled &middot; 59 missing COGS"
      showTabs={false}
      showAIPrompt={false}
    >
      <div className="flex flex-col gap-4">

        {/* Realify Brief */}
        <BriefCard data={REALIFY_BRIEF} />

        {/* Toolbar */}
        <div className="flex items-center justify-between gap-3 mt-4">
          <div className="flex items-center gap-4">
            {/* Left: Count */}
            <div className="text-sm font-medium text-gray-700 dark:text-slate-300">
              {sortedFiltered.length} SKUs
            </div>

            {/* Left: Search input */}
            <div className="relative">
              <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 text-sm pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search products…"
                className="pl-9 pr-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-gray-700 dark:text-slate-300 placeholder-gray-400 dark:placeholder-slate-500 focus:outline-none focus:border-gray-400 dark:focus:border-slate-500 w-64 transition-all shadow-sm"
              />
            </div>
          </div>

          {/* Right controls: download csv, channel + date filters */}
          <div className="flex items-center justify-end gap-3">
            <button className="px-4 py-2 bg-indigo-300 hover:bg-indigo-400 text-white rounded-xl text-[13px] font-bold transition-colors shadow-sm flex items-center gap-2">
              <i className="fa-solid fa-download text-[11px]" /> Download CSV
            </button>
            <BriefHeaderControls />
          </div>
        </div>

        {/* Table */}
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead>
                <tr className="border-b border-gray-100 dark:border-slate-800">
                  <th className="px-4 py-3 w-8">
                    <input type="checkbox" checked={pageProducts.length > 0 && selectedIds.size === pageProducts.length} onChange={toggleAll} className="rounded border-gray-300 dark:border-slate-600 text-brand focus:ring-brand/20" />
                  </th>
                  <th className="px-3 py-3 w-8"></th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">SKU</th>
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Title</th>
                  {renderSortableHeader('Price', 'price')}
                  {renderSortableHeader('COGS', 'cogs')}
                  {renderSortableHeader('Margin %', 'margin')}
                  {renderSortableHeader('Unit/Mo', 'velocity')}
                  {renderSortableHeader('Returns', 'returns')}
                  {renderSortableHeader('Buy Box', 'bb')}
                  <th className="px-3 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-left">Sales Trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-slate-800/60">
                {pageProducts.length === 0 ? (
                  <tr><td colSpan="11" className="px-4 py-8 text-center text-sm text-gray-400 dark:text-slate-500">No products match your search.</td></tr>
                ) : pageProducts.map((product) => {
                  return (
                    <tr
                      key={product.id}
                      onClick={() => handleProductClick(product)}
                      className="transition-colors hover:bg-gray-50/80 dark:hover:bg-slate-800/30 cursor-pointer group"
                    >
                      <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                        <input type="checkbox" checked={selectedIds.has(product.id)} onChange={() => toggleSelect(product.id)} className="rounded border-gray-300 dark:border-slate-600 text-brand focus:ring-brand/20 disabled:opacity-40" />
                      </td>
                      <td className="px-3 py-3">
                        <span className={`w-2 h-2 rounded-full inline-block ${product.status === 'Active' ? 'bg-green-500' : product.status === 'Archived' ? 'bg-red-500' : 'bg-gray-400'}`}></span>
                      </td>
                      <td className="px-3 py-3 text-xs text-gray-500 dark:text-slate-400 font-sans">
                        {product.sku}
                      </td>
                      <td className="px-3 py-3">
                        <p className="text-sm font-semibold text-gray-900 dark:text-slate-100 group-hover:text-brand dark:group-hover:text-gray-200 transition-colors leading-tight truncate max-w-[200px]" title={product.name}>
                          {product.name}
                        </p>
                      </td>
                      <td className="px-3 py-3 text-xs font-semibold text-gray-700 dark:text-slate-300">{product.price}</td>
                      <td className="px-3 py-3 text-xs text-gray-600 dark:text-slate-400">{product.cogs}</td>
                      <td className="px-3 py-3 text-xs font-medium text-gray-700 dark:text-slate-300">{product.margin}</td>
                      <td className="px-3 py-3 text-xs text-gray-600 dark:text-slate-400">{product.velocity}</td>
                      <td className="px-3 py-3 text-xs text-gray-600 dark:text-slate-400">{product.returns}</td>
                      <td className="px-3 py-3 text-xs text-gray-600 dark:text-slate-400">{product.bb}</td>
                      <td className="px-3 py-3">
                        {product.salesTrend === 'up' ? (
                          <svg viewBox="0 0 40 20" className="w-10 h-5 overflow-visible">
                            <polyline points="0,18 10,12 20,15 30,5 40,0" fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        ) : (
                          <svg viewBox="0 0 40 20" className="w-10 h-5 overflow-visible">
                            <polyline points="0,2 10,8 20,5 30,15 40,20" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-1">
          <p className="text-xs text-gray-500 dark:text-slate-400">
            Showing {Math.min((page - 1) * PAGE_SIZE + 1, sortedFiltered.length)}–{Math.min(page * PAGE_SIZE, sortedFiltered.length)} of {sortedFiltered.length} products
          </p>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${page === 1 ? 'border-gray-100 dark:border-slate-800 text-gray-300 dark:text-slate-600 cursor-default' : 'border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 bg-white dark:bg-slate-900'}`}>
              Previous
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map(p => (
                <button key={p} onClick={() => setPage(p)}
                  className={`w-7 h-7 rounded-lg text-xs font-semibold transition-all ${page === p ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900' : 'text-gray-500 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800'}`}>
                  {p}
                </button>
              ))}
              {totalPages > 5 && <span className="text-xs text-gray-400">…</span>}
            </div>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages || totalPages === 0}
              className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${page === totalPages || totalPages === 0 ? 'border-gray-100 dark:border-slate-800 text-gray-300 dark:text-slate-600 cursor-default' : 'border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 bg-white dark:bg-slate-900'}`}>
              Next
            </button>
          </div>
        </div>

      </div>
      <ProductDetailModal isOpen={!!selectedProductForModal} onClose={() => setSelectedProductForModal(null)} product={selectedProductForModal} />
    </DashboardLayout>
  );
};

export default ProductsListPage;
