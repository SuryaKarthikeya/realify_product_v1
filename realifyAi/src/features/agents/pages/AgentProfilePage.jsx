import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import { AGENTS_ROSTER, agentStatusLabel } from '@/features/agents/data/agentsData';
import {
  agentProfile,
  PROFILE_TABS,
  ACTIVITY_TONES,
  EXECUTION_RHYTHM,
  RHYTHM_STATE_TONES,
  CONNECTED_AGENTS,
  CONNECTED_OVERFLOW,
} from '@/features/agents/data/agentProfileData';
import TriggersTab from '@/features/agents/components/TriggersTab';
import { ROUTES } from '@/constants/routes';

const STAT_TONES = {
  indigo: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400',
  amber: 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400',
  violet: 'bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400',
  emerald: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400',
};

/**
 * Agent settings card. Shared by Overview and Triggers, which both show it in
 * the sidebar — duplicating it is how the two would drift apart.
 */
const SettingsCard = ({ settings }) => (
  <div className="rounded-2xl border border-gray-100 dark:border-slate-800 bg-gradient-to-b from-emerald-50/40 to-white dark:from-emerald-950/10 dark:to-slate-900 p-4">
    <div className="flex items-center justify-between gap-2 mb-4">
      <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Agent settings</h3>
      <button className="text-[11.5px] font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 flex items-center gap-1.5">
        View settings <i className="fa-solid fa-arrow-right text-[9px]" />
      </button>
    </div>

    <div className="space-y-3.5">
      {settings.map((row) => (
        <div key={row.key} className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2.5 min-w-0">
            <i className={`fa-solid ${row.icon} text-[11px] text-gray-400 dark:text-slate-500 w-3.5 text-center flex-shrink-0`} />
            <span className="text-[12px] text-gray-600 dark:text-slate-400">{row.label}</span>
          </div>

          {row.chip ? (
            <span className="px-2 py-0.5 rounded bg-emerald-100/70 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 text-[9.5px] font-bold uppercase tracking-wider whitespace-nowrap flex-shrink-0">
              {row.value}
            </span>
          ) : (
            <span className="text-[12px] font-bold text-gray-900 dark:text-white text-right flex items-center gap-1.5 flex-shrink-0">
              {row.dot && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
              {row.value}
            </span>
          )}
        </div>
      ))}
    </div>
  </div>
);

/** Placeholder body for the tabs that have no design yet. */
const TabPlaceholder = ({ tab }) => (
  <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-10 flex flex-col items-center text-center px-5">
    <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
      <i className="fa-solid fa-layer-group text-[15px]" />
    </div>
    <p className="text-[13.5px] font-bold text-gray-800 dark:text-slate-200 mb-1">{tab}</p>
    <p className="text-[12.5px] text-gray-500 dark:text-slate-400 max-w-[340px] leading-relaxed">
      This tab has no design yet. Everything the Overview shows is already wired to
      this specialist, so {tab} can be built on the same data.
    </p>
  </div>
);

/**
 * Full profile for one specialist, reached from "View decisions" in the roster's
 * detail panel.
 *
 * The agent comes from the route (`/agents/:agentId`) rather than component
 * state, so the page survives a refresh and can be linked to directly.
 */
const AgentProfilePage = () => {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState('Overview');

  const agent = AGENTS_ROSTER.find((a) => a.id === agentId);
  const profile = agentProfile(agent);

  const backToAgents = () => navigate(ROUTES.AGENTS);

  /* An unknown id is a dead link, not a crash — offer the way back. */
  if (!agent) {
    return (
      <DashboardLayout showTabs={false} showAIPrompt={false} showSearch={false}>
        <div className="max-w-[900px] mx-auto px-5 py-12 flex flex-col items-center text-center">
          <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
            <i className="fa-solid fa-user-slash text-[15px]" />
          </div>
          <p className="text-[14px] font-bold text-gray-800 dark:text-slate-200 mb-1">
            No such specialist
          </p>
          <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mb-5">
            <span className="font-mono">{agentId}</span> is not on your team.
          </p>
          <button
            onClick={backToAgents}
            className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors"
          >
            Back to Agents
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout showTabs={false} showAIPrompt showSearch={false}>
      <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 font-sans">

        <button
          onClick={backToAgents}
          className="text-[12.5px] font-semibold text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-200 transition-colors flex items-center gap-2 mb-5"
        >
          <i className="fa-solid fa-chevron-left text-[10px]" /> Back to Agents
        </button>

        {/* ── Identity ── */}
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex items-start gap-4 min-w-0">
            <div className="w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0 text-[13px] font-bold">
              {agent.initials}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-[22px] font-bold text-gray-900 dark:text-white tracking-tight">
                  {agent.name}
                </h1>
                {/* Same rule as the roster card — Active only once the ramp is done. */}
                <span
                  className={`px-2 py-0.5 rounded text-[9.5px] font-bold uppercase tracking-wider ${
                    agentStatusLabel(agent) === 'Active'
                      ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400'
                      : 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'
                  }`}
                >
                  {agentStatusLabel(agent)}
                </span>
              </div>
              <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mt-1">
                {agent.name} Specialist &nbsp;•&nbsp; {profile.tagline}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="text-right hidden sm:block">
              <p className="text-[11.5px] text-gray-400 dark:text-slate-500">
                On the team since {profile.since}
              </p>
              <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">
                {profile.decisionsLogged.toLocaleString('en-US')} decisions logged
              </p>
            </div>
            <button className="px-4 py-2 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors">
              Pause
            </button>
            <button className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-[13px] font-bold transition-colors">
              Edit agent
            </button>
          </div>
        </div>

        {/* ── Tabs ── */}
        <div className="border-b border-gray-200 dark:border-slate-800 mt-5">
          <div className="flex items-center gap-5 overflow-x-auto scrollbar-hide">
            {PROFILE_TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`py-3 text-[13px] font-semibold whitespace-nowrap transition-colors relative ${
                  tab === t
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200'
                }`}
              >
                {t}
                {tab === t && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-blue-600 dark:bg-blue-400 rounded-t-sm" />
                )}
              </button>
            ))}
          </div>
        </div>

        {tab === 'Triggers' ? (
          <div className="flex flex-col xl:flex-row gap-5 items-start mt-5">
            <div className="flex-1 min-w-0 w-full">
              <TriggersTab agent={agent} />
            </div>
            <div className="w-full xl:w-[400px] xl:flex-shrink-0">
              <SettingsCard settings={profile.settings} />
            </div>
          </div>
        ) : tab !== 'Overview' ? (
          <div className="mt-5">
            <TabPlaceholder tab={tab} />
          </div>
        ) : (
          <div className="flex flex-col xl:flex-row gap-5 items-start mt-5">

            {/* ── Main column ── */}
            <div className="flex-1 min-w-0 w-full space-y-5">

              {/* Doing now */}
              <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <h2 className="text-[13.5px] font-bold text-gray-900 dark:text-white">
                    What this agent is doing now
                  </h2>
                  <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Live
                  </span>
                </div>

                <div className="flex flex-col lg:flex-row gap-6">
                  <p className="text-[13px] text-gray-600 dark:text-slate-400 leading-relaxed flex-1 min-w-0">
                    {profile.summary}
                  </p>

                  <div className="lg:border-l lg:border-gray-100 dark:lg:border-slate-800 lg:pl-6 flex-shrink-0">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">
                      {profile.stats.map((stat) => (
                        <div key={stat.key} className="text-center min-w-0">
                          <div
                            className={`w-9 h-9 rounded-xl flex items-center justify-center mx-auto mb-2.5 ${STAT_TONES[stat.tone]}`}
                          >
                            <i className={`fa-solid ${stat.icon} text-[13px]`} />
                          </div>
                          <p className="text-[19px] font-bold text-gray-900 dark:text-white leading-none">
                            {stat.value}
                          </p>
                          <p className="text-[9.5px] text-gray-400 dark:text-slate-500 leading-tight mt-2 max-w-[92px] mx-auto">
                            {stat.label}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Latest activity */}
              <div className="rounded-2xl bg-gray-50/70 dark:bg-slate-800/30 border border-gray-100 dark:border-slate-800 p-5">
                <h2 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-4">
                  Latest activity
                </h2>

                <div className="space-y-1">
                  {profile.activity.map((row) => {
                    const tone = ACTIVITY_TONES[row.tone] || ACTIVITY_TONES.info;
                    return (
                      <button
                        key={row.time + row.title}
                        className="w-full flex items-center gap-4 py-2.5 text-left rounded-lg hover:bg-white/70 dark:hover:bg-slate-900/40 transition-colors px-2 -mx-2"
                      >
                        <span className="text-[11px] text-gray-400 dark:text-slate-500 w-[62px] flex-shrink-0 tabular">
                          {row.time}
                        </span>

                        <span
                          className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${tone.bg} ${tone.fg}`}
                        >
                          <i className={`fa-solid ${tone.icon} text-[10px]`} />
                        </span>

                        <span className="min-w-0 flex-1">
                          <span className="block text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug truncate">
                            {row.title}
                          </span>
                          <span className="block text-[11px] text-gray-400 dark:text-slate-500 truncate">
                            {row.sub}
                          </span>
                        </span>

                        {row.value ? (
                          <span className={`text-[12px] font-bold whitespace-nowrap ${tone.chip}`}>
                            {row.value}
                          </span>
                        ) : (
                          <span
                            className={`text-[9.5px] font-bold uppercase tracking-wider whitespace-nowrap ${tone.chip}`}
                          >
                            {row.badge}
                          </span>
                        )}

                        <i className="fa-solid fa-chevron-right text-[9px] text-gray-300 dark:text-slate-600 flex-shrink-0" />
                      </button>
                    );
                  })}
                </div>

                <button className="text-[12px] font-bold text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-200 transition-colors flex items-center gap-2 mt-4">
                  See full timeline <i className="fa-solid fa-arrow-right text-[10px]" />
                </button>
              </div>

              {/* Execution rhythm */}
              <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
                <h2 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-5">
                  Execution rhythm
                </h2>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-y-6 relative">
                  {/* Hairline behind the markers, inset so it stops at the outer nodes */}
                  <div className="hidden lg:block absolute top-[15px] left-[12.5%] right-[12.5%] h-[1px] bg-gray-200 dark:bg-slate-700" />

                  {EXECUTION_RHYTHM.map((stage) => (
                    <div key={stage.key} className="flex flex-col items-center text-center px-2 relative z-10">
                      {stage.state === 'DONE' ? (
                        <span className="w-8 h-8 rounded-full border-2 border-emerald-500 bg-white dark:bg-slate-900 text-emerald-500 flex items-center justify-center mb-3">
                          <i className="fa-solid fa-check text-[11px]" />
                        </span>
                      ) : (
                        <span className="w-8 h-8 rounded-full border-2 border-indigo-400 dark:border-indigo-600 bg-white dark:bg-slate-900 flex items-center justify-center mb-3">
                          <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                        </span>
                      )}

                      <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug">
                        {stage.label}
                      </p>
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider my-2 ${RHYTHM_STATE_TONES[stage.state]}`}
                      >
                        {stage.state}
                      </span>
                      <p className="text-[10.5px] text-gray-400 dark:text-slate-500 leading-relaxed max-w-[140px]">
                        {stage.description}
                      </p>
                    </div>
                  ))}
                </div>

                <p className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mt-5 pt-4 border-t border-gray-100 dark:border-slate-800">
                  Next run scheduled: Today, 6:00 AM
                </p>
              </div>
            </div>

            {/* ── Sidebar ── */}
            <div className="w-full xl:w-[400px] xl:flex-shrink-0 space-y-4">

              <SettingsCard settings={profile.settings} />

              {/* Mission */}
              <div className="rounded-2xl bg-indigo-600 p-4 flex items-start gap-4">
                <span className="w-9 h-9 rounded-lg bg-white/20 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-[9.5px] font-bold text-indigo-200 uppercase tracking-wider mb-1.5">
                    Mission
                  </p>
                  <p className="text-[15px] font-bold text-white leading-snug">
                    {profile.mission}
                  </p>
                </div>
              </div>

              {/* Connected agents */}
              <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
                <div className="flex items-center justify-between gap-2 mb-5">
                  <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">
                    Connected agents
                  </h3>
                  <button
                    onClick={backToAgents}
                    className="text-[11.5px] font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 flex items-center gap-1.5"
                  >
                    View all <i className="fa-solid fa-arrow-right text-[9px]" />
                  </button>
                </div>

                <div className="grid grid-cols-4 gap-4">
                  {CONNECTED_AGENTS.map((peer) => (
                    <div key={peer.key} className="flex flex-col items-center text-center min-w-0">
                      <span
                        className={`w-10 h-10 rounded-xl ${peer.bg} text-white flex items-center justify-center mb-2 flex-shrink-0`}
                      >
                        <i className={`fa-solid ${peer.icon} text-[13px]`} />
                      </span>
                      <span className="text-[9.5px] text-gray-500 dark:text-slate-400 leading-tight">
                        {peer.label}
                      </span>
                    </div>
                  ))}

                  <div className="flex flex-col items-center text-center">
                    <span className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400 flex items-center justify-center mb-2 text-[12px] font-bold flex-shrink-0">
                      +{CONNECTED_OVERFLOW}
                    </span>
                    <span className="text-[9.5px] text-gray-500 dark:text-slate-400 leading-tight">
                      More
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AgentProfilePage;
