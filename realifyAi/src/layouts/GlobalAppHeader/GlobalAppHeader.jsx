import React, { useRef, useLayoutEffect, useMemo, useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useFilterStore } from '@/store/useFilterStore';
import { useHeaderScroll, notifyHeaderMeasured } from '@/layouts/GlobalAppHeader/useHeaderScroll';
import { useSimulationStore } from '@/store/useSimulationStore';
import SelectInput from '@/components/ui/SelectInput';
import white_latest from '@/assets/white_latest.png';
import dark_latest from '@/assets/dark_latest.png';
import ProfileDrawer from '@/layouts/ProfileDrawer';
import FilterPopover from '@/layouts/GlobalAppHeader/FilterPopover';

const TOOLBAR = { compressed: 64, expanded: 84 };

const TOOLBAR_MARKETPLACE_PLATFORMS = [
  { id: 'amazon', icon: 'fa-amazon', color: 'text-orange-500' },
  { id: 'shopify', icon: 'fa-shopify', color: 'text-green-500' },
];
const FULL_MARKETPLACE_PLATFORMS = [
  { id: 'amazon', icon: 'fa-amazon', color: 'text-orange-500' },
  { id: 'shopify', icon: 'fa-shopify', color: 'text-green-500' },
  { id: 'walmart', icon: 'fa-cart-shopping', color: 'text-blue-400' },
];

