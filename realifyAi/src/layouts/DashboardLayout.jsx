import React, { useState, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import AppSidebar from '@/layouts/AppSidebar/AppSidebar';
import GlobalAppHeader from '@/layouts/GlobalAppHeader/GlobalAppHeader';
import AIPromptBox from '@/components/ai/AIPromptBox';
import NotificationDrawer from '@/layouts/NotificationDrawer';
import LoadingBar from '@/components/feedback/LoadingBar';
import AIResultPanel from '@/components/ai/AIResultPanel';
import { useMarketplaceStore } from '@/store/useMarketplaceStore';
import { useShopProfile } from '@/hooks/useShopProfile';
import { useDarkMode } from '@/hooks/useDarkMode';
import NoStoresConnected from '@/components/feedback/NoStoresConnected';

/** Pages that render before a store is connected, so they skip the overlay. */
const NO_STORE_EXEMPT_PREFIXES = ['/settings', '/login', '/unauthorized', '/privacy', '/terms'];

const DashboardLayout = ({
  title,
  subtitle,
  showTabs = true,
  tabs,
  filters,
  children,
  sidebarActive = true,
  showAIPrompt = true,
  hideHeader = false,
  customRightElement,
  contentClassName,
  noPadding = false,
  activeTabPath,
  tabsOnly = false,
  showSearch: _showSearch = false,
  aiPromptFullWidth = false,
  searchCollapsed = false,
  headerCenterElement = null,
  hideMobileSearchIcon = false,
}) => {
  const location = useLocation();
  const { connectedStores } = useMarketplaceStore();
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const scrollRef = useRef(null);

  const [darkMode, setDarkMode] = useDarkMode();
  const shopProfile = useShopProfile();

  // Show "no stores" overlay on all pages except settings/onboarding/auth
  const showNoStores =
    connectedStores.length === 0 &&
    location.pathname !== '/' &&
    !NO_STORE_EXEMPT_PREFIXES.some((p) => location.pathname.startsWith(p));

  return (
    /* No `dark` class here on purpose. `documentElement` is the sole carrier —
       a second copy nested inside it is what made Dark → Light fail to apply,
       because removing the outer class left this one still switching every
       `dark:` variant on. `darkMode` below is only read for asset swaps. */
    <div className="h-screen overflow-hidden flex bg-white dark:bg-[#030712]">
      <LoadingBar />
      <AIResultPanel />

      {/* Left sidebar */}
      {sidebarActive && (
        <AppSidebar
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          inline
          mobileOpen={mobileNavOpen}
          onMobileClose={() => setMobileNavOpen(false)}
        />
      )}

      {/* Right column: toolbar + content */}
      <div className="flex-1 flex flex-col min-h-0 min-w-0">

        {/* Top toolbar: title (left) + search bar + icons (right) */}
        {!hideHeader && (
          <div className="flex-shrink-0 bg-white dark:bg-[#030712]">
            <GlobalAppHeader
              title={title}
              subtitle={subtitle}
              shopProfile={shopProfile}
              onNotificationClick={() => setIsNotificationOpen(true)}
              customRightElement={customRightElement}
              searchCollapsed={searchCollapsed}
              centerElement={headerCenterElement}
              renderOnly="toolbar"
              darkMode={darkMode}
              onMenuClick={sidebarActive ? () => setMobileNavOpen(true) : undefined}
              hideMobileSearchIcon={hideMobileSearchIcon}
            />
          </div>
        )}

        {/* Content area with clean canvas background */}
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-white dark:bg-[#030712]">

          {/* Main content container */}
          <div className="flex-1 flex flex-col min-h-0 bg-white dark:bg-[#030712] overflow-hidden relative">

            {/* Secondary: tabs + filters (hidden when no stores connected) */}
            {!hideHeader && !showNoStores && (showTabs || filters) && (
              <div className="flex-shrink-0">
                <GlobalAppHeader
                  title={title}
                  subtitle={subtitle}
                  showTabs={showTabs}
                  tabs={tabs}
                  filters={filters}
                  scrollRef={scrollRef}
                  activeTabPath={activeTabPath}
                  tabsOnly={tabsOnly}
                  renderOnly="secondary"
                />
              </div>
            )}

            {/* Main page content */}
            <main
              ref={scrollRef}
              style={!showNoStores && showAIPrompt ? { paddingBottom: '8rem' } : undefined}
              className={`dashboard-main-content flex-1 overflow-y-auto overscroll-y-contain min-h-0 custom-scrollbar ${noPadding && !showNoStores ? '' : 'p-2 sm:p-2.5'
                } ${contentClassName || ''}`}
            >
              {showNoStores ? <NoStoresConnected /> : children}
            </main>

            {/* AI Prompt Background Mask */}
            {!showNoStores && showAIPrompt && (
              <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white via-white/95 to-transparent dark:from-[#030712] dark:via-[#030712]/95 pointer-events-none z-10" />
            )}
          </div>
        </div>
      </div>

      <NotificationDrawer
        isOpen={isNotificationOpen}
        onClose={() => setIsNotificationOpen(false)}
        darkMode={darkMode}
      />

      {showAIPrompt && !showNoStores && (
        <AIPromptBox
          placeholder={`Ask Realify`}
          sidebarActive={sidebarActive}
          fullWidth={aiPromptFullWidth}
        />
      )}
    </div>
  );
};

export default DashboardLayout;
