import React, { useMemo, useState } from 'react';
import CsvUploadButton from '@/features/integrations/components/detail/CsvUploadButton';
import {
  AUTHORIZE_PILLARS,
  CONSENT_BLOCKS,
  GO_LIVE_NEXT,
  JOURNEY_STEPS,
  SCOPE_SEGMENTS,
  authorizeNextSteps,
  chooseConnectorCard,
  providerName,
  readScopes,
  writePermissions,
} from '@/features/integrations/data/connectorDetailData';

/**
 * The five-node rail. Everything before the current step reads as complete.
 *
 * `allDone` is the finished state: every node carries a tick instead of its
 * number, because a rail of numbers with nothing current on it reads as a journey
 * still waiting to be started.
 */
const StepRail = ({ step, allDone = false }) => (
  <div className="relative">
    <div className="grid grid-cols-5">
      {JOURNEY_STEPS.map((s, idx) => {
        const isDone = allDone || idx < step;
        const isCurrent = !allDone && idx === step;
        const reached = isDone || isCurrent;
        return (
          <div key={s.key} className="flex flex-col items-center text-center px-1 relative">
            {/* Connector drawn per node so it never overshoots the ends, and is
                tinted only where the journey has actually been. */}
            {idx > 0 && (
              <span
                className={`absolute top-[13px] right-1/2 left-[-50%] h-[2px] ${
                  allDone
                    ? 'bg-emerald-500'
                    : reached
                      ? 'bg-gray-900 dark:bg-slate-200'
                      : 'bg-gray-200 dark:bg-slate-700'
                }`}
              />
            )}

            <div
              className={`relative z-10 w-[26px] h-[26px] rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 ${
                allDone
                  ? 'bg-emerald-500 text-white'
                  : reached
                    ? 'bg-[#0f172a] dark:bg-white text-white dark:text-gray-900'
                    : 'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-400 dark:text-slate-500'
              }`}
            >
              {allDone ? <i className="fa-solid fa-check text-[10px]" /> : idx + 1}
            </div>

            <p
              className={`text-[12px] mt-2 leading-snug ${
                isCurrent
                  ? 'font-bold text-gray-900 dark:text-white'
                  : reached
                    ? 'font-semibold text-gray-700 dark:text-slate-300'
                    : 'font-medium text-gray-400 dark:text-slate-500'
              }`}
            >
              {s.label}
            </p>
          </div>
        );
      })}
    </div>
  </div>
);

const Footer = ({ backLabel, onBack, nextLabel, nextIcon = 'fa-arrow-right', onNext, nextDisabled }) => (
  <div className="flex items-center justify-between gap-3 pt-4 mt-4 border-t border-gray-100 dark:border-slate-800">
    <button
      onClick={onBack}
      className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
    >
      {backLabel}
    </button>
    <button
      onClick={onNext}
      disabled={nextDisabled}
      className="px-4 py-2 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
    >
      {nextLabel} <i className={`fa-solid ${nextIcon} text-[11px]`} />
    </button>
  </div>
);

/**
 * The celebration mark above "You're all set!".
 *
 * A solid green disc with a white tick, a soft halo, and confetti specks placed
 * on a ring around it. Positions are fixed rather than random so the mark looks
 * the same every time it is seen — and because Math.random() during render would
 * reshuffle the confetti on every re-render.
 */
const CONFETTI = [
  { top: '4%', left: '30%', color: 'bg-amber-400', size: 'w-[7px] h-[7px]' },
  { top: '10%', left: '68%', color: 'bg-emerald-400', size: 'w-[6px] h-[6px]' },
  { top: '46%', left: '4%', color: 'bg-blue-500', size: 'w-[6px] h-[6px]' },
  { top: '56%', left: '84%', color: 'bg-amber-400', size: 'w-[6px] h-[6px]' },
  { top: '82%', left: '62%', color: 'bg-blue-600', size: 'w-[7px] h-[7px]' },
  { top: '74%', left: '22%', color: 'bg-emerald-300', size: 'w-[5px] h-[5px]' },
];

const SuccessMark = () => (
  <div className="relative w-[124px] h-[124px] mb-3 flex items-center justify-center">
    {/* Two halos: a wide wash and a tighter ring inside it. */}
    <span className="absolute inset-0 rounded-full bg-emerald-50 dark:bg-emerald-950/30" />
    <span className="absolute inset-[14px] rounded-full bg-emerald-100/70 dark:bg-emerald-900/30" />

    {CONFETTI.map((c, i) => (
      <span
        key={i}
        className={`absolute rounded-full ${c.color} ${c.size}`}
        style={{ top: c.top, left: c.left }}
      />
    ))}

    <span className="relative w-[72px] h-[72px] rounded-full bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/25">
      <i className="fa-solid fa-check text-white text-[28px]" />
    </span>
  </div>
);

