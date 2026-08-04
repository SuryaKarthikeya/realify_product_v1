import React from 'react';

const TeamTab = ({ onOpenInvite }) => {
  const members = [
    { id: 1, name: 'Rohit Sharma', email: 'rohit@realify.ai', role: 'Owner', status: 'Active', initials: 'R', color: 'bg-slate-800' },
    { id: 2, name: 'Mark Chen', email: 'mark@realify.ai', role: 'Admin', status: 'Active', initials: 'M', color: 'bg-emerald-600' },
    { id: 3, name: 'Sarah Ops', email: 'sarah.ops@acmepets.com', role: 'Analyst', status: 'Pending', initials: 'S', color: 'bg-amber-600', isPending: true },
  ];

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm">
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Team Members</h3>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Manage who has access to this workspace</p>
          </div>
          <button
            onClick={onOpenInvite}
            className="px-4 py-2 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition-all shadow-md shadow-black/10 dark:shadow-gray-700/20 active:scale-95"
          >
            <i className="fa-solid fa-plus mr-2"></i>Invite Member
          </button>
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-4">
          {members.map((member) => (
            <div
              key={member.id}
              className={`flex items-center justify-between p-4 rounded-2xl border transition-all ${member.isPending
                  ? 'border-dashed border-gray-300 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-800/30'
                  : 'border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900/50 shadow-sm'
                }`}
            >
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl ${member.color} flex items-center justify-center text-white text-sm font-bold shadow-sm`}>
                  {member.isPending ? <i className="fa-solid fa-clock"></i> : member.initials}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className={`text-sm font-bold ${member.isPending ? 'text-gray-500 dark:text-slate-400' : 'text-gray-900 dark:text-slate-100'}`}>
                      {member.name || member.email}
                    </p>
                    {member.isPending && (
                      <span className="px-2 py-0.5 bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded-lg text-[10px] font-bold border border-amber-100 dark:border-amber-800">
                        PENDING
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-slate-500">{member.email}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {!member.isPending ? (
                  <>
                    <select className="bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs font-bold outline-none focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30/20 dark:text-slate-300">
                      <option>Admin</option>
                      <option>Analyst</option>
                      <option>Viewer</option>
                    </select>
                    <div className="flex items-center gap-2">
                      <span className={`px-3 py-1 rounded-lg text-[10px] font-bold border ${member.role === 'Owner'
                          ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800'
                          : 'bg-gray-50 dark:bg-slate-800 text-gray-600 dark:text-slate-400 border-gray-200 dark:border-slate-700'
                        }`}>
                        {member.role}
                      </span>
                      {member.role !== 'Owner' && (
                        <button className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all">
                          <i className="fa-solid fa-trash-can text-sm"></i>
                        </button>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="flex items-center gap-2">
                    <button className="px-3 py-1.5 text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline">
                      Resend Invite
                    </button>
                    <button className="px-3 py-1.5 text-xs font-bold text-red-500 hover:underline">
                      Revoke
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TeamTab;