const GlobalAppHeader = ({
  title,
  subtitle,
  onNotificationClick,
  shopProfile,
  customRightElement,
  showTabs = true,
  tabs,
  filters: customFilters,
  scrollRef,
  activeTabPath,
  tabsOnly = false,
  _showSearch = false,
  renderOnly = null,
  searchCollapsed = false,
  centerElement = null,
  darkMode = false,
  onMenuClick,
  hideMobileSearchIcon = false,
}) => {
  const [profileDrawerOpen, setProfileDrawerOpen] = useState(false);

  const _getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const _username = localStorage.getItem('username') || 'anurag101';
  const _activeShop = localStorage.getItem('active_shop') || shopProfile?.shop_name || 'sdfsdf';
  const platformDomain = localStorage.getItem('active_platform_domain') || 'amazon.in';
  const currentDateFormatted = new Date().toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).toUpperCase();

  const location = useLocation();
  const {
    searchQuery, setSearchQuery,
    dateRange, setDateRange,
    category, setCategory,
    channel, setChannel,
  } = useFilterStore();

  const secondaryRef = useRef(null);
  const { isCompressed, isScrolled, forceExpand } = useHeaderScroll(TOOLBAR, scrollRef);
  const [searchExpanded, setSearchExpanded] = useState(false);
  const [filterPreviewCount, setFilterPreviewCount] = useState(0);
  const searchInputRef = useRef(null);
  const { isSimulating, progress: globalProgress } = useSimulationStore();

  const [prevSearchCollapsed, setPrevSearchCollapsed] = useState(searchCollapsed);
  if (searchCollapsed !== prevSearchCollapsed) {
    setPrevSearchCollapsed(searchCollapsed);
    if (!searchCollapsed) setSearchExpanded(false);
  }

  useEffect(() => {
    if (searchExpanded && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [searchExpanded]);

  useLayoutEffect(() => {
    const el = secondaryRef.current;
    if (!el) return;
    const measure = () => {
      const h = el.getBoundingClientRect().height;
      document.documentElement.style.setProperty('--header-secondary-height', `${h}px`);
      notifyHeaderMeasured(TOOLBAR);
    };
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    measure();
    return () => ro.disconnect();
  }, []);

  const defaultTabs = useMemo(() => [
    { path: '/sales', label: 'Sales', icon: 'fa-dollar-sign' },
    { path: '/margin', label: 'Margin', icon: 'fa-chart-line' },
    { path: '/inventory', label: 'Inventory', icon: 'fa-boxes' },
    { path: '/ads', label: 'Ads', icon: 'fa-bullhorn' },
    { path: '/cash', label: 'Cash', icon: 'fa-money-bill-wave' },
  ], []);

  const activeTabs = tabs || defaultTabs;

  const isTabActive = (tab) => {
    if (activeTabPath !== undefined) return tab.path === activeTabPath;
    return location.pathname === tab.path;
  };

  const renderTab = (tab, variant) => {
    const active = isTabActive(tab);
    const compactCls = active
      ? 'bg-gray-900 dark:bg-slate-700 text-white dark:text-white'
      : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800';
    const fullCls = active
      ? 'bg-gray-900 dark:bg-slate-700 text-white dark:text-white'
      : 'text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800';

    const isCompact = variant === 'compact';
    const className = isCompact
      ? `px-3 py-1 text-[11px] font-medium rounded-full transition-colors whitespace-nowrap flex items-center gap-1 ${compactCls}`
      : `px-4 py-1.5 text-sm font-medium rounded-full transition-colors whitespace-nowrap flex items-center gap-1.5 ${fullCls}`;

    const content = isCompact
      ? <><i className={`fa-solid ${tab.icon} text-[9px]`} />{tab.label}</>
      : <><i className={`fa-solid ${tab.icon} text-[11px]`} />{tab.label}</>;

    if (tab.onClick) {
      return (
        <button key={tab.path} onClick={tab.onClick} className={className}>
          {content}
        </button>
      );
    }
    return (
      <Link key={tab.path} to={tab.path} className={className}>
        {content}
      </Link>
    );
  };

  const _renderMarketplaceToggles = (platforms) => (
    <div className="flex items-center gap-1 px-2 py-1.5 bg-gray-50 dark:bg-slate-800/60 rounded-xl border border-gray-200 dark:border-slate-700 shadow-sm">
      {platforms.map((p) => {
        const activePlatforms = JSON.parse(localStorage.getItem('active_platforms') || '["shopify"]');
        const isActive = activePlatforms.includes(p.id);
        return (
          <button
            key={p.id}
            onClick={() => {
              let next;
              if (isActive) {
                if (activePlatforms.length > 1) next = activePlatforms.filter(id => id !== p.id);
                else return;
              } else {
                next = [...activePlatforms, p.id];
              }
              localStorage.setItem('active_platforms', JSON.stringify(next));
              localStorage.setItem('active_platform', next[0]);
              window.location.reload();
            }}
            title={`${p.id.charAt(0).toUpperCase() + p.id.slice(1)} ${isActive ? '(Active)' : '(Connect)'}`}
            className={`relative w-7 h-7 rounded-lg flex items-center justify-center transition-all active:scale-90 ${isActive
              ? 'bg-white dark:bg-slate-900 shadow-sm'
              : 'opacity-35 grayscale hover:opacity-80 hover:grayscale-0'
              }`}
          >
            <i className={`fa-brands ${p.icon} ${p.color} text-sm`} />
            {isActive && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full border border-gray-50 dark:border-slate-900" />
            )}
          </button>
        );
      })}
    </div>
  );

  const simulationRing = isSimulating && (
    <div className="relative w-8 h-8 flex-shrink-0" title={`Executing: ${globalProgress}%`}>
      <svg className="w-8 h-8 -rotate-90" viewBox="0 0 32 32">
        <circle cx="16" cy="16" r="12" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-gray-200 dark:text-slate-700" />
        <circle cx="16" cy="16" r="12" fill="none" stroke="currentColor" strokeWidth="2.5"
          className="text-gray-800 dark:text-slate-200 transition-all duration-700"
          strokeDasharray={`${2 * Math.PI * 12}`}
          strokeDashoffset={`${2 * Math.PI * 12 * (1 - globalProgress / 100)}`}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[8px] font-bold text-gray-700 dark:text-slate-300">
        {globalProgress}%
      </span>
    </div>
  );

  const refreshButton = (
    <button
      className="w-8 h-8 flex items-center justify-center group active:scale-95 transition-all"
      onClick={() => window.location.reload()}
      title="Refresh Data"
    >
      <i className="fa-solid fa-rotate text-gray-500 dark:text-slate-400 group-hover:text-gray-700 dark:group-hover:text-slate-200 text-sm group-hover:rotate-180 transition-transform duration-700 ease-out" />
    </button>
  );

  const renderNotificationButton = (count = 0) => (
    <button
      onClick={onNotificationClick}
      className="w-8 h-8 relative flex items-center justify-center group active:scale-95 transition-all"
      title="Notifications"
    >
      <i className="fa-solid fa-bell text-gray-600 dark:text-slate-300 group-hover:text-gray-800 dark:group-hover:text-slate-100 text-sm transition-colors" />
      {count > 0 ? (
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-gray-800 dark:bg-slate-200 text-white dark:text-gray-900 text-[9px] font-bold rounded-full flex items-center justify-center leading-none pointer-events-none">
          {count}
        </span>
      ) : (
        <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
      )}
    </button>
  );

  const profileButton = (
    <button onClick={() => setProfileDrawerOpen(true)} className="relative group p-0">
      <div className="w-8 h-8 rounded-full overflow-hidden border border-gray-200 dark:border-slate-700 bg-gray-100 dark:bg-slate-800 group-hover:ring-2 group-hover:ring-gray-400 dark:group-hover:ring-slate-500 transition-all flex items-center justify-center">
        <i className="fa-solid fa-user text-gray-400 dark:text-slate-500 text-sm" />
      </div>
    </button>
  );

  const renderSearchExpandToggle = () => (
    <>
      <button
        onClick={() => setSearchExpanded(v => !v)}
        className={`w-8 h-8 flex items-center justify-center bg-gray-50 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700 rounded-xl shadow-sm hover:bg-gray-100 dark:hover:bg-slate-700 transition-all${searchExpanded ? ' border-brand/40 bg-blue-50 dark:bg-slate-700' : ''}`}
        title="Search"
      >
        <i className={`fa-solid fa-magnifying-glass text-xs ${searchExpanded ? 'text-brand dark:text-gray-300' : 'text-gray-400 dark:text-slate-500'}`} />
      </button>
      {searchExpanded && (
        <div className="absolute right-0 top-full mt-1.5 w-72 z-[99999] shadow-xl rounded-xl overflow-hidden border border-gray-200 dark:border-slate-700">
          <div className="relative bg-white dark:bg-slate-900">
            <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-brand dark:text-gray-400 text-xs pointer-events-none" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search products, SKUs, or customers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onBlur={() => { if (!searchQuery) setSearchExpanded(false); }}
              className="w-full pl-9 pr-8 py-2 bg-white dark:bg-slate-900 text-xs text-gray-700 dark:text-slate-200 placeholder-gray-400 dark:placeholder-slate-500 focus:outline-none"
            />
            <button
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => { setSearchExpanded(false); setSearchQuery(''); }}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
            >
              <i className="fa-solid fa-xmark text-xs" />
            </button>
          </div>
        </div>
      )}
    </>
  );

  const defaultFilterBar = (
    <div className="flex items-center gap-2">
      {[
        {
          value: dateRange, onChange: setDateRange,
          options: [['all', 'All'], ['last-7-days', 'Last 7 Days'], ['last-30-days', 'Last 30 Days'], ['last-90-days', 'Last 90 Days'], ['ytd', 'Year to Date']],
        },
        {
          value: category, onChange: setCategory,
          options: [['all', 'All Categories'], ['electronics', 'Electronics'], ['home-garden', 'Home & Garden'], ['apparel', 'Apparel']],
        },
      ].map((sel, i) => (
        <SelectInput
          key={i}
          value={sel.value}
          onChange={(e) => sel.onChange(e.target.value)}
        >
          {sel.options.map(([val, label]) => (
            <option key={val} value={val}>{label}</option>
          ))}
        </SelectInput>
      ))}
    </div>
  );

  const filterBar = customFilters !== undefined ? customFilters : (showTabs ? defaultFilterBar : null);

  if (tabsOnly) {
    return (
      <div className="flex-shrink-0 rounded-t-2xl overflow-hidden bg-white dark:bg-[#030712] border-b border-gray-200 dark:border-slate-800">
        <div ref={secondaryRef} className="flex items-center overflow-x-auto scrollbar-hide px-4 sm:px-6 pt-1 gap-0.5">
          {activeTabs.map((tab) => renderTab(tab, 'full'))}
        </div>
      </div>
    );
  }

  if (renderOnly === 'toolbar') {
    return (
      <>
        {/* MOBILE top bar — hamburger, logo, search/notifications/profile (ss1) */}
        <div className="sm:hidden grid grid-cols-3 items-center px-4 h-[56px] border-b border-black/[0.05]">
          <div className="justify-self-start">
            {onMenuClick && (
              <button
                onClick={onMenuClick}
                className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-600 dark:text-slate-300 active:scale-95 transition-transform"
                title="Menu"
              >
                <i className="fa-solid fa-bars text-base" />
              </button>
            )}
          </div>
          <div className="justify-self-center">
            <img src={darkMode ? white_latest : dark_latest} alt="Realify" className="h-[2.5rem] w-auto max-w-[100px] object-contain" />
          </div>
          <div className="relative flex items-center gap-3 justify-self-end">
            {!hideMobileSearchIcon && renderSearchExpandToggle()}
            {renderNotificationButton()}
            {profileButton}
          </div>
        </div>

        <div className="hidden sm:flex items-center px-4 sm:px-6 gap-4 h-[56px] relative border-b border-black/[0.05]">
          {/* LEFT — page title + subtitle */}
          {title && (
            <div className="shrink-0 min-w-0">
              <h2 className="font-bold text-gray-900 dark:text-slate-100 text-[18px] leading-tight tracking-tight whitespace-nowrap">
                {title}
              </h2>
              {subtitle && (
                <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5 whitespace-nowrap hidden sm:block">
                  {subtitle}
                </p>
              )}
            </div>
          )}

          {/* CENTER — absolutely centered on full header width for true centering */}
          {centerElement && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="pointer-events-auto flex items-center">
                {centerElement}
              </div>
            </div>
          )}
          {/* Flex spacer always present to push right section to edge */}
          <div className="flex-1" />

          {/* RIGHT — Dynamic User Greeting + Actions */}
          <div className="flex items-center gap-3 shrink-0">
            {!isScrolled && !isCompressed && (
              <div className="header-greeting-block hidden md:flex flex-col items-end text-right px-1 transition-opacity duration-200">
                <div className="flex items-center gap-1.5 text-[8px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mt-0.5">
                  <span>{currentDateFormatted}</span>
                  <span>•</span>
                  <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-extrabold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    LIVE
                  </span>
                  <span>•</span>
                  <span>{platformDomain}</span>
                </div>
              </div>
            )}

            {customRightElement}

            {simulationRing}

            {refreshButton}
            {renderNotificationButton()}
            {profileButton}
          </div>
        </div>
        <ProfileDrawer isOpen={profileDrawerOpen} onClose={() => setProfileDrawerOpen(false)} />
      </>
    );
  }

  if (renderOnly === 'secondary') {
    return (
      <div className="flex-shrink-0 border-b border-gray-200 dark:border-slate-800">
        {/* MOBILE-only page heading (ss1) — the toolbar row hides title/subtitle below sm */}
        {!tabsOnly && title && (
          <div className="sm:hidden px-4 pt-3 pb-1">
            <h2 className="font-bold text-gray-900 dark:text-slate-100 text-[17px] leading-tight tracking-tight">{title}</h2>
            {subtitle && <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
        )}
        <div ref={secondaryRef} className="flex flex-col sm:flex-row sm:items-center">
          {showTabs && (
            <div id="header-navigation" className="flex-1 flex items-center overflow-x-auto scrollbar-hide px-4 sm:px-6 py-2 gap-1 min-w-0">
              {activeTabs.map((tab) => renderTab(tab, 'full'))}
            </div>
          )}
          {!tabsOnly && filterBar && (
            <div className={`flex items-center px-4 sm:px-6 pb-2 sm:pb-1 pt-0 sm:pt-1 ${showTabs ? 'sm:flex-shrink-0' : 'flex-1 w-full'}`}>
              {filterBar}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-shrink-0 rounded-t-2xl overflow-hidden bg-white dark:bg-[#030712] border-b border-gray-200 dark:border-slate-800">

      {/* ── Toolbar row: title | search/compact-tabs | icons ── */}
      <div className="page-header-toolbar px-4 sm:px-6 gap-3">

        {/* LEFT — title */}
        {title && (
          <div className="page-header-title shrink-0 min-w-0">
            <h2 className="font-bold text-gray-900 dark:text-slate-100 text-[1.1rem] leading-tight tracking-tight">
              {title}
            </h2>
            {subtitle && (
              <p className="page-header-subtitle text-[10px] text-gray-400 dark:text-slate-500 mt-0.5 whitespace-nowrap hidden sm:block">
                {subtitle}
              </p>
            )}
          </div>
        )}

        {/* CENTER — Sticky page header tabs (when scrolled) */}
        <div className="flex-1 flex flex-col items-center justify-center text-center shrink-0 min-w-0">
          {centerElement ? (
            <div className="flex items-center justify-center font-bold text-sm sm:text-base">
              {centerElement}
            </div>
          ) : null}
        </div>

        {/* RIGHT — greeting block, rules button, refresh, notifications, profile, expand */}
        <div className="flex items-center gap-2 shrink-0 ml-auto">
          {!isScrolled && !isCompressed && (
            <div className="header-greeting-block hidden md:flex flex-col items-end text-right px-1 transition-opacity duration-200">
              <div className="flex items-center gap-1.5 text-[8px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mt-0.5">
                <span>{currentDateFormatted}</span>
                <span>•</span>
                <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-extrabold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  LIVE
                </span>
                <span>•</span>
                <span>{platformDomain}</span>
              </div>
            </div>
          )}

          {customRightElement}

          {isCompressed && (
            <FilterPopover
              dateRange={dateRange} setDateRange={setDateRange}
              category={category} setCategory={setCategory}
              channel={channel} setChannel={setChannel}
              onPendingCountChange={setFilterPreviewCount}
            />
          )}

          {simulationRing}

          {refreshButton}

          {renderNotificationButton(filterPreviewCount)}

          {profileButton}

          <button
            onClick={forceExpand}
            className={`page-header-expand-btn w-8 h-8 flex items-center justify-center bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/50 rounded-xl border border-blue-200 dark:border-blue-800 shadow-sm active:scale-95 transition-all${isCompressed ? ' is-visible' : ''}`}
            title="Expand header"
          >
            <i className="fa-solid fa-chevron-down text-blue-600 dark:text-blue-400 text-xs" />
          </button>
        </div>
      </div>

      {/* ── Secondary row: full tabs + filter dropdowns (collapses on scroll) ── */}
      <div className="page-header-secondary">
        <div ref={secondaryRef} className="page-header-secondary-inner">
          {showTabs && (
            <div
              id="header-navigation"
              className="flex items-center overflow-x-auto scrollbar-hide px-4 sm:px-6 pt-1 gap-0.5"
            >
              {activeTabs.map((tab) => renderTab(tab, 'full'))}
            </div>
          )}
          {filterBar}
        </div>
      </div>
      <ProfileDrawer isOpen={profileDrawerOpen} onClose={() => setProfileDrawerOpen(false)} />
    </div>
  );
};

export default GlobalAppHeader;
