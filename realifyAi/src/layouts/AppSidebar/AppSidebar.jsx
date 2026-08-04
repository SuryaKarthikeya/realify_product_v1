import React, { useState, useEffect } from 'react';
import { useUIStore } from '@/store/useUIStore';
import { useMarketplaceStore } from '@/store/useMarketplaceStore';
import { useViewModeStore } from '@/store/useViewModeStore';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ROUTES } from '@/constants/routes';
import logo_dark from '@/assets/logo_dark.png';
import logo_white from '@/assets/logo_white.png';
import LOGO1 from '@/assets/LOGO1.png';
import LOGO2 from '@/assets/LOGO2.png';
import white_latest from '@/assets/white_latest.png';
import dark_latest from '@/assets/dark_latest.png';
import { rolePermissions } from "@/config/RolePermission";
import { SETTINGS_NAV_ITEMS } from '@/features/settings';

import { t } from '@/layouts/AppSidebar/constants';
import { IconPanelCollapse, IconPanelExpand } from '@/layouts/AppSidebar/icons';
import HistorySectionContent from '@/layouts/AppSidebar/HistorySection';
import SidebarItem from '@/layouts/AppSidebar/SidebarItem';
import { isWorkspacePath, workspacePath, dashboardPath } from '@/features/workspace';

