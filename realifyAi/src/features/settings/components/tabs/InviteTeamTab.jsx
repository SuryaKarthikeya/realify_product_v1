import React, { useState } from 'react';
import { sendInviteEmail } from '@/services/invitationService';

const ROLES = [
  { value: 'admin', label: 'Admin' },
  { value: 'analyst', label: 'Analyst' },
  { value: 'viewer', label: 'Viewer' },
  { value: 'inventory-planner', label: 'Inventory Planner' },
  { value: 'sales-manager', label: 'Sales Manager' },
];

const ROLE_CARDS = [
  {
    key: 'admin',
    title: 'Admin',
    icon: 'fa-cog',
    iconColor: 'text-red-600',
    bg: 'bg-red-50',
    dotColor: 'bg-red-400',
    features: ['Stock levels', 'Reorder alerts'],
  },
  {
    key: 'analyst',
    title: 'Analyst',
    icon: 'fa-chart-line',
    iconColor: 'text-blue-600',
    bg: 'bg-blue-50',
    dotColor: 'bg-blue-400',
    features: ['Campaign ROAS', 'Ad spend'],
  },
  {
    key: 'viewer',
    title: 'Viewer',
    icon: 'fa-eye',
    iconColor: 'text-orange-600',
    bg: 'bg-orange-50',
    dotColor: 'bg-orange-400',
    features: ['Orders', 'Operational KPIs'],
  },
  {
    key: 'inventory-planner',
    title: 'Inventory Planner',
    icon: 'fa-boxes-stacked',
    iconColor: 'text-emerald-600',
    bg: 'bg-emerald-50',
    dotColor: 'bg-emerald-400',
    features: ['Full dashboard access', 'No editing permissions'],
  },
];

const STATUS_CONFIG = {
  Pending: {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    border: 'border-amber-100',
  },
  Accepted: {
    bg: 'bg-green-50',
    text: 'text-green-600',
    border: 'border-green-100',
  },
  Expired: {
    bg: 'bg-red-50',
    text: 'text-red-500',
    border: 'border-red-100',
  },
  Revoked: {
    bg: 'bg-gray-100',
    text: 'text-gray-500',
    border: 'border-gray-200',
  },
};

const MOCK_INVITES = [
  { id: 1, email: 'priya@acmepets.com', role: 'Inventory Planner', status: 'Pending', date: 'Jun 20, 2025' },
  { id: 2, email: 'john.doe@acmepets.com', role: 'Ads Manager', status: 'Accepted', date: 'Jun 15, 2025' },
  { id: 3, email: 'ops.team@acmepets.com', role: 'Ops', status: 'Expired', date: 'Jun 1, 2025' },
  { id: 4, email: 'viewer@acmepets.com', role: 'Read-only', status: 'Revoked', date: 'May 28, 2025' },
];

let rowIdCounter = 2;

