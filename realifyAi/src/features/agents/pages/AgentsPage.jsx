import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import AgentCard from '@/features/agents/components/AgentCard';
import HireSpecialistView from '@/features/agents/components/HireSpecialistView';
import { SelectAgentPrompt, SelectAgentPicker } from '@/features/agents/components/SelectAgentModal';
import AgentDetailPanel from '@/features/agents/components/AgentDetailPanel';
import LiveAgentPanel from '@/features/agents/components/LiveAgentPanel';
import LiveNowStrip from '@/features/agents/components/LiveNowStrip';
import { liveAgents } from '@/features/agents/data/agentDetailData';
import { HIRE_STEPS, CURRENT_HIRE_STEP } from '@/features/agents/data/hireSpecialistData';
import AssignCoverageStep from '@/features/agents/components/hire/AssignCoverageStep';
import ReviewLaunchStep from '@/features/agents/components/hire/ReviewLaunchStep';
import LaunchSuccessStep from '@/features/agents/components/hire/LaunchSuccessStep';
import {
  DEFAULT_COVERAGE,
  DEFAULT_AUTONOMY,
  WORKSPACES,
  TEAMS,
} from '@/features/agents/data/hireWizardData';
import { useAgentsStore } from '@/store/useAgentsStore';
import { ROUTES } from '@/constants/routes';
import { AGENTS_ROSTER, AGENT_GROUPS, agentSummary } from '@/features/agents/data/agentsData';
import { scrollDashboardToTop } from '@/hooks/useScrollIntoViewOnChange';

const TONES = {
  indigo: 'bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400',
  emerald: 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400',
};

