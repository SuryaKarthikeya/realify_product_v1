import React, { useMemo, useState } from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import { connectorSettings } from '@/features/integrations/data/connectorDetailData';

/**
 * The green switch from ss1.
 *
 * Local rather than the shared ToggleSwitch: that one paints `bg-brand` (the
 * app's dark grey), and recolouring it would change every other screen using it.
 */
const Switch = ({ on, onToggle, label, disabled }) => (
  <button
    type="button"
    onClick={onToggle}
    disabled={disabled}
    role="switch"
    aria-checked={on}
    aria-label={label}
    className={`relative w-9 h-5 rounded-full transition-colors flex-shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 ${
      on ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-slate-700'
    } ${disabled ? 'opacity-100 cursor-default' : 'cursor-pointer'}`}
  >
    <span
      className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
        on ? 'translate-x-4' : 'translate-x-0'
      }`}
    />
  </button>
);

const onOffLabel = (field, value) =>
  value ? field.onLabel || 'On' : field.offLabel || 'Off';

/**
 * Settings for one connector.
 *
 * Fields are declared in the data layer with their own control type, so this
 * renders and edits them generically — a new setting is a data entry, not new
 * markup. Each section edits in place: Edit swaps its read-only values for live
 * controls, and Cancel restores the values the section opened with, so an
 * abandoned edit cannot leave a half-changed section behind.
 */
const SettingsTab = ({ connector }) => {
  const sections = useMemo(() => connectorSettings(connector), [connector]);

  /* One flat map of every field's current value, keyed section.field. */
  const initial = useMemo(() => {
    const out = {};
    sections.forEach((s) => s.fields.forEach((f) => { out[`${s.key}.${f.key}`] = f.value; }));
    return out;
  }, [sections]);

  const [values, setValues] = useState(initial);
  const [editing, setEditing] = useState(null);
  /* The values the open section started with, so Cancel has something to restore. */
  const [snapshot, setSnapshot] = useState(null);

  const set = (id, v) => setValues((prev) => ({ ...prev, [id]: v }));

  const startEdit = (section) => {
    setSnapshot(values);
    setEditing(section.key);
  };
  const cancelEdit = () => {
    if (snapshot) setValues(snapshot);
    setSnapshot(null);
    setEditing(null);
  };
  const saveEdit = () => {
    setSnapshot(null);
    setEditing(null);
  };

  return (
    <div className="space-y-4">

      {/* ── Header ── */}
      <div>
        <h2 className="text-[16px] font-bold text-gray-900 dark:text-white">Settings</h2>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5">
          Configure how {connector.name} data is synced and managed.
        </p>
      </div>

      {sections.map((section) => {
        const isEditing = editing === section.key;
        return (
          <div
            key={section.key}
            className={`bg-white dark:bg-slate-900 border rounded-2xl p-4 transition-colors ${
              isEditing
                ? 'border-indigo-300 dark:border-indigo-800'
                : 'border-gray-200 dark:border-slate-800'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3 min-w-0">
                <span className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0">
                  <i className={`fa-solid ${section.icon} text-[13px]`} />
                </span>
                <div className="min-w-0">
                  <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">{section.title}</h3>
                  <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5 leading-snug">
                    {section.subtitle}
                  </p>
                </div>
              </div>

              {isEditing ? (
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={cancelEdit}
                    className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-[12px] font-bold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveEdit}
                    className="px-3 py-1.5 rounded-lg bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[12px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors"
                  >
                    Save
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => startEdit(section)}
                  className="text-[12.5px] font-bold text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors flex items-center gap-1.5 flex-shrink-0"
                >
                  Edit <i className="fa-solid fa-chevron-right text-[9px]" />
                </button>
              )}
            </div>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 sm:pl-12">
              {section.fields.map((field) => {
                const id = `${section.key}.${field.key}`;
                const value = values[id];

                return (
                  <div key={field.key} className="min-w-0">
                    <p className="text-[11px] text-gray-500 dark:text-slate-400 mb-1.5">{field.label}</p>

                    {field.type === 'toggle' ? (
                      <div className="flex items-center gap-2.5">
                        <Switch
                          on={!!value}
                          onToggle={() => isEditing && set(id, !value)}
                          disabled={!isEditing}
                          label={field.label}
                        />
                        <span className="text-[12.5px] font-semibold text-gray-900 dark:text-white">
                          {onOffLabel(field, value)}
                        </span>
                      </div>
                    ) : isEditing ? (
                      <SelectMenu
                        value={value}
                        options={field.options}
                        onChange={(v) => set(id, v)}
                        size="sm"
                        ariaLabel={field.label}
                      />
                    ) : (
                      <p className="text-[12.5px] font-semibold text-gray-900 dark:text-white leading-snug">
                        {value}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SettingsTab;
