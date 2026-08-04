import React, { useMemo, useState } from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import ConnectorCard from '@/features/integrations/components/ConnectorCard';
import ConnectorDetailPanel from '@/features/integrations/components/ConnectorDetailPanel';
import {
  CONNECTORS,
  PAGE_SIZES,
  categoryChips,
  integrationSummary,
} from '@/features/integrations/data/integrationsData';
import { ROUTES } from '@/constants/routes';

/** How many category chips show before the rest collapse behind "More". */
const VISIBLE_CHIPS = 5;

const IntegrationsPage = () => {
  const navigate = useNavigate();
  const [category, setCategory] = useState('all');
  const [view, setView] = useState('grid');
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0]);
  const [page, setPage] = useState(1);
  const [moreOpen, setMoreOpen] = useState(false);

  /* Closed by default: the page opens as the catalogue alone, and only splits
     once the user picks a connector. */
  const [openConnector, setOpenConnector] = useState(null);

  const summary = useMemo(() => integrationSummary(), []);
  const chips = useMemo(() => categoryChips(), []);

  const filtered = useMemo(
    () => (category === 'all' ? CONNECTORS : CONNECTORS.filter((c) => c.category === category)),
    [category]
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  /* Clamp rather than store a page that may no longer exist after a filter
     change — keeps the grid from rendering empty. */
  const currentPage = Math.min(page, totalPages);
  const visible = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const pickCategory = (key) => {
    setCategory(key);
    setPage(1);
    setMoreOpen(false);
  };

  /* Card columns: three across the 60% column beside an open panel, four across
     the full-width catalogue. */
  const gridClass =
    view === 'list'
      ? 'space-y-2.5'
      : openConnector
        ? 'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3'
        : 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-3';

  const [headChips, moreChips] = [chips.slice(0, VISIBLE_CHIPS), chips.slice(VISIBLE_CHIPS)];

  const chipButton = (chip) => (
    <button
      key={chip.key}
      onClick={() => pickCategory(chip.key)}
      className={`px-3 py-1.5 rounded-lg text-[12.5px] font-semibold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
        category === chip.key
          ? 'bg-indigo-600 text-white'
          : 'bg-gray-50 dark:bg-slate-800/60 text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800'
      }`}
    >
      {chip.label}
      <span
        className={`text-[10.5px] font-bold ${
          category === chip.key ? 'text-white/70' : 'text-gray-400 dark:text-slate-500'
        }`}
      >
        {chip.count}
      </span>
    </button>
  );

  return (
    <DashboardLayout
      title="Integration"
      subtitle="Connect external services & channels"
      showTabs={false}
      showAIPrompt={false}
    >
      <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 space-y-4 font-sans">

        {/* ── Summary tiles ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {summary.map((tile) => (
            <div
              key={tile.key}
              className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl px-4 py-3.5"
            >
              <p className="text-[22px] font-bold text-gray-900 dark:text-white leading-none">
                {tile.value}
              </p>
              <p className="text-[12.5px] text-gray-600 dark:text-slate-300 mt-1.5">{tile.label}</p>

              {tile.sub && (
                <p className={`text-[11px] mt-1 flex items-center gap-1 ${tile.subTone || 'text-gray-400 dark:text-slate-500'}`}>
                  {tile.subIcon && <i className={`fa-solid ${tile.subIcon} text-[9px]`} />}
                  {tile.sub}
                </p>
              )}

              {tile.link && (
                <button
                  onClick={() => {
                    /* Jump straight to the connector that needs a human, rather
                       than making the user hunt for it in the grid. */
                    const target = CONNECTORS.find((c) => c.id === tile.linkTo);
                    if (target) setOpenConnector(target);
                  }}
                  disabled={!tile.linkTo}
                  className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 mt-1 flex items-center gap-1 disabled:opacity-40"
                >
                  {tile.link} <i className="fa-solid fa-arrow-right text-[9px]" />
                </button>
              )}
            </div>
          ))}
        </div>

        {/* ── Catalogue + detail panel ──
            60 / 40 via flex-[3] / flex-[2], matching the Agents screen. Growth
            factors rather than percentages, because percentages plus the gap
            would total more than the row. */}
        <div className={openConnector ? 'flex flex-col xl:flex-row gap-4 items-start' : ''}>
          <div className={`min-w-0 space-y-3 ${openConnector ? 'w-full xl:flex-[3]' : ''}`}>

            {/* ── Categories ── */}
            <div>
              <p className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">
                Categories
              </p>
              <div className="flex items-center gap-2 flex-wrap">
                {headChips.map(chipButton)}

                {moreChips.length > 0 && (
                  <div className="relative">
                    <button
                      onClick={() => setMoreOpen((v) => !v)}
                      className="px-3 py-1.5 rounded-lg text-[12.5px] font-semibold bg-gray-50 dark:bg-slate-800/60 text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1.5"
                    >
                      More <i className={`fa-solid fa-chevron-${moreOpen ? 'up' : 'down'} text-[9px]`} />
                    </button>

                    {moreOpen && (
                      <div className="absolute left-0 top-full mt-1.5 z-20 min-w-[190px] bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-xl p-1.5 flex flex-col gap-1 animate-in fade-in zoom-in-95 duration-150">
                        {moreChips.map((chip) => (
                          <button
                            key={chip.key}
                            onClick={() => pickCategory(chip.key)}
                            className={`px-2.5 py-1.5 rounded-lg text-[12.5px] font-medium text-left flex items-center justify-between gap-3 transition-colors ${
                              category === chip.key
                                ? 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 font-bold'
                                : 'text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                            }`}
                          >
                            {chip.label}
                            <span className="text-[10.5px] font-bold text-gray-400 dark:text-slate-500">
                              {chip.count}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* ── Connector grid ── */}
            {visible.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center py-10">
                <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
                  <i className="fa-solid fa-plug-circle-xmark text-[15px]" />
                </div>
                <p className="text-[13.5px] font-bold text-gray-800 dark:text-slate-200 mb-1">
                  No connectors here yet
                </p>
                <p className="text-[12.5px] text-gray-500 dark:text-slate-400 max-w-[340px] leading-relaxed">
                  Switch to All to browse the full catalogue.
                </p>
              </div>
            ) : (
              <div className={gridClass}>
                {visible.map((connector) => (
                  <ConnectorCard
                    key={connector.id}
                    connector={connector}
                    view={view}
                    onSelect={setOpenConnector}
                    isSelected={openConnector?.id === connector.id}
                  />
                ))}
              </div>
            )}

            {/* ── Pagination + view controls ── */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  aria-label="Previous page"
                  className="w-7 h-7 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center disabled:opacity-40 disabled:hover:bg-transparent"
                >
                  <i className="fa-solid fa-chevron-left text-[9px]" />
                </button>

                {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                  <button
                    key={n}
                    onClick={() => setPage(n)}
                    className={`w-7 h-7 rounded-lg text-[12px] font-semibold transition-colors ${
                      n === currentPage
                        ? 'border border-indigo-500 text-indigo-600 dark:text-indigo-400'
                        : 'text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    {n}
                  </button>
                ))}

                <button
                  onClick={() => setPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  aria-label="Next page"
                  className="w-7 h-7 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center disabled:opacity-40 disabled:hover:bg-transparent"
                >
                  <i className="fa-solid fa-chevron-right text-[9px]" />
                </button>
              </div>

              <div className="flex items-center gap-2.5">
                <div className="flex items-center gap-1.5 text-[12px] text-gray-500 dark:text-slate-400">
                  View:
                  <SelectMenu
                    value={pageSize}
                    options={PAGE_SIZES.map((n) => ({ id: n, label: `${n} per page` }))}
                    onChange={(n) => { setPageSize(Number(n)); setPage(1); }}
                    size="sm"
                    ariaLabel="Results per page"
                    className="w-[124px] flex-shrink-0"
                  />
                </div>

                <div className="flex items-center rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
                  {[
                    { key: 'grid', icon: 'fa-table-cells-large' },
                    { key: 'list', icon: 'fa-list' },
                  ].map((opt) => (
                    <button
                      key={opt.key}
                      onClick={() => setView(opt.key)}
                      aria-label={`${opt.key} view`}
                      aria-pressed={view === opt.key}
                      className={`w-8 h-7 flex items-center justify-center transition-colors ${
                        view === opt.key
                          ? 'bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-200'
                          : 'text-gray-400 dark:text-slate-500 hover:bg-gray-50 dark:hover:bg-slate-800/60'
                      }`}
                    >
                      <i className={`fa-solid ${opt.icon} text-[11px]`} />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {openConnector && (
            <div className="w-full min-w-0 xl:flex-[2] animate-in fade-in slide-in-from-right-4 duration-300">
              <ConnectorDetailPanel
                connector={openConnector}
                onClose={() => setOpenConnector(null)}
                /* The panel is a summary; the full connector page is a real route,
                   so it survives a refresh and a given tab can be linked to. */
                onPrimaryAction={(c) =>
                  navigate(ROUTES.CONNECTOR_DETAIL.replace(':connectorId', c.id))
                }
              />
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default IntegrationsPage;