const AppSidebar = ({ darkMode, _setDarkMode, inline = false, mobileOpen = false, onMobileClose }) => {
  const { isSidebarCollapsed, toggleSidebar } = useUIStore();
  const { connectedStores } = useMarketplaceStore();
  const { dashboardView, lastWorkspaceDomain, setDashboardView } = useViewModeStore();
  const isConnected = connectedStores.length > 0;
  const location = useLocation();
  const navigate = useNavigate();

  // Auto-close the mobile drawer on navigation, and lock body scroll while it's open.
  useEffect(() => {
    if (mobileOpen) onMobileClose?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.key]);

  useEffect(() => {
    if (!mobileOpen) return;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  // Mobile drawer's "Settings" row opens a sub-list (ss4) instead of navigating
  // directly — switching settings sections is only reachable from here, never
  // from within a settings tab itself. Reset back to the main menu on close.
  const [settingsSubOpen, setSettingsSubOpen] = useState(false);
  useEffect(() => {
    if (!mobileOpen) setSettingsSubOpen(false);
  }, [mobileOpen]);
  const activeSettingsTab = new URLSearchParams(location.search).get('tab') || 'account';

  const _isHistoryActive = location.pathname === ROUTES.HISTORY;
  const isScreenerActive = location.pathname.startsWith(ROUTES.SCREENER);
  const isNewAnalysisActive = location.pathname === ROUTES.NEW_ANALYSIS;
  const isSettingsActive = location.pathname === ROUTES.SETTINGS;
  const isWorkspaceActive = isWorkspacePath(location.pathname);

  // Land back on whichever view (AI or Dashboard) + tab the user last had open,
  // instead of always defaulting to AI View / sales.
  const workspaceHref = dashboardView ? dashboardPath(lastWorkspaceDomain) : workspacePath(lastWorkspaceDomain);
  // Role permissions are checked against the base path, not the tab-specific one.
  const workspacePermissionKey = ROUTES.WORKSPACE;

  const isCatalogueActive = location.pathname === '/catalogue' || location.pathname === '/products';
  const isAgentsActive = location.pathname === '/agents';
  /* Prefix, not equality: a connector's own page (/integrations/amazon-sp-api)
     is still inside Integrations, and left the nav item unhighlighted. */
  const isIntegrationsActive = location.pathname.startsWith('/integrations');
  const isProfitAdsActive = location.pathname === '/profit-ads';

  const navItems = [
    { name: 'New', icon: 'fa-plus', href: ROUTES.NEW_ANALYSIS, active: isNewAnalysisActive },
    { name: 'Workspace', icon: 'fa-chart-line', href: workspaceHref, permissionKey: workspacePermissionKey, active: isWorkspaceActive },
    { name: 'Agents', icon: 'fa-solid fa-user-tie', href: ROUTES.AGENTS || '/agents', permissionKey: ROUTES.AGENTS || '/agents', active: isAgentsActive },
    { name: 'Integrations', icon: 'fa-plug', href: ROUTES.INTEGRATIONS || '/integrations', permissionKey: ROUTES.INTEGRATIONS || '/integrations', active: isIntegrationsActive },
  ];
  const role = localStorage.getItem("userRole") || "admin";
  const allowedRoutes = rolePermissions[role] || [];
  const filteredNavItems = navItems.filter(item => allowedRoutes.includes(item.permissionKey || item.href));
  const _isProductsActive = location.pathname === '/products' || location.pathname === '/catalogue';
  const _isActionLogActive = location.pathname === '/action-log';
  const isActionsActive = location.pathname === ROUTES.ACTIONS;
  const settingsItem = { name: 'Settings', icon: 'fa-gear', href: ROUTES.SETTINGS, active: isSettingsActive };

  /* ── Mobile drawer (ss2 layout) — opened via the header hamburger button ── */
  const mobileDrawer = mobileOpen && (
    <>
      <div className="md:hidden fixed inset-0 bg-black/40 z-[9998]" onClick={onMobileClose} />
      <div className="md:hidden fixed inset-y-0 left-0 w-[66vw] bg-white dark:bg-[#030712] z-[9999] flex flex-col shadow-2xl">
        {settingsSubOpen ? (
          <>
            {/* Settings sub-list header: back to main menu, or close the drawer entirely */}
            <div className="flex items-center justify-between px-3 pt-4 pb-2 flex-shrink-0 border-b border-gray-100 dark:border-slate-800" style={{ height: 56 }}>
              <button
                onClick={() => setSettingsSubOpen(false)}
                className="w-7 h-7 flex items-center justify-center rounded-md text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800/50 transition-colors"
                title="Back"
              >
                <i className="fa-solid fa-arrow-left text-sm" />
              </button>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-100">Settings</span>
              <button
                onClick={onMobileClose}
                className="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/50 transition-colors"
                title="Close menu"
              >
                <i className="fa-solid fa-xmark text-sm" />
              </button>
            </div>

            {/* Scrollable settings section list — switching sections is only possible from here */}
            <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide px-2 pt-2 flex flex-col gap-1">
              {SETTINGS_NAV_ITEMS.slice(0, 7).map(item => (
                <Link
                  key={item.id}
                  to={`${ROUTES.SETTINGS}?tab=${item.id}`}
                  onClick={onMobileClose}
                  className={`flex items-center gap-3 px-2 py-2 rounded-lg transition-colors ${activeSettingsTab === item.id
                    ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                    : 'text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/30'
                    }`}
                >
                  <i className={`fa-solid ${item.icon} w-5 text-center text-[13px] ${activeSettingsTab === item.id ? '' : 'text-gray-400 dark:text-slate-500'}`} />
                  <span className="text-xs font-medium">{item.name}</span>
                </Link>
              ))}
              <div className="border-t border-gray-100 dark:border-slate-800 my-1" />
              {SETTINGS_NAV_ITEMS.slice(7).map(item => (
                <Link
                  key={item.id}
                  to={`${ROUTES.SETTINGS}?tab=${item.id}`}
                  onClick={onMobileClose}
                  className={`flex items-center gap-3 px-2 py-2 rounded-lg transition-colors ${activeSettingsTab === item.id
                    ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                    : 'text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/30'
                    }`}
                >
                  <i className={`fa-solid ${item.icon} w-5 text-center text-[13px] ${activeSettingsTab === item.id ? '' : 'text-gray-400 dark:text-slate-500'}`} />
                  <span className="text-xs font-medium">{item.name}</span>
                </Link>
              ))}
            </div>

            <div className="flex-shrink-0 pb-4 pt-2 border-t border-gray-100 dark:border-slate-800 w-full px-2">
              <div className="flex items-center gap-2 px-2 py-2">
                <i className="fa-solid fa-circle-user text-2xl text-gray-900 dark:text-slate-200" />
                <span className="text-xs font-medium text-gray-900 dark:text-slate-200 truncate">My Account</span>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Top: scrollable logo + nav + history */}
            <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide flex flex-col">
              <div className="flex items-center justify-between px-3 pt-4 pb-2 flex-shrink-0" style={{ height: 56 }}>
                <img src={darkMode ? white_latest : dark_latest} alt="Realify" className="h-9 w-auto max-w-[110px] object-contain" />
                <button
                  onClick={onMobileClose}
                  className="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/50 transition-colors"
                  title="Close menu"
                >
                  <i className="fa-solid fa-xmark text-sm" />
                </button>
              </div>
              <nav className="w-full px-2 pt-2 flex flex-col gap-1 flex-shrink-0">
                {filteredNavItems.map(item => (
                  <div key={item.name} className="w-full">
                    <SidebarItem item={item} isCollapsed={false} small={true} />
                  </div>
                ))}
              </nav>
              {isConnected && <HistorySectionContent />}
            </div>

            {/* Bottom: Catalog + Actions + Settings */}
            <div className="flex-shrink-0 pb-4 pt-2 flex flex-col gap-1 border-t border-gray-100 dark:border-slate-800 w-full px-2">
              <button
                onClick={() => setSettingsSubOpen(true)}
                className={`flex items-center group relative w-full rounded-lg transition-colors justify-start px-2 py-1.5 ${isSettingsActive
                  ? 'text-gray-900 dark:text-slate-100 bg-gray-100 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700/50 shadow-sm'
                  : 'text-gray-900 dark:text-slate-200 hover:text-gray-900 dark:hover:text-slate-100 hover:bg-gray-100 dark:hover:bg-slate-800/30'
                  }`}
              >
                <div className="flex items-center justify-center flex-shrink-0 rounded-md w-7 h-7">
                  <i className="fa-solid fa-gear" style={{ fontSize: 15 }} />
                </div>
                <span className="ml-2 text-xs font-normal whitespace-nowrap">Settings</span>
              </button>

              {/* AI VIew Toggle */}
              <button
                onClick={() => {
                  const nextView = !dashboardView;

                  setDashboardView(nextView);

                  navigate(
                    nextView
                      ? dashboardPath(lastWorkspaceDomain)
                      : workspacePath(lastWorkspaceDomain)
                  );
                }}
                className="flex items-center justify-between w-full px-2 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <i className={`fa-solid ${dashboardView ? 'fa-table-cells-large' : 'fa-wand-magic-sparkles'} text-base text-gray-900 dark:text-slate-200`} />

                  <span className="text-xs font-medium text-gray-900 dark:text-slate-200">
                    {dashboardView ? "Dashboard View" : "AI View"}
                  </span>
                </div>

                <div
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${dashboardView
                    ? "bg-blue-500"
                    : "bg-gray-300 dark:bg-slate-600"
                    }`}
                >
                  <span
                    className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${dashboardView
                      ? "translate-x-4"
                      : "translate-x-0.5"
                      }`}
                  />
                </div>
              </button>


              <div className="flex items-center gap-2 px-2 py-2 mt-1 rounded-lg">
                <i className="fa-solid fa-circle-user text-2xl text-gray-900 dark:text-slate-200" />
                <span className="text-xs font-medium text-gray-900 dark:text-slate-200 truncate">My Account</span>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );

  /* ── Inline variant (used inside DashboardLayout) ── */
  if (inline) {
    return (
      <>
        <div
          style={{ width: isSidebarCollapsed ? 56 : 200, transition: t(['width']), willChange: 'width' }}
          className="hidden md:flex flex-shrink-0 flex-col h-full bg-white dark:bg-[#030712] transition-colors duration-300 border-r border-gray-200 dark:border-slate-800 overflow-visible relative z-10"
        >
          {/* Logo row */}
          {isSidebarCollapsed ? (
            <div className="flex items-center justify-center flex-shrink-0" style={{ height: 56 }}>
              <div
                className="relative group flex items-center justify-center cursor-pointer w-9 h-9 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800/30"
                onClick={toggleSidebar}
                title="Expand sidebar"
              >
                <img
                  src={darkMode ? logo_white : logo_dark}
                  alt="Realify"
                  className="absolute inset-0 w-full h-full object-contain p-1 transition-opacity duration-150 group-hover:opacity-0"
                />
                <span className="opacity-0 transition-opacity duration-150 group-hover:opacity-100 text-gray-500 dark:text-slate-400">
                  <IconPanelExpand size={15} />
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between px-2 flex-shrink-0" style={{ height: 56 }}>
              <img src={darkMode ? white_latest : dark_latest} alt="Realify" className="h-10 w-auto max-w-[110px] object-contain" />
              <button
                onClick={toggleSidebar}
                className="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/50 transition-colors"
                title="Collapse sidebar"
              >
                <IconPanelCollapse size={15} />
              </button>
            </div>
          )}

          {/* Nav */}
          <nav className="flex-1 w-full scrollbar-hide px-2 pt-2 flex flex-col gap-1 overflow-y-auto">
            {filteredNavItems.map(item => (
              <div key={item.name} className="w-full">
                <SidebarItem item={item} isCollapsed={isSidebarCollapsed} small={true} />
              </div>
            ))}
            {!isSidebarCollapsed && isConnected && <HistorySectionContent />}
          </nav>

          {/* Bottom: Catalog + Actions + Settings */}
          <div className="pb-4 pt-2 flex flex-col gap-1 border-t border-gray-100 dark:border-slate-800 w-full px-2">
            <SidebarItem item={settingsItem} isCollapsed={isSidebarCollapsed} small={true} />
          </div>
        </div>
        {mobileDrawer}
      </>
    );
  }

  /* ── Floating sidebar (main) ── */
  return (
    <div
      id="sidebar"
      style={{ width: isSidebarCollapsed ? 48 : 200, transition: t(['width']), willChange: 'width' }}
      className="hidden md:flex fixed left-4 top-4 h-[calc(100vh-2rem)] bg-[#FEFEFF] dark:bg-[#030712] border border-gray-200 dark:border-slate-800 rounded-2xl flex-col z-[99999] transition-colors duration-300 shadow-sm overflow-visible"
    >
      {/* Header: logo + collapse/expand button */}
      {isSidebarCollapsed ? (
        <div className="flex items-center justify-center pt-4 pb-2">
          <div
            className="relative group flex items-center justify-center cursor-pointer w-9 h-9 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800/30"
            onClick={toggleSidebar}
            title="Expand sidebar"
          >
            <img
              src={darkMode ? logo_white : logo_dark}
              alt="Realify"
              className="absolute inset-0 w-full h-full object-contain p-1 transition-opacity duration-150 group-hover:opacity-0"
            />
            <span className="opacity-0 transition-opacity duration-150 group-hover:opacity-100 text-gray-500 dark:text-slate-400">
              <IconPanelExpand size={15} />
            </span>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between px-3 pt-4 pb-2">
          <img
            src={darkMode ? LOGO2 : LOGO1}
            alt="Realify"
            className="h-8 w-auto max-w-[72px] object-contain"
          />
          <button
            onClick={toggleSidebar}
            className="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/50 transition-colors"
            title="Collapse sidebar"
          >
            <IconPanelCollapse size={15} />
          </button>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 w-full scrollbar-hide px-2 pt-2 flex flex-col gap-1 overflow-y-auto">
        {filteredNavItems.map(item => (
          <div key={item.name} className="w-full">
            <SidebarItem item={item} isCollapsed={isSidebarCollapsed} small={true} />
          </div>
        ))}
        {!isSidebarCollapsed && isConnected && <HistorySectionContent />}
      </nav>

      {/* Bottom: Catalog + Actions + Settings */}
      <div className="pb-4 pt-2 flex flex-col gap-1 border-t border-gray-100 dark:border-slate-800 w-full px-2">
        <SidebarItem item={settingsItem} isCollapsed={isSidebarCollapsed} small={true} />
      </div>
    </div>
  );
};

export default AppSidebar;
