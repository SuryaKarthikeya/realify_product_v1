import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import ConnectorRail from '@/features/integrations/components/detail/ConnectorRail';
import OverviewTab from '@/features/integrations/components/detail/OverviewTab';
import OnboardingTab from '@/features/integrations/components/detail/OnboardingTab';
import ScopesTab from '@/features/integrations/components/detail/ScopesTab';
import ScopesRail from '@/features/integrations/components/detail/ScopesRail';
import ActivityTab from '@/features/integrations/components/detail/ActivityTab';
import ActivityRail from '@/features/integrations/components/detail/ActivityRail';
import DataTab from '@/features/integrations/components/detail/DataTab';
import DataRail from '@/features/integrations/components/detail/DataRail';
import SettingsTab from '@/features/integrations/components/detail/SettingsTab';
import SettingsRail from '@/features/integrations/components/detail/SettingsRail';
import { CONNECTORS, CATEGORY_BY_KEY, isOnboarded } from '@/features/integrations/data/integrationsData';
import {
  DETAIL_PAGE_TABS,
  JOURNEY_STEPS,
  ACTIVITY_TYPES,
  ACTIVITY_STATUS_FILTERS,
  DATASET_STATUS_FILTERS,
} from '@/features/integrations/data/connectorDetailData';
import { ROUTES } from '@/constants/routes';
import { useIntegrationsStore, useSetupComplete } from '@/store/useIntegrationsStore';

/** Tabs with no design yet still say something useful about this connector. */
const TabPlaceholder = ({ tab, connector }) => (
  <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-12 flex flex-col items-center text-center px-5">
    <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
      <i className="fa-solid fa-layer-group text-[15px]" />
    </div>
    <p className="text-[13.5px] font-bold text-gray-800 dark:text-slate-200 mb-1">{tab}</p>
    <p className="text-[12.5px] text-gray-500 dark:text-slate-400 max-w-[400px] leading-relaxed">
      This tab has no design yet. Everything the Overview shows is already wired to{' '}
      {connector.name}, so {tab} can be built on the same data.
    </p>
  </div>
);

/**
 * One connector, in full — the screen "Resume Setup" opens.
 *
 * The active tab and the wizard step both live in the URL, so a refresh keeps the
 * user where they were and a given step can be linked to.
 */
