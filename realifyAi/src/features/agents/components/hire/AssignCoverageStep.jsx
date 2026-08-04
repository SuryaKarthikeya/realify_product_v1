import React, { useMemo, useState } from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import WizardChrome from '@/features/agents/components/hire/WizardChrome';
import {
  COVERAGE_TREE,
  WORKSPACES,
  TEAMS,
  AUTONOMY_LEVELS,
  allCoverageIds,
  coveragePath,
  selectedAutonomy,
  flattenTree,
} from '@/features/agents/data/hireWizardData';

/** Square tick box matching the design's filled-blue checked state. */
const CheckBox = ({ checked }) => (
  <span
    className={`w-4 h-4 rounded-[4px] flex items-center justify-center flex-shrink-0 transition-colors ${
      checked
        ? 'bg-blue-600 text-white'
        : 'border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-900'
    }`}
  >
    {checked && <i className="fa-solid fa-check text-[8px]" />}
  </span>
);

/**
 * One tree row plus its descendants.
 *
 * Recursion rather than a flattened list, so the guide rail and indent follow
 * the real shape of the tree at any depth.
 */
const TreeNode = ({ node, depth, selected, onToggle, open, onToggleOpen, search }) => {
  const isChecked = selected.includes(node.id);
  const hasChildren = Boolean(node.children?.length);
  const isOpen = open.includes(node.id);

  /* While searching, show a branch if it or any descendant matches — hiding a
     matching child behind a non-matching parent would make it unreachable. */
  const matches = useMemo(() => {
    if (!search.trim()) return true;
    const term = search.trim().toLowerCase();
    const inSubtree = (n) =>
      n.label.toLowerCase().includes(term) || (n.children || []).some(inSubtree);
    return inSubtree(node);
  }, [node, search]);

  if (!matches) return null;
  const forceOpen = Boolean(search.trim());

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-1.5 rounded-md ${
          isChecked && depth >= 2 ? 'bg-blue-50/70 dark:bg-blue-950/30' : ''
        }`}
        style={{ paddingLeft: `${depth * 22 + 4}px`, paddingRight: '8px' }}
      >
        {hasChildren ? (
          <button
            onClick={() => onToggleOpen(node.id)}
            className="w-3 text-gray-400 dark:text-slate-500 hover:text-gray-600 flex-shrink-0"
            aria-label={isOpen ? `Collapse ${node.label}` : `Expand ${node.label}`}
          >
            <i className={`fa-solid fa-chevron-${isOpen || forceOpen ? 'down' : 'right'} text-[8px]`} />
          </button>
        ) : (
          <span className="w-3 flex-shrink-0" />
        )}

        <button
          onClick={() => onToggle(node)}
          className="flex items-center gap-2 min-w-0 text-left"
        >
          <CheckBox checked={isChecked} />
          <i
            className={`fa-solid ${node.icon || 'fa-folder'} text-[10px] flex-shrink-0 ${
              isChecked ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-slate-500'
            }`}
          />
          <span
            className={`text-[12.5px] truncate ${
              isChecked
                ? 'font-semibold text-gray-900 dark:text-white'
                : 'font-medium text-gray-600 dark:text-slate-400'
            }`}
          >
            {node.label}
          </span>
        </button>
      </div>

      {hasChildren && (isOpen || forceOpen) && (
        <div className="relative">
          {/* Guide rail, aligned to this level's chevron column */}
          <div
            className="absolute top-0 bottom-1 w-[1px] bg-gray-200 dark:bg-slate-700"
            style={{ left: `${depth * 22 + 10}px` }}
          />
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              selected={selected}
              onToggle={onToggle}
              open={open}
              onToggleOpen={onToggleOpen}
              search={search}
            />
          ))}
        </div>
      )}
    </div>
  );
};

/** "Your selection" row. */
const SummaryRow = ({ label, children }) => (
  <div>
    <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">
      {label}
    </p>
    {children}
  </div>
);

/**
 * Step 2 — where the specialist works, which workspace and team it belongs to,
 * and how much autonomy it is granted.
 *
 * Autonomy is multi-select: the user may grant several rungs, and the review
 * step lists every one of them.
 */
const AssignCoverageStep = ({ agent, draft, onChange, onBack, onContinue, onSaveDraft }) => {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(() =>
    flattenTree().filter((n) => n.defaultOpen).map((n) => n.id)
  );

  const specialistName = agent?.name || 'Pricing & Margin';
  const workspace = WORKSPACES.find((w) => w.id === draft.workspace) || WORKSPACES[0];
  const team = TEAMS.find((t) => t.id === draft.team) || TEAMS[0];
  const path = coveragePath(draft.coverage);
  const chosen = selectedAutonomy(draft.autonomy);

  /* Ticking a branch takes its whole subtree; unticking releases it. Selecting a
     parent without its children would claim coverage the specialist never got. */
  const toggleNode = (node) => {
    const subtree = flattenTree([node]).map((n) => n.id);
    const isChecked = draft.coverage.includes(node.id);
    onChange({
      coverage: isChecked
        ? draft.coverage.filter((id) => !subtree.includes(id))
        : [...new Set([...draft.coverage, ...subtree])],
    });
  };

  const toggleAutonomy = (key) => {
    onChange({
      autonomy: draft.autonomy.includes(key)
        ? draft.autonomy.filter((k) => k !== key)
        : [...draft.autonomy, key],
    });
  };

  const allSelected = draft.coverage.length === allCoverageIds().length;

  return (
    <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 space-y-4 font-sans">
      <WizardChrome
        title={`Hire ${specialistName.split(' ')[0]} Specialist`}
        stepIndex={1}
        tagline="Assign coverage, team and trust level"
        onBack={onBack}
        onSaveDraft={onSaveDraft}
        subs={{ specialist: specialistName }}
      />

      <div className="flex flex-col xl:flex-row gap-5 items-start">

        {/* ── Configuration ── */}
        <div className="flex-1 min-w-0 w-full rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

            {/* Coverage tree */}
            <div className="min-w-0">
              <h2 className="text-[14px] font-bold text-gray-900 dark:text-white">
                Where should this specialist work?
              </h2>
              <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mt-1 mb-4">
                Select the categories it will operate on.
              </p>

              <div className="relative mb-4">
                <i className="fa-solid fa-magnifying-glass text-[11px] text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search categories..."
                  className="w-full rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 pl-9 pr-24 py-2.5 text-[12.5px] text-gray-800 dark:text-slate-200 placeholder-gray-400 dark:placeholder-slate-500 outline-none focus:border-blue-500 transition-colors"
                />
                <button
                  onClick={() => onChange({ coverage: allSelected ? [] : allCoverageIds() })}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[12px] font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700"
                >
                  {allSelected ? 'Clear all' : 'Select all'}
                </button>
              </div>

              <div>
                {COVERAGE_TREE.map((node) => (
                  <TreeNode
                    key={node.id}
                    node={node}
                    depth={0}
                    selected={draft.coverage}
                    onToggle={toggleNode}
                    open={open}
                    onToggleOpen={(id) =>
                      setOpen((o) => (o.includes(id) ? o.filter((x) => x !== id) : [...o, id]))
                    }
                    search={search}
                  />
                ))}
              </div>
            </div>

            {/* Workspace & team */}
            <div className="min-w-0 space-y-5">
              <SelectMenu
                label="Workspace"
                value={workspace.id}
                options={WORKSPACES}
                onChange={(id) => onChange({ workspace: id })}
                badge={
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 w-6 h-6 rounded-md bg-blue-600 text-white flex items-center justify-center text-[9px] font-bold pointer-events-none z-10">
                    {workspace.initials}
                  </span>
                }
              />

              <SelectMenu
                label="Team"
                value={team.id}
                options={TEAMS}
                onChange={(id) => onChange({ team: id })}
                badge={
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 w-6 h-6 rounded-md bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-[9px] pointer-events-none z-10">
                    <i className="fa-solid fa-users" />
                  </span>
                }
              />

              <div className="rounded-xl bg-gray-50/80 dark:bg-slate-800/40 px-4 py-3.5 flex items-start gap-3">
                <i className="fa-regular fa-clock text-[12px] text-gray-400 dark:text-slate-500 mt-0.5 flex-shrink-0" />
                <p className="text-[11.5px] text-gray-500 dark:text-slate-400 leading-relaxed">
                  This specialist will access data and playbooks from the selected workspace.
                </p>
              </div>
            </div>
          </div>

          {/* ── Autonomy — multi-select ── */}
          <div className="mt-5 pt-5 border-t border-gray-100 dark:border-slate-800">
            <h2 className="text-[14px] font-bold text-gray-900 dark:text-white">
              How much autonomy should this specialist have?
            </h2>
            <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mt-1 mb-4">
              You can change this anytime. Select as many levels as you want to grant.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              {AUTONOMY_LEVELS.map((level) => {
                const isOn = draft.autonomy.includes(level.key);
                return (
                  <button
                    key={level.key}
                    onClick={() => toggleAutonomy(level.key)}
                    aria-pressed={isOn}
                    className={`text-left rounded-xl border-2 p-4 transition-colors ${
                      isOn
                        ? 'border-[#0f172a] dark:border-white bg-white dark:bg-slate-900'
                        : 'border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-gray-200 dark:hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2.5">
                      <div className="flex items-center gap-2 min-w-0">
                        <i className={`fa-solid ${level.icon} text-[11px] text-gray-500 dark:text-slate-400`} />
                        <span className="text-[12.5px] font-bold text-gray-900 dark:text-white truncate">
                          {level.label}
                        </span>
                      </div>
                      {/* Square tick, not a radio — several may be granted */}
                      <span
                        className={`w-4 h-4 rounded-[4px] flex items-center justify-center flex-shrink-0 ${
                          isOn
                            ? 'bg-[#0f172a] dark:bg-white text-white dark:text-gray-900'
                            : 'border border-gray-300 dark:border-slate-600'
                        }`}
                      >
                        {isOn && <i className="fa-solid fa-check text-[8px]" />}
                      </span>
                    </div>
                    {level.lines.map((line) => (
                      <p key={line} className="text-[11px] text-gray-500 dark:text-slate-400 leading-relaxed">
                        {line}
                      </p>
                    ))}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── Your selection ── */}
        <div className="w-full xl:w-[330px] xl:flex-shrink-0 space-y-4">
          <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
            <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white pb-4 mb-4 border-b border-gray-100 dark:border-slate-800">
              Your selection
            </h3>

            <div className="space-y-5">
              <SummaryRow label="Specialist">
                <div className="flex items-center gap-2.5">
                  <span className="w-7 h-7 rounded-md bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                    {specialistName.charAt(0)}
                  </span>
                  <span className="text-[12.5px] font-bold text-gray-900 dark:text-white">
                    {specialistName}
                  </span>
                </div>
              </SummaryRow>

              <SummaryRow label="Coverage">
                {path.length === 0 ? (
                  <p className="text-[11.5px] text-gray-400 dark:text-slate-500 italic">
                    No categories selected
                  </p>
                ) : (
                  <div className="space-y-1.5">
                    {path.map((node, idx) => (
                      <div
                        key={node.id}
                        className="flex items-center gap-1.5"
                        style={{ paddingLeft: `${idx * 16}px` }}
                      >
                        <i
                          className={`fa-solid ${
                            idx === 0 ? node.icon || 'fa-house' : idx === path.length - 1 ? 'fa-minus' : 'fa-folder'
                          } text-[9px] ${
                            idx === path.length - 1
                              ? 'text-blue-600 dark:text-blue-400'
                              : 'text-gray-400 dark:text-slate-500'
                          }`}
                        />
                        <span
                          className={`text-[11.5px] ${
                            idx === path.length - 1
                              ? 'font-semibold text-blue-600 dark:text-blue-400'
                              : 'font-medium text-gray-600 dark:text-slate-400'
                          }`}
                        >
                          {node.label}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </SummaryRow>

              <SummaryRow label="Workspace">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-md bg-blue-600 text-white flex items-center justify-center text-[9px] font-bold flex-shrink-0">
                    {workspace.initials}
                  </span>
                  <span className="text-[11.5px] font-semibold text-gray-800 dark:text-slate-200">
                    {workspace.label}
                  </span>
                </div>
              </SummaryRow>

              <SummaryRow label="Team">
                <div className="flex items-center gap-2.5">
                  <i className="fa-solid fa-users text-[11px] text-blue-600 dark:text-blue-400 w-6 text-center flex-shrink-0" />
                  <span className="text-[11.5px] font-semibold text-gray-800 dark:text-slate-200">
                    {team.label}
                  </span>
                </div>
              </SummaryRow>

              <SummaryRow label="Trust level">
                {chosen.length === 0 ? (
                  <p className="text-[11.5px] text-gray-400 dark:text-slate-500 italic">
                    No level granted yet
                  </p>
                ) : (
                  /* Each granted level gets its own chip, so a multi-select is
                     visible here rather than collapsed to one name. */
                  <div className="flex flex-wrap gap-1.5">
                    {chosen.map((level) => (
                      <span
                        key={level.key}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 text-[11.5px] font-bold"
                      >
                        <i className={`fa-solid ${level.icon} text-[9px]`} /> {level.label}
                      </span>
                    ))}
                  </div>
                )}
              </SummaryRow>
            </div>

            <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-relaxed mt-4">
              This specialist will start in Shadow mode.
            </p>

            <button
              onClick={onContinue}
              disabled={chosen.length === 0 || path.length === 0}
              className="w-full mt-4 py-2.5 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Continue to next step <i className="fa-solid fa-arrow-right text-[11px]" />
            </button>
          </div>

          {/* Guardrails for whatever is granted */}
          {chosen.length > 0 && (
            <div className="rounded-2xl bg-gray-50/80 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 p-4 space-y-4">
              {chosen.map((level) => (
                <div key={level.key}>
                  <span className="inline-block px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-[10px] font-bold text-gray-600 dark:text-slate-300 mb-2.5">
                    {level.label}{level.recommended ? ' (Recommended)' : ''}
                  </span>
                  <ul className="space-y-1.5">
                    {level.benefits.map((b) => (
                      <li key={b} className="flex items-start gap-2">
                        <i className="fa-solid fa-check text-[9px] text-gray-400 dark:text-slate-500 mt-[3px] flex-shrink-0" />
                        <span className="text-[11px] text-gray-600 dark:text-slate-400 leading-relaxed">{b}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssignCoverageStep;