/**
 * The handshake beside "What happens next?".
 *
 * Narrates the list next to it rather than decorating it: the wire draws, three
 * packets travel from the provider to Realify, the Realify node pulses as they
 * land, and a tick confirms the link. One shared 3.2s loop keeps the parts in
 * step — see the `conn-*` keyframes in index.css — with the packets staggered by
 * negative delay so they trail each other.
 */
const ConnectionAnimation = ({ provider }) => (
  <div
    className="w-full sm:w-[210px] flex-shrink-0 rounded-xl bg-gray-50 dark:bg-slate-800/60 p-3 flex flex-col overflow-hidden"
    role="img"
    aria-label={`Realify connecting to ${provider}`}
  >
    {/* Browser chrome, so the frame reads as the provider's sign-in window */}
    <div className="flex items-center gap-1 mb-3 flex-shrink-0">
      {[0, 1, 2].map((i) => (
        <span key={i} className="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-slate-600" />
      ))}
    </div>

    <div className="flex-1 min-h-[68px] flex items-center justify-center">
      <div className="relative flex items-center">
        {/* Provider */}
        <span className="relative z-10 w-9 h-9 rounded-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 flex items-center justify-center text-gray-400 dark:text-slate-500 flex-shrink-0">
          <i className="fa-solid fa-store text-[12px]" />
        </span>

        {/* Wire + packets */}
        <span className="relative w-[52px] h-[2px] mx-1 flex items-center">
          <span className="conn-wire absolute inset-0 rounded-full bg-gradient-to-r from-gray-200 to-indigo-300 dark:from-slate-700 dark:to-indigo-700" />
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="conn-packet absolute left-0 w-1.5 h-1.5 rounded-full bg-indigo-500"
              style={{ '--conn-distance': '46px', animationDelay: `${i * -0.42}s` }}
            />
          ))}
        </span>

        {/* Realify */}
        <span className="relative z-10 w-9 h-9 flex-shrink-0 flex items-center justify-center">
          <span className="conn-pulse absolute inset-0 rounded-full bg-indigo-400/50" />
          <span className="relative w-9 h-9 rounded-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 flex items-center justify-center text-indigo-500">
            <i className="fa-solid fa-star text-[13px]" />
          </span>
          <span className="conn-confirm absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 text-white flex items-center justify-center ring-2 ring-gray-50 dark:ring-slate-800">
            <i className="fa-solid fa-check text-[7px]" />
          </span>
        </span>
      </div>
    </div>
  </div>
);