const ConnectorDetailPage = () => {
  const { connectorId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const connector = CONNECTORS.find((c) => c.id === connectorId);

  const tabParam = searchParams.get('tab');
  const tab = DETAIL_PAGE_TABS.includes(tabParam) ? tabParam : DETAIL_PAGE_TABS[0];

  const stepParam = Number(searchParams.get('step'));
  const [step, setStepState] = useState(
    Number.isInteger(stepParam) && stepParam >= 1 && stepParam <= 5 ? stepParam - 1 : 0
  );

  const setTab = (next) => {
    const params = { tab: next };
    /* Keep the step in the URL only while it is meaningful. */
    if (next === 'Onboarding') params.step = String(step + 1);
    setSearchParams(params, { replace: true });
  };

  const setStep = (next) => {
    setStepState(next);
    setSearchParams({ tab: 'Onboarding', step: String(next + 1) }, { replace: true });
  };

  /* Lifted so the rail's Type/Status controls and the log they narrow stay one
     source of truth rather than two copies that can drift. */
  const [activityFilters, setActivityFilters] = useState({
    type: ACTIVITY_TYPES[0],
    status: ACTIVITY_STATUS_FILTERS[0],
  });

  /* Data gets its own pair rather than sharing Activity's: the Type lists are
     different (feeds vs event kinds), so one shared value would read as a filter
     the other tab cannot honour. */
  const [dataFilters, setDataFilters] = useState({
    type: 'All types',
    status: DATASET_STATUS_FILTERS[0],
  });

  const setupComplete = useSetupComplete(connectorId);
  const completeSetup = useIntegrationsStore((s) => s.completeSetup);

  /*
   * Reaching Go live is what completes setup, and it has to outlive this page —
   * the catalogue button and the journey rail both read it back. Recorded from an
   * effect rather than from the Continue handler so arriving at the last step by
   * any route (deep link, refresh on ?step=5) leaves the app in the same state the
   * screen is claiming. The store ignores repeats, so re-running is harmless.
   */
  useEffect(() => {
    if (tab === 'Onboarding' && step >= JOURNEY_STEPS.length - 1) completeSetup(connectorId);
  }, [tab, step, connectorId, completeSetup]);

  /* Derived, not stored: a connector can be done because the user just finished
     it (`setupComplete`) or because it was already live when they arrived. Both
     have to suppress the wizard, so the question is asked in one place. */
  const onboarded = isOnboarded(connector, setupComplete);

  const backToIntegrations = () => navigate(ROUTES.INTEGRATIONS);

  if (!connector) {
    return (
      <DashboardLayout showTabs={false} showAIPrompt={false}>
        <div className="max-w-[900px] mx-auto px-5 py-12 flex flex-col items-center text-center">
          <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
            <i className="fa-solid fa-plug-circle-xmark text-[15px]" />
          </div>
          <p className="text-[14px] font-bold text-gray-800 dark:text-slate-200 mb-1">
            No such connector
          </p>
          <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mb-5">
            <span className="font-mono">{connectorId}</span> is not in the catalogue.
          </p>
          <button
            onClick={backToIntegrations}
            className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/30 transition-colors"
          >
            Back to Integrations
          </button>
        </div>
      </DashboardLayout>
    );
  }

  const isLive = connector.status !== 'available';
  const needsAttention = connector.status === 'attention';
  const categoryLabel = CATEGORY_BY_KEY[connector.category] || connector.category;

  const onOnboarding = tab === 'Onboarding';
  const onScopes = tab === 'Scopes & Permissions';
  const onActivity = tab === 'Activity';
  const onData = tab === 'Data';
  const onSettings = tab === 'Settings';
  const lastStep = JOURNEY_STEPS.length - 1;

  /* Mid-wizard the rail's journey card would just restate the step rail already
     on screen, so it is held back until the last step, where it reports the
     finished journey instead of duplicating a live one. */
  const showJourney = !onOnboarding || onboarded || step === lastStep;

  return (
    <DashboardLayout showTabs={false} showAIPrompt={false}>
      <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 font-sans">

        <button
          onClick={backToIntegrations}
          className="text-[12.5px] font-semibold text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-200 transition-colors flex items-center gap-2 mb-4"
        >
          <i className="fa-solid fa-arrow-left text-[10px]" /> Back to Integrations
        </button>

        {/* ── Identity ── */}
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex items-start gap-3.5 min-w-0">
            <span className={`w-11 h-11 rounded-full flex-shrink-0 flex items-center justify-center text-[18px] ${connector.tone}`}>
              <i className={connector.icon} />
            </span>

            <div className="min-w-0">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-[19px] font-bold text-gray-900 dark:text-white tracking-tight">
                  {connector.name}
                </h1>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold whitespace-nowrap ${
                    needsAttention
                      ? 'bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400'
                      : isLive
                        ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400'
                        : 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'
                  }`}
                >
                  {needsAttention ? 'Attention' : isLive ? 'Connected' : 'Available'}
                </span>
              </div>

              <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1">
                {categoryLabel}
                <span className="mx-1.5 text-gray-300 dark:text-slate-600">•</span>
                Feeds: {connector.feeds.join(' · ')}
              </p>

              <p className="text-[12px] mt-1 flex items-center gap-1.5 flex-wrap">
                <span className={`w-1.5 h-1.5 rounded-full ${needsAttention ? 'bg-amber-500' : isLive ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-slate-600'}`} />
                <span className={`font-semibold ${needsAttention ? 'text-amber-600 dark:text-amber-400' : isLive ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400 dark:text-slate-500'}`}>
                  {needsAttention ? 'Degraded' : isLive ? 'Healthy' : 'Not connected'}
                </span>
                <span className="text-gray-300 dark:text-slate-600">·</span>
                <span className="text-gray-500 dark:text-slate-400">
                  {isLive ? `Last sync ${connector.lastSync}` : 'Never synced'}
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
            <button className="px-3.5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12.5px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap">
              <i className="fa-solid fa-gear text-[11px]" /> Manage connector
            </button>
            {/* Hidden while the wizard is open: the step's own footer button is
                what advances the flow there, and a second Connect in the header
                would be a competing, ambiguous call to action.

                Once every step is done there is nothing left to connect, so the
                button stops being an action and becomes the answer: Connected,
                with a tick. Same padding and text size as the button it replaces
                so the header does not reflow when it flips. */}
            {!onOnboarding && (
              onboarded && connector.status !== 'attention' ? (
                <span className="px-3.5 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-400 text-[12.5px] font-bold flex items-center gap-2 whitespace-nowrap">
                  <i className="fa-solid fa-circle-check text-[12px]" /> Connected
                </span>
              ) : (
                <button
                  onClick={() => setTab('Onboarding')}
                  className="px-3.5 py-2 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[12.5px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center gap-2 whitespace-nowrap"
                >
                  Connect <i className="fa-solid fa-arrow-right text-[10px]" />
                </button>
              )
            )}
            <button
              aria-label="More options"
              className="w-9 h-9 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center flex-shrink-0"
            >
              <i className="fa-solid fa-ellipsis-vertical text-[12px]" />
            </button>
          </div>
        </div>

        {/* ── Tabs ── */}
        <div className="border-b border-gray-200 dark:border-slate-800 mt-4">
          <div className="flex items-center gap-6 overflow-x-auto scrollbar-hide">
            {DETAIL_PAGE_TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`py-2.5 text-[12.5px] font-semibold whitespace-nowrap transition-colors relative ${
                  tab === t
                    ? 'text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200'
                }`}
              >
                {t}
                {tab === t && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-indigo-600 dark:bg-indigo-400 rounded-t-sm" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* ── Content + rail ──
            ~64 / 36 via flex-[9] / flex-[5]. The rail is persistent across tabs
            because "where am I in setup" is not a per-tab question. */}
        <div className="flex flex-col xl:flex-row gap-4 items-start mt-4">
          <div className="min-w-0 w-full xl:flex-[9]">
            {tab === 'Overview' && <OverviewTab connector={connector} />}

            {tab === 'Onboarding' && (
              <OnboardingTab
                connector={connector}
                step={step}
                setStep={setStep}
                onboarded={onboarded}
                onExit={backToIntegrations}
                onGoToOverview={() => setTab('Overview')}
              />
            )}

            {onScopes && <ScopesTab connector={connector} />}

            {onActivity && <ActivityTab connector={connector} filters={activityFilters} />}

            {onData && <DataTab connector={connector} filters={dataFilters} />}

            {onSettings && <SettingsTab connector={connector} />}

            {!onOnboarding && !onScopes && !onActivity && !onData && !onSettings && tab !== 'Overview' && (
              <TabPlaceholder tab={tab} connector={connector} />
            )}
          </div>

          <div className="w-full xl:w-auto xl:flex-[5] min-w-0">
            {onScopes ? (
              <ScopesRail connector={connector} />
            ) : onActivity ? (
              <ActivityRail
                connector={connector}
                filters={activityFilters}
                onChange={setActivityFilters}
              />
            ) : onData ? (
              <DataRail
                connector={connector}
                filters={dataFilters}
                onChange={setDataFilters}
              />
            ) : onSettings ? (
              <SettingsRail connector={connector} onViewActivity={() => setTab('Activity')} />
            ) : (
            <ConnectorRail
              connector={connector}
              /* The rail's journey advances with the wizard, so the two can never
                 disagree about how far setup has got. */
              wizardStep={onOnboarding ? step : 0}
              setupComplete={setupComplete}
              showJourney={showJourney}
              onViewAllActivity={() => setTab('Activity')}
            />
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ConnectorDetailPage;
