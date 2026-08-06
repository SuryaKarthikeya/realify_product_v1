import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import SettingsInnerSidebar from '@/features/settings/components/SettingsInnerSidebar';
import SaveBar from '@/features/settings/components/SaveBar';
import SettingsSaveFooter from '@/features/settings/components/SettingsSaveFooter';
import { motion, AnimatePresence } from 'framer-motion';
import { useUIStore } from '@/store/useUIStore';

// Tabs
import AccountTab from '@/features/settings/components/tabs/AccountTab';
import TeamTab from '@/features/settings/components/tabs/TeamTab';
import InviteTeamTab from '@/features/settings/components/tabs/InviteTeamTab';
import AccessTab from '@/features/settings/components/tabs/AccessTab';
import BusinessProfileTab from '@/features/settings/components/tabs/BusinessProfileTab';
import IntegrationsTab from '@/features/settings/components/tabs/IntegrationsTab';
import GuardrailsTab from '@/features/settings/components/tabs/GuardrailsTab';
import SubscriptionTab from '@/features/settings/components/tabs/SubscriptionTab';
import BillingTab from '@/features/settings/components/tabs/BillingTab';
import NotificationsTab from '@/features/settings/components/tabs/NotificationsTab';
import PrivacyTab from '@/features/settings/components/tabs/PrivacyTab';
import AppearanceTab from '@/features/settings/components/tabs/AppearanceTab';
import RulesTab from '@/features/settings/components/tabs/RulesTab';
import ActivityTab from '@/features/settings/components/tabs/ActivityTab';

// Modals
import InviteModal from '@/features/settings/components/modals/InviteModal';
import PaymentModal from '@/features/settings/components/modals/PaymentModal';
import CustomRoleModal from '@/features/settings/components/modals/CustomRoleModal';
import ConnectModal from '@/features/settings/components/modals/ConnectModal';

/**
 * Tabs whose Save / Discard is docked to the bottom of the panel instead of
 * appearing as a floating bar plus a second copy in the page header. On these,
 * both of those are suppressed — three places to save one form is two too many.
 */
const INLINE_SAVE_TABS = new Set(['business-profile', 'access', 'guardrails', 'notifications']);

const SettingsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTabState] = useState(searchParams.get('tab') || 'account');
  const [isDirty, setIsDirty] = useState(false);

  /**
   * Mirror the open tab into ?tab= so a refresh (or a shared link) lands back on
   * it instead of resetting to Account. `replace` keeps the browser Back button
   * pointing at wherever the user came from rather than each tab they visited.
   */
  const setActiveTab = (tab) => {
    setActiveTabState(tab);
    setSearchParams({ tab }, { replace: true });
  };
  const setSidebarCollapsed = useUIStore(state => state.setSidebarCollapsed);

  // Collapse main sidebar when entering settings by default
  useEffect(() => {
    setSidebarCollapsed(true);
  }, [setSidebarCollapsed]);

  // The mobile burger-drawer settings sub-list navigates via ?tab=, not the
  // desktop sidebar's setActiveTab calls — keep activeTab in sync when it does.
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && tab !== activeTab) setActiveTabState(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);
  const [showToast, setShowToast] = useState(false);
  const [modalState, setModalState] = useState({
    invite: false,
    payment: false,
    role: false,
    connect: null // Stores the platform object if connecting
  });

  // Track changes to show save bar
  const handleInputChange = () => {
    if (!isDirty) setIsDirty(true);
  };

  const handleSave = () => {
    setIsDirty(false);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const handleDiscard = () => {
    setIsDirty(false);
    // In a real app, we would revert state here
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'account': return <AccountTab onInputChange={handleInputChange} />;
      case 'team': return <TeamTab onOpenInvite={() => setModalState({ ...modalState, invite: true })} />;
      case 'invitations': return <InviteTeamTab />;
      case 'access': return <AccessTab onInputChange={handleInputChange} onOpenRoleModal={() => setModalState({ ...modalState, role: true })} />;
      case 'business-profile': return <BusinessProfileTab onInputChange={handleInputChange} />;
      case 'integrations': return <IntegrationsTab />;
      case 'rules': return <RulesTab />;
      case 'guardrails': return <GuardrailsTab onInputChange={handleInputChange} />;
      case 'subscription': return <SubscriptionTab />;
      case 'billing': return <BillingTab onOpenPayment={() => setModalState({ ...modalState, payment: true })} />;
      case 'notifications': return <NotificationsTab onInputChange={handleInputChange} />;
      case 'privacy': return <PrivacyTab />;
      case 'appearance': return <AppearanceTab onInputChange={handleInputChange} />;
      case 'activity': return <ActivityTab />;
      default: return <AccountTab onInputChange={handleInputChange} />;
    }
  };

  const hasInlineSave = INLINE_SAVE_TABS.has(activeTab);

  const headerButtons = (
    <AnimatePresence>
      {isDirty && !hasInlineSave && (
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="flex items-center gap-2 mr-2"
        >
          <button 
            onClick={handleDiscard}
            className="px-4 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all active:scale-95"
          >
            Discard
          </button>
          <button 
            onClick={handleSave}
            className="px-6 py-2 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 shadow-lg shadow-black/10 dark:shadow-gray-700/20 transition-all flex items-center gap-2 active:scale-95"
          >
            <i className="fa-solid fa-check"></i>
            Save Changes
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <DashboardLayout 
      title="Settings" 
      subtitle="Manage your account, integrations, and preferences"
      showAIPrompt={false}
      showTabs={false}
      customRightElement={headerButtons}
      contentClassName="bg-[#f8f9fa] dark:bg-[#030712]"
      noPadding={true}
    >
      <div className="w-full px-4 lg:px-6 py-5">
        <div className="flex flex-col lg:flex-row gap-5 items-start">
          {/* Inner Sidebar Navigation */}
          <SettingsInnerSidebar activeTab={activeTab} setActiveTab={setActiveTab} onTabChange={() => setIsDirty(false)} />

          {/* Main Content Area */}
          <div className="flex-1 w-full min-w-0">
            <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-[24px] shadow-[0_1px_3px_0_rgba(0,0,0,0.05)] overflow-hidden">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {renderTabContent()}
                </motion.div>
              </AnimatePresence>

              {/* Docked to the panel, so it is the last thing in the form
                  rather than an overlay that arrives once the form is dirty. */}
              {hasInlineSave && (
                <SettingsSaveFooter
                  isDirty={isDirty}
                  onSave={handleSave}
                  onDiscard={handleDiscard}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Floating Save Bar — only for tabs that have no docked footer. */}
      <SaveBar isVisible={isDirty && !hasInlineSave} onSave={handleSave} onDiscard={handleDiscard} />

      {/* Toast Notification */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed top-6 right-6 z-[100]"
          >
            <div className="bg-green-600 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-3">
              <i className="fa-solid fa-check-circle"></i>
              <span className="text-sm font-medium">Changes saved successfully</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modals */}
      <InviteModal 
        isOpen={modalState.invite} 
        onClose={() => setModalState({ ...modalState, invite: false })} 
      />
      <PaymentModal 
        isOpen={modalState.payment} 
        onClose={() => setModalState({ ...modalState, payment: false })} 
      />
      <CustomRoleModal 
        isOpen={modalState.role} 
        onClose={() => setModalState({ ...modalState, role: false })} 
      />
      {modalState.connect && (
        <ConnectModal 
          platform={modalState.connect} 
          onClose={() => setModalState({ ...modalState, connect: null })} 
        />
      )}
    </DashboardLayout>
  );
};

export default SettingsPage;