const InviteTeamTab = () => {
  const [inviteRows, setInviteRows] = useState([{ id: 1, email: '', role: '' }]);
  const [pendingInvites, setPendingInvites] = useState(MOCK_INVITES);
  const [inviteSent, setInviteSent] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const addRow = () => {
    rowIdCounter += 1;
    setInviteRows(prev => [...prev, { id: rowIdCounter, email: '', role: '' }]);
  };

  const removeRow = (id) => {
    if (inviteRows.length === 1) return;
    setInviteRows(prev => prev.filter(r => r.id !== id));
  };

  const updateRow = (id, field, value) => {
    setInviteRows(prev => prev.map(r => (r.id === id ? { ...r, [field]: value } : r)));
  };

const handleSendInvites = async () => {
  const validRows = inviteRows.filter(r => r.email && r.role);
  if (!validRows.length) return;

  setIsSending(true);
  setErrorMsg('');

  const newInvites = [];
  const failedEmails = [];
  const todayLabel = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

  for (const row of validRows) {
    const roleLabel = ROLES.find(r => r.value === row.role)?.label || row.role;
    const inviteLink = `${window.location.origin}/login?role=${encodeURIComponent(row.role)}&email=${encodeURIComponent(row.email)}`;

    try {
      await sendInviteEmail({
        email:       row.email,
        userName:    row.email.split('@')[0],
        roleName:    roleLabel,
        inviteLink,
      });
      newInvites.push({
        id:     Date.now() + Math.random(),
        email:  row.email,
        role:   roleLabel,
        status: 'Pending',
        date:   todayLabel,
      });
    } catch (err) {
      console.error('EmailJS error for', row.email, err);
      failedEmails.push(row.email);
    }
  }

  setIsSending(false);

  if (newInvites.length) {
    setPendingInvites(prev => [...newInvites, ...prev]);
    // Reset invite rows after successful send
    rowIdCounter = 2;
    setInviteRows([{ id: 1, email: '', role: '' }]);
    setInviteSent(true);
    setTimeout(() => setInviteSent(false), 3000);
  }

  if (failedEmails.length) {
    setErrorMsg(`Failed to send to: ${failedEmails.join(', ')}`);
    setTimeout(() => setErrorMsg(''), 5000);
  }
};

  const handleRevoke = (id) => {
    setPendingInvites(prev =>
      prev.map(inv => (inv.id === id ? { ...inv, status: 'Revoked' } : inv))
    );
  };

  const handleResend = (id) => {
    setPendingInvites(prev =>
      prev.map(inv => (inv.id === id ? { ...inv, status: 'Pending', date: 'Jun 22, 2025' } : inv))
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Tab header */}
      <div className="pb-5 border-b border-gray-100 dark:border-slate-800">
        <h2 className="text-lg font-bold text-gray-900 dark:text-slate-100">Invitations</h2>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">
          Invite teammates and manage outstanding invitations
        </p>
      </div>

      {/* Invite card */}
      <div className="border border-gray-200 dark:border-slate-700 rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30">
          <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100">Invite your team</h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
            Team members get a role-scoped experience from day one.
          </p>
        </div>

        <div className="px-6 py-5 space-y-3">
          {inviteRows.map((row) => (
            <div key={row.id} className="flex items-center gap-3">
              {/* Email input */}
              <div className="flex-1 relative">
                <i className="fa-regular fa-envelope absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 text-xs pointer-events-none" />
                <input
                  type="email"
                  placeholder="teammate@company.com"
                  value={row.email}
                  onChange={e => updateRow(row.id, 'email', e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 text-sm bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand/40 placeholder:text-gray-400 dark:placeholder:text-slate-500 text-gray-900 dark:text-slate-200 transition-all"
                />
              </div>

              {/* Role dropdown */}
              <select
                value={row.role}
                onChange={e => updateRow(row.id, 'role', e.target.value)}
                className="w-44 px-3 py-2.5 text-sm bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand/40 text-gray-700 dark:text-slate-300 transition-all"
              >
                <option value="">Select role</option>
                {ROLES.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>

              {/* Remove row */}
              {inviteRows.length > 1 && (
                <button
                  onClick={() => removeRow(row.id)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all flex-shrink-0"
                >
                  <i className="fa-solid fa-xmark text-sm" />
                </button>
              )}
            </div>
          ))}

          {/* Add another row */}
          <button
            onClick={addRow}
            className="flex items-center gap-1.5 text-xs font-medium text-brand hover:text-brand-hover dark:text-blue-400 dark:hover:text-blue-300 transition-colors mt-1"
          >
            <i className="fa-solid fa-plus text-[10px]" />
            Add another
          </button>
        </div>

        {/* Info note */}
        <div className="px-6 pb-5">
          <div className="flex items-start gap-2.5 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800/50">
            <i className="fa-solid fa-circle-info text-blue-500 dark:text-blue-400 text-xs mt-0.5 flex-shrink-0" />
            <p className="text-xs text-blue-600 dark:text-blue-400 leading-relaxed">
              If the invitee already has a Realify account, they'll be attached without creating a duplicate.
              Invites expire in <strong>7 days</strong> — you can re-send anytime.
            </p>
          </div>
        </div>

        {/* Error banner */}
        {errorMsg && (
          <div className="mx-6 mb-4 flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-100 dark:border-red-800/50">
            <i className="fa-solid fa-circle-exclamation text-red-500 text-xs flex-shrink-0" />
            <p className="text-xs text-red-600 dark:text-red-400">{errorMsg}</p>
          </div>
        )}

        {/* Footer actions */}
        <div className="px-6 py-4 border-t border-gray-100 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30 flex items-center justify-end">
          <button
            onClick={handleSendInvites}
            disabled={isSending}
            className="px-5 py-2 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition-all shadow-md shadow-black/10 dark:shadow-gray-700/20 active:scale-95 flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isSending ? (
              <>
                <i className="fa-solid fa-circle-notch fa-spin" />
                Sending…
              </>
            ) : inviteSent ? (
              <>
                <i className="fa-solid fa-check" />
                Sent!
              </>
            ) : (
              <>
                <i className="fa-solid fa-paper-plane" />
                Send Invites
              </>
            )}
          </button>
        </div>
      </div>

      {/* Pending invites */}
      <div className="border border-gray-200 dark:border-slate-700 rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30">
          <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100">Pending &amp; Past Invites</h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
            Track the status of all invitations you've sent
          </p>
        </div>

        <div className="overflow-x-auto">
          {/* Column headers */}
          <div className="px-6 py-2.5 grid grid-cols-[1fr_140px_90px_110px_110px] gap-4 min-w-[580px]">
            {['Email', 'Role', 'Status', 'Invited', 'Actions'].map(h => (
              <span key={h} className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">
                {h}
              </span>
            ))}
          </div>

          <div className="divide-y divide-gray-100 dark:divide-slate-800">
            {pendingInvites.map(inv => {
              const s = STATUS_CONFIG[inv.status];
              const canAct = inv.status === 'Pending' || inv.status === 'Expired';
              return (
                <div
                  key={inv.id}
                  className="px-6 py-3.5 grid grid-cols-[1fr_140px_90px_110px_110px] gap-4 items-center hover:bg-gray-50/50 dark:hover:bg-slate-800/30 transition-colors min-w-[580px]"
                >
                  <span className="text-sm text-gray-700 dark:text-slate-300 truncate">{inv.email}</span>
                  <span className="text-xs text-gray-500 dark:text-slate-400 truncate">{inv.role}</span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] font-bold border w-fit ${s.bg} ${s.text} ${s.border}`}
                  >
                    {inv.status}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-slate-500">{inv.date}</span>
                  <div className="flex items-center gap-1.5">
                    {canAct ? (
                      <>
                        <button
                          onClick={() => handleResend(inv.id)}
                          className="text-[11px] font-medium text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Resend
                        </button>
                        <span className="text-gray-300 dark:text-slate-600">·</span>
                        <button
                          onClick={() => handleRevoke(inv.id)}
                          className="text-[11px] font-medium text-red-500 hover:underline"
                        >
                          Revoke
                        </button>
                      </>
                    ) : (
                      <span className="text-[11px] text-gray-300 dark:text-slate-600">—</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InviteTeamTab;