const AgentsPage = () => {
  const [group, setGroup] = useState('All');
  const [view, setView] = useState('grid');
  const [sortAsc, setSortAsc] = useState(true);

  /**
   * The hire flow lives in the URL (`?view=hire`) so a refresh mid-hire keeps
   * the user where they were instead of dropping them back on the roster.
   *
   * `stage` is local because it is a transient dialog step, not a place:
   *   'prompt' → the small Select/Create dialog over the blurred screen
   *   'picker' → the roster dialog
   *   'ready'  → dialogs dismissed, the Hire screen fully visible
   */
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const isHiring = searchParams.get('view') === 'hire';
  const [stage, setStage] = useState('prompt');
  const [selectedAgent, setSelectedAgent] = useState(null);

  /* The wizard swaps the whole page for a new screen without changing route, so
     nothing resets the scroll position — a user who advanced from the footer
     button lands part-way down the next step. Runs on entering the flow and on
     every screen change within it. */
  useEffect(() => {
    if (isHiring) scrollDashboardToTop();
  }, [isHiring, stage]);

  /** Everything the wizard collects, carried across its three steps. */
  const [draft, setDraft] = useState({
    coverage: DEFAULT_COVERAGE,
    workspace: WORKSPACES[0].id,
    team: TEAMS[0].id,
    autonomy: DEFAULT_AUTONOMY,
  });
  const patchDraft = (patch) => setDraft((d) => ({ ...d, ...patch }));

  /* Stamped once at launch. Reading the clock during render would make the
     "Started" time creep forward on every re-render. */
  const [startedAt, setStartedAt] = useState('');

  const openHire = () => {
    setStage('prompt');
    setSelectedAgent(null);
    setDraft({
      coverage: DEFAULT_COVERAGE,
      workspace: WORKSPACES[0].id,
      team: TEAMS[0].id,
      autonomy: DEFAULT_AUTONOMY,
    });
    setSearchParams({ view: 'hire' }, { replace: true });
  };

  const closeHire = () => {
    setSearchParams({}, { replace: true });
    setStage('prompt');
    setSelectedAgent(null);
  };

  /* The agent whose detail panel is open. Opening one splits the page: roster
     left, panel right. */
  const [openAgent, setOpenAgent] = useState(null);

  const graduatedIds = useAgentsStore((s) => s.graduatedIds);
  const graduateAgent = useAgentsStore((s) => s.graduateAgent);

  const summary = useMemo(() => agentSummary(graduatedIds), [graduatedIds]);

  /* Which top strip to show. Only graduated specialists are live, so a
     first-time visitor has an empty strip and gets the five-step hire rail in
     its place instead. */
  const live = useMemo(() => liveAgents(graduatedIds), [graduatedIds]);
  const hasLiveAgents = live.length > 0;

  /**
   * Confirm and Launch. This is what actually hires the specialist, so it is
   * where graduation happens — the Active count and the Live Now strip both read
   * from that list.
   */
  const handleLaunch = () => {
    if (selectedAgent) {
      graduateAgent(selectedAgent.id);
      setOpenAgent(selectedAgent);
    }
    setStartedAt(
      `Today, ${new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
    );
    setStage('launched');
  };

  // Filter, then sort. `localeCompare` so 'Bidding & Ads' orders naturally.
  const visible = useMemo(() => {
    const rows = group === 'All'
      ? AGENTS_ROSTER
      : AGENTS_ROSTER.filter((a) => a.group === group);
    return [...rows].sort((a, b) =>
      sortAsc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name)
    );
  }, [group, sortAsc]);

  /* Card columns. Two per row in the 60% column beside an open panel; three or
     four across the full-width roster, which is as many as fit before the name
     and the status badge start fighting for the same line. */
  const rosterClass = view === 'list'
    ? 'space-y-3'
    : openAgent
      ? 'grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4'
      : 'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3 sm:gap-4';

  const layoutProps = {
    showTabs: false,
    showAIPrompt: true,
    showSearch: false,
  };

  /* ── Hire a specialist ──
     One flow, four screens, driven by `stage`:
       prompt / picker / ready → the specialist preview, dialogs over a blur
       coverage                → assign coverage, team and trust
       review                  → read-only summary
       launched                → the specialist is live
     The preview renders underneath the dialogs so the user keeps the context
     they are about to fill in. */
  if (isHiring) {
    if (stage === 'launched') {
      return (
        <DashboardLayout {...layoutProps}>
          <LaunchSuccessStep
            agent={selectedAgent}
            draft={draft}
            startedAt={startedAt}
            onBackToAgents={closeHire}
            /* Land back on the roster with this specialist selected — it is now
               live, so its panel is the live one. `openAgent` was already set at
               launch, so closing the flow is enough to reveal it. */
            onOpenSpecialist={closeHire}
            onReturn={closeHire}
          />
        </DashboardLayout>
      );
    }

    if (stage === 'review') {
      return (
        <DashboardLayout {...layoutProps}>
          <ReviewLaunchStep
            agent={selectedAgent}
            draft={draft}
            onBack={() => setStage('coverage')}
            onEdit={() => setStage('coverage')}
            onLaunch={handleLaunch}
            onSaveDraft={closeHire}
          />
        </DashboardLayout>
      );
    }

    if (stage === 'coverage') {
      return (
        <DashboardLayout {...layoutProps}>
          <AssignCoverageStep
            agent={selectedAgent}
            draft={draft}
            onChange={patchDraft}
            onBack={() => setStage('ready')}
            onContinue={() => setStage('review')}
            onSaveDraft={closeHire}
          />
        </DashboardLayout>
      );
    }

    return (
      <DashboardLayout
        {...layoutProps}
        title="Hire a specialist"
        subtitle="Build your AI specialist in five simple steps. Every hire starts at Observe."
      >
        <HireSpecialistView
          agent={selectedAgent}
          currentStep={CURRENT_HIRE_STEP}
          onCancel={closeHire}
          onContinue={() => setStage('coverage')}
          onViewAll={closeHire}
          onViewAgents={closeHire}
        />

        {stage === 'prompt' && (
          <SelectAgentPrompt
            onSelectAgent={() => setStage('picker')}
            onCreateAgent={() => setStage('picker')}
            onClose={closeHire}
          />
        )}

        {stage === 'picker' && (
          <SelectAgentPicker
            onPick={(agent) => { setSelectedAgent(agent); setStage('ready'); }}
            onCreateAgent={() => setStage('ready')}
            onClose={() => setStage('prompt')}
          />
        )}
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      {...layoutProps}
      title={
        <div className="flex items-center gap-2.5">
          <span>Agents</span>
          <span className="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-[11.5px] font-bold tracking-normal">
            {AGENTS_ROSTER.length}
          </span>
        </div>
      }
      subtitle="Your AI team is working around the clock to grow your business."
    >
      <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 space-y-4 font-sans">

        {/* ── Page header ── */}
        <div className="flex justify-end">
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <button
              onClick={openHire}
              className="px-3.5 py-1.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50/60 dark:hover:bg-indigo-950/30 transition-colors flex items-center gap-2 whitespace-nowrap"
            >
              <i className="fa-solid fa-user-plus text-[12px]" /> Hire a Specialist
            </button>
          </div>
        </div>

        {/* ── Summary tiles ── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {summary.map((tile) => (
            <div
              key={tile.key}
              className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl px-4 py-3.5 flex items-center gap-3.5"
            >
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${TONES[tile.tone]}`}>
                <i className={`fa-solid ${tile.icon} text-[15px]`} />
              </div>
              <div className="min-w-0">
                <p className="text-[20px] font-bold text-gray-900 dark:text-white leading-none">
                  {tile.value}
                </p>
                <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mt-1">{tile.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* ── Top strip ──
            Three states, in priority order:
              1. Something graduated  → Live Now
              2. Nothing graduated, a detail panel open → the ramp rail, giving
                 the panel context on where that specialist sits
              3. Nothing graduated, no panel → no strip at all. This is the
                 first-visit screen: tiles straight into the roster. */}
        {hasLiveAgents ? (
          <LiveNowStrip agents={live} />
        ) : openAgent ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-y-4 relative pt-1">
            <div className="hidden lg:block absolute top-[17px] left-[10%] right-[10%] h-[1px] bg-gray-200 dark:bg-slate-700" />
            {HIRE_STEPS.map((step, idx) => {
              const isDone = idx < CURRENT_HIRE_STEP;
              const isActive = idx === CURRENT_HIRE_STEP;
              return (
                <div key={step.key} className="flex flex-col items-center text-center px-3 relative z-10">
                  <div
                    className={`w-[26px] h-[26px] rounded-full flex items-center justify-center text-[11px] font-bold mb-2 flex-shrink-0 ${
                      isDone
                        ? 'bg-emerald-500 text-white'
                        : isActive
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-400 dark:text-slate-500'
                    }`}
                  >
                    {isDone ? <i className="fa-solid fa-check text-[10px]" /> : idx + 1}
                  </div>
                  <p className={`text-[12.5px] font-bold mb-1 ${isDone || isActive ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-slate-500'}`}>
                    {step.label}
                  </p>
                  <p className="text-[10.5px] text-gray-400 dark:text-slate-500 leading-relaxed max-w-[170px]">
                    {step.description}
                  </p>
                </div>
              );
            })}
          </div>
        ) : null}

        {/* ── Roster + detail panel ──
            Roster on the left at 60%, the open specialist's panel on the right
            at 40%.

            The split is flex-[3] / flex-[2] rather than w-[60%] / w-[40%]:
            percentages plus the 16px gap would total more than the row, so the
            columns would overflow or silently shrink off-ratio. Growth factors
            divide what is left after the gap, so 3:2 is exactly 60:40.

            Neither column is a fixed-height sidebar — both grow with their
            content and the page scrolls, so neither has a scroller of its own. */}
        <div className={openAgent ? 'flex flex-col xl:flex-row gap-4 items-start' : ''}>

          <div className={`min-w-0 space-y-4 ${openAgent ? 'w-full xl:flex-[3]' : ''}`}>

        {/* ── Group tabs + sort / view controls ── */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
            {AGENT_GROUPS.map((g) => (
              <button
                key={g}
                onClick={() => setGroup(g)}
                className={`px-3.5 py-1.5 rounded-lg text-[13px] font-semibold whitespace-nowrap transition-colors ${group === g
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800'
                  }`}
              >
                {g}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <button
              onClick={() => setSortAsc((v) => !v)}
              className="text-[12.5px] font-medium text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors whitespace-nowrap"
            >
              Sort: {sortAsc ? 'A to Z' : 'Z to A'}
            </button>

            <div className="flex items-center rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
              {[
                { key: 'list', icon: 'fa-list' },
                { key: 'grid', icon: 'fa-table-cells-large' },
              ].map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => setView(opt.key)}
                  aria-label={`${opt.key} view`}
                  aria-pressed={view === opt.key}
                  className={`w-8 h-7 flex items-center justify-center transition-colors ${view === opt.key
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

        {/* ── Roster ── */}
        {visible.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center py-10">
            <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
              <i className="fa-solid fa-user-slash text-[15px]" />
            </div>
            <p className="text-[13.5px] font-bold text-gray-800 dark:text-slate-200 mb-1">
              No specialists in {group}
            </p>
            <p className="text-[12.5px] text-gray-500 dark:text-slate-400 max-w-[340px] leading-relaxed">
              Hire a specialist for this area, or switch to All to see your whole team.
            </p>
          </div>
        ) : (
          <div className={rosterClass}>
            {visible.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                view={view}
                onSelect={setOpenAgent}
                isSelected={openAgent?.id === agent.id}
              />
            ))}
          </div>
        )}
          </div>

          {openAgent && (
            <div className="w-full min-w-0 xl:flex-[2] animate-in fade-in slide-in-from-right-4 duration-300">
              {/* A graduated specialist is reported on differently from one still
                  in Shadow — ramp bar and graduation gates no longer apply — so
                  liveness picks the panel. */}
              {graduatedIds.includes(openAgent.id) ? (
                <LiveAgentPanel
                  agent={openAgent}
                  onClose={() => setOpenAgent(null)}
                  onViewProfile={() =>
                    navigate(ROUTES.AGENT_PROFILE.replace(':agentId', openAgent.id))
                  }
                />
              ) : (
                <AgentDetailPanel
                  agent={openAgent}
                  onClose={() => setOpenAgent(null)}
                  /* Assigning is what takes a graduated specialist live: it joins
                     `graduatedIds`, so it heads the Live Now strip and this panel
                     flips to the live one on the next render. The panel itself
                     keeps the button locked until the trust dial reaches
                     Graduate, so this only ever fires on a ready specialist. */
                  onAssign={() => graduateAgent(openAgent.id)}
                  /* The decisions this specialist is producing live on the Shadow
                     step of the hire flow — the rail sits at step 3 with Connect
                     and Baseline behind it. Seeded with this specialist rather
                     than the placeholder the screen defaults to. */
                  onViewDecisions={() => {
                    setSelectedAgent(openAgent);
                    setStage('ready');
                    setSearchParams({ view: 'hire' }, { replace: true });
                  }}
                  /* Full profile page, which opens on Overview. A real route, so
                     it survives a refresh and can be linked to. */
                  onViewProfile={() =>
                    navigate(ROUTES.AGENT_PROFILE.replace(':agentId', openAgent.id))
                  }
                />
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AgentsPage;