const Tick = ({ checked, onChange, label }) => (
  <button
    onClick={onChange}
    role="checkbox"
    aria-checked={checked}
    aria-label={label}
    className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 transition-colors ${
      checked
        ? 'bg-indigo-600 text-white'
        : 'border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-900'
    }`}
  >
    {checked && <i className="fa-solid fa-check text-[8px]" />}
  </button>
);

/**
 * The Onboarding tab — five steps in one card.
 *
 * `step` is lifted to the page so the right rail's journey card can advance with
 * it; the two would otherwise disagree about how far setup has got.
 *
 * `onboarded` short-circuits the whole wizard. A connector that is already
 * connected has nothing to authorize, no scopes left to pick and no consent left
 * to give, so the steps are not rendered at all — not merely skipped past, which
 * would still leave a Back button leading into them.
 */
const OnboardingTab = ({ connector, step, setStep, onExit, onGoToOverview, onboarded = false }) => {
  const [segment, setSegment] = useState('read');
  const [consented, setConsented] = useState(true);
  /* A parsed CSV is an alternative source of truth for this connector, so the
     Authorize step's primary button changes once one is loaded. */
  const [csv, setCsv] = useState(null);

  const scopes = useMemo(() => readScopes(connector), [connector]);
  const permissions = useMemo(() => writePermissions(connector), [connector]);

  /* Recommended scopes start on; everything else is opt-in — least privilege by
     default rather than by remembering to untick. */
  const [selected, setSelected] = useState(() =>
    readScopes(connector).filter((s) => s.recommended).map((s) => s.key)
  );

  const rows = segment === 'read' ? scopes : permissions;
  const toggle = (key) =>
    setSelected((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));

  const provider = providerName(connector);
  const card = chooseConnectorCard(connector);

  const shell = 'rounded-2xl border border-gray-200 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/25 p-5';

  return (
    <div className={shell}>
      <h2 className="text-[16px] font-bold text-gray-900 dark:text-white">Onboarding journey</h2>
      <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5 mb-6">
        {onboarded
          ? `All steps completed — ${connector.name} is connected to Realify.`
          : 'Complete all steps to go live.'}
      </p>

      <StepRail step={onboarded ? JOURNEY_STEPS.length : step} allDone={onboarded} />

      {/* ── Step 1 · Choose connector ── */}
      {!onboarded && step === 0 && (
        <div className="mt-7">
          <h3 className="text-[14.5px] font-bold text-gray-900 dark:text-white">Choose connector</h3>
          <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5 mb-4">
            Select the connector you want to connect with Realify.
          </p>

          <p className="text-[11.5px] font-semibold text-gray-600 dark:text-slate-400 mb-2">Connector</p>
          <div className="rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 flex items-start gap-3.5">
            <span className={`w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center text-[16px] ${connector.tone}`}>
              <i className={connector.icon} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-[13.5px] font-bold text-gray-900 dark:text-white">{card.name}</p>
                <span className="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-[10px] font-bold">
                  {card.badge}
                </span>
              </div>
              <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-0.5">{card.categoryLabel}</p>
              <p className="text-[12px] text-gray-600 dark:text-slate-300 leading-relaxed mt-2">
                {card.description}
              </p>
            </div>
            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center flex-shrink-0">
              <i className="fa-solid fa-check text-[9px]" />
            </span>
          </div>

          <div className="mt-4 rounded-xl bg-blue-50/70 dark:bg-blue-950/25 border border-blue-100 dark:border-blue-900/40 p-3.5 flex items-start gap-3">
            <i className="fa-solid fa-circle-info text-[13px] text-blue-500 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-1">Why we need this</p>
              <p className="text-[12px] text-gray-600 dark:text-slate-300 leading-relaxed">
                Enables specialists to read data and take actions such as pricing, inventory updates,
                and listing optimizations.
              </p>
            </div>
            <button className="text-[11.5px] font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 flex items-center gap-1 flex-shrink-0">
              Learn more <i className="fa-solid fa-arrow-right text-[9px]" />
            </button>
          </div>

          <Footer
            backLabel="Cancel"
            onBack={onExit}
            nextLabel="Continue to authorize"
            onNext={() => setStep(1)}
          />
        </div>
      )}

      {/* ── Step 2 · Authorize ── */}
      {!onboarded && step === 1 && (
        <div className="mt-7">
          {/* Title left, CSV upload right: uploading a file is the alternative to
              the OAuth handoff this heading describes, so the two choices belong
              on one line rather than a page-header button away from each other. */}
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-5">
            <div className="min-w-0">
              <h3 className="text-[16px] font-bold text-gray-900 dark:text-white">
                Authorize Realify to access your {provider} account
              </h3>
              <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1">
                You&apos;ll be redirected to {provider} to securely sign in and authorize access.
              </p>
            </div>

            <CsvUploadButton connectorName={connector.name} onParsed={setCsv} />
          </div>

          <div className="rounded-xl bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 p-3.5 flex items-start gap-3">
            <span className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
              <i className="fa-solid fa-shield-halved text-[12px]" />
            </span>
            <div className="min-w-0">
              <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-0.5">Secure &amp; compliant</p>
              <p className="text-[12px] text-gray-600 dark:text-slate-300 leading-relaxed">
                We use {connector.name} with OAuth 2.0. Your credentials are never stored or shared.
                You can revoke access anytime.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
            {AUTHORIZE_PILLARS.map((p) => (
              <div
                key={p.key}
                className="rounded-xl bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 p-3.5"
              >
                <span className="w-8 h-8 rounded-lg bg-gray-50 dark:bg-slate-800 text-gray-500 dark:text-slate-400 flex items-center justify-center mb-2.5">
                  <i className={`fa-solid ${p.icon} text-[12px]`} />
                </span>
                <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug">{p.title}</p>
                <p className="text-[11px] text-gray-500 dark:text-slate-400 leading-relaxed mt-1">{p.body}</p>
              </div>
            ))}
          </div>

          <div className="mt-3 rounded-xl bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 p-4 flex flex-col sm:flex-row gap-4">
            <div className="min-w-0 flex-1">
              <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-2.5">What happens next?</p>
              <ul className="space-y-2">
                {authorizeNextSteps(connector).map((line) => (
                  <li key={line} className="flex items-start gap-2.5">
                    <i className="fa-regular fa-circle-check text-[11px] text-emerald-500 mt-[3px] flex-shrink-0" />
                    <span className="text-[12px] text-gray-600 dark:text-slate-300 leading-relaxed">{line}</span>
                  </li>
                ))}
              </ul>
            </div>

            <ConnectionAnimation provider={provider} />
          </div>

          <Footer
            backLabel="Back"
            onBack={() => setStep(0)}
            nextLabel={csv ? `Continue with ${csv.name}` : `Authorize with ${provider}`}
            nextIcon={csv ? 'fa-arrow-right' : 'fa-arrow-up-right-from-square'}
            onNext={() => setStep(2)}
          />
        </div>
      )}

      {/* ── Step 3 · Scopes & permissions ── */}
      {!onboarded && step === 2 && (
        <div className="mt-7">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="min-w-0">
              <h3 className="text-[14.5px] font-bold text-gray-900 dark:text-white">Scopes &amp; permissions</h3>
              <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5">
                Select the data Realify can read and the actions it can take.
              </p>
            </div>

            <div className="flex rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden flex-shrink-0 bg-white dark:bg-slate-900">
              {SCOPE_SEGMENTS.map((seg) => (
                <button
                  key={seg.key}
                  onClick={() => setSegment(seg.key)}
                  className={`px-3.5 py-2 text-left transition-colors ${
                    segment === seg.key
                      ? 'bg-white dark:bg-slate-900 border-b-2 border-gray-900 dark:border-white'
                      : 'bg-gray-50/70 dark:bg-slate-800/50'
                  }`}
                >
                  <p className={`text-[12px] font-bold ${segment === seg.key ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-slate-400'}`}>
                    {seg.label}
                  </p>
                  <p className="text-[10.5px] text-gray-400 dark:text-slate-500">{seg.sub}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4 rounded-xl bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 overflow-hidden">
            <div className="px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 dark:border-slate-800">
              <div className="min-w-0">
                <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">
                  {segment === 'read' ? 'Select read scopes' : 'Select write permissions'}
                </p>
                <p className="text-[11px] text-gray-500 dark:text-slate-400 mt-0.5">
                  {segment === 'read'
                    ? `These scopes allow Realify to read data from your ${provider} account.`
                    : `These permissions let Realify act on your ${provider} account inside your guardrails.`}
                </p>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <button
                  onClick={() => setSelected(rows.filter((r) => r.recommended).map((r) => r.key))}
                  className="text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 whitespace-nowrap"
                >
                  Select all recommended
                </button>
                <button className="text-[11.5px] font-semibold text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 flex items-center gap-1.5 whitespace-nowrap">
                  View documentation <i className="fa-solid fa-arrow-up-right-from-square text-[9px]" />
                </button>
              </div>
            </div>

            <div className="px-4 py-2 grid grid-cols-[1fr_auto] sm:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_auto] gap-3 border-b border-gray-100 dark:border-slate-800">
              {['Scope', 'Description', 'Recommended'].map((h, i) => (
                <p
                  key={h}
                  className={`text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider ${
                    i === 1 ? 'hidden sm:block' : ''
                  } ${i === 2 ? 'text-right' : ''}`}
                >
                  {h}
                </p>
              ))}
            </div>

            {rows.map((row) => {
              const checked = selected.includes(row.key);
              return (
                <div
                  key={row.key}
                  className="px-4 py-3 grid grid-cols-[1fr_auto] sm:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_auto] gap-3 items-center border-b border-gray-100 dark:border-slate-800 last:border-0"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Tick checked={checked} onChange={() => toggle(row.key)} label={row.label} />
                    <span className="text-[12.5px] font-semibold text-gray-900 dark:text-white truncate">
                      {row.label}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400 text-[10px] font-mono whitespace-nowrap flex-shrink-0">
                      {row.scope}
                    </span>
                  </div>

                  <p className="hidden sm:block text-[11.5px] text-gray-500 dark:text-slate-400 leading-snug">
                    {row.description}
                  </p>

                  <span
                    className={`px-2 py-0.5 rounded text-[10.5px] font-semibold whitespace-nowrap justify-self-end ${
                      row.recommended
                        ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400'
                        : 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400'
                    }`}
                  >
                    {row.recommended ? 'Recommended' : 'Optional'}
                  </span>
                </div>
              );
            })}
          </div>

          <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-2.5">
            {selected.filter((k) => rows.some((r) => r.key === k)).length} of {rows.length}{' '}
            {segment === 'read' ? 'scopes' : 'permissions'} selected
          </p>

          <Footer
            backLabel="Back"
            onBack={() => setStep(1)}
            nextLabel="Continue to permissions"
            onNext={() => setStep(3)}
          />
        </div>
      )}

      {/* ── Step 4 · Access & consent ── */}
      {!onboarded && step === 3 && (
        <div className="mt-7">
          <h3 className="text-[14.5px] font-bold text-gray-900 dark:text-white">Access &amp; consent</h3>
          <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5 mb-4">
            Review how Realify will handle your data and confirm your consent.
          </p>

          <div className="rounded-xl bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 overflow-hidden">
            {CONSENT_BLOCKS.map((block) => (
              <div
                key={block.key}
                className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 border-b border-gray-100 dark:border-slate-800 last:border-0"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <span className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
                    <i className={`fa-solid ${block.icon} text-[12px]`} />
                  </span>
                  <div className="min-w-0">
                    <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-1">{block.title}</p>
                    <p className="text-[11.5px] text-gray-500 dark:text-slate-400 leading-relaxed">
                      {block.body}
                    </p>
                  </div>
                </div>

                <ul className="space-y-2 sm:pl-4">
                  {block.points.map((point) => (
                    <li key={point} className="flex items-start gap-2.5">
                      <i className="fa-solid fa-check text-[10px] text-emerald-500 mt-[3px] flex-shrink-0" />
                      <span className="text-[12px] text-gray-600 dark:text-slate-300 leading-relaxed">
                        {point}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-3 rounded-xl bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-3.5 flex items-start gap-3">
            <Tick
              checked={consented}
              onChange={() => setConsented((v) => !v)}
              label="Confirm consent"
            />
            <div className="min-w-0">
              <p className="text-[12px] text-gray-800 dark:text-slate-200 leading-relaxed">
                I confirm that I have the right to grant access to this {provider} account and allow
                Realify to access data as described above.
              </p>
              <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-1.5 flex items-center gap-1.5">
                <i className="fa-solid fa-file-shield text-[10px]" />
                By continuing, you agree to Realify&apos;s{' '}
                <button className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline">Terms of Service</button>
                {' '}and{' '}
                <button className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline">Privacy Policy</button>.
              </p>
            </div>
          </div>

          {/* Consent is the gate: without the tick there is nothing to continue on. */}
          <Footer
            backLabel="Back"
            onBack={() => setStep(2)}
            nextLabel="Continue"
            onNext={() => setStep(4)}
            nextDisabled={!consented}
          />
        </div>
      )}

      {/* ── Step 5 · Go live ──
          Also the whole tab for a connector that was already onboarded: the
          finished state is the same screen, so it is one branch, not two. */}
      {(onboarded || step === 4) && (
        <div className="mt-7">
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-6">
            <div className="flex flex-col items-center text-center">
              <SuccessMark />
              <h3 className="text-[20px] font-bold text-gray-900 dark:text-white tracking-tight">
                You&apos;re all set!
              </h3>
              <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mt-1.5 leading-relaxed max-w-[380px]">
                {connector.name} is now connected to Realify.
                <br />
                {/* "will start syncing" is a promise, and it would be a stale one
                    for a connector that has been syncing for weeks. */}
                {connector.lastSync
                  ? `Data is syncing — last sync ${connector.lastSync}.`
                  : 'Your data will start syncing shortly.'}
              </p>
            </div>

            <div className="mt-6 rounded-xl bg-gray-50/70 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 p-4">
              <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-3">
                What happens next?
              </p>
              <div className="space-y-3">
                {GO_LIVE_NEXT.map((item) => (
                  <div key={item.key} className="flex items-start gap-3">
                    <span
                      className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        item.tone === 'active'
                          ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                          : 'bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 text-gray-400 dark:text-slate-500'
                      }`}
                    >
                      <i className={`fa-solid ${item.icon} text-[11px]`} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug">
                        {item.title}
                      </p>
                      <p className="text-[11px] text-gray-500 dark:text-slate-400 leading-relaxed mt-0.5">
                        {item.body}
                      </p>
                    </div>
                    <span
                      className={`text-[11px] font-semibold whitespace-nowrap flex-shrink-0 flex items-center gap-1.5 ${
                        item.tone === 'active'
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-gray-400 dark:text-slate-500'
                      }`}
                    >
                      {item.status}
                      {item.tone === 'active' && (
                        <i className="fa-solid fa-circle-notch fa-spin text-[9px]" />
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 mt-4">
            <button
              onClick={onGoToOverview}
              className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
            >
              View integration details
            </button>
            <button
              onClick={onGoToOverview}
              className="px-4 py-2 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center gap-2"
            >
              Go to overview <i className="fa-solid fa-arrow-right text-[11px]" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default OnboardingTab;
