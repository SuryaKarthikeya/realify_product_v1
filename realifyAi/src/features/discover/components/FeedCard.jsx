import React from 'react';

const FeedCard = ({ post }) => {
  return (
    <div className="feed-card bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden transition-all hover:shadow-md dark:hover:shadow-blue-900/10">
      <div className="p-5">
        <div className="flex items-start gap-3 mb-4">
          <img src={post.userAvatar} alt={post.userName}
            className="w-12 h-12 rounded-full object-cover border border-gray-100 dark:border-slate-700" />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-bold text-gray-900 dark:text-slate-100">{post.userName}</h4>
              {post.isVerified && <i className="fa-solid fa-circle-check text-blue-600 text-sm"></i>}
              <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
              <span className="text-sm text-gray-500 dark:text-slate-500">{post.time}</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-slate-400">{post.userRole} • {post.followers} followers</p>
          </div>
          <button
            className="px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg text-sm font-medium transition">
            <i className={`fa-solid ${post.isFollowing ? 'fa-check' : 'fa-user-plus'} mr-1`}></i>
            {post.isFollowing ? 'Following' : 'Follow'}
          </button>
        </div>

        <div className="mb-4">
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-2">{post.title}</h3>
          <p className="text-gray-700 dark:text-slate-300 mb-3 leading-relaxed">{post.content}</p>
          
          {post.dataSection && (
            <div className="mb-4">
              {post.dataType === 'market' ? (
                <div className="grid grid-cols-2 gap-3">
                  {post.dataSection.map((item, idx) => (
                    <div key={idx} className="bg-gray-50 dark:bg-slate-800/50 rounded-xl p-4 border border-gray-100 dark:border-slate-800">
                      <p className="text-xs text-gray-500 dark:text-slate-500 mb-1 tracking-wider">{item.label}</p>
                      <p className={`text-xl font-bold ${item.trend === 'up' ? 'text-green-600' : 'text-gray-900 dark:text-slate-100'}`}>
                        {item.value}
                      </p>
                      <p className={`text-xs mt-1 ${item.trend === 'up' ? 'text-green-600' : 'text-gray-500 dark:text-slate-500'}`}>
                        {item.subtext}
                      </p>
                    </div>
                  ))}
                </div>
              ) : post.dataType === 'gradient' ? (
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/10 dark:to-purple-900/10 rounded-xl p-4 border border-blue-100 dark:border-blue-900/20">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-white dark:bg-slate-800 rounded-lg flex items-center justify-center shadow-sm">
                      <i className={`fa-solid ${post.dataSection.icon} text-2xl text-blue-600`}></i>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900 dark:text-slate-200">{post.dataSection.label}</p>
                      <p className="text-2xl font-bold text-blue-600">{post.dataSection.value}</p>
                    </div>
                  </div>
                </div>
              ) : post.dataType === 'grid' ? (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {post.dataSection.map((item, idx) => (
                    <div key={idx} className={`${item.bg} rounded-xl p-3 text-center border ${item.border}`}>
                      <p className={`text-xs ${item.labelColor} mb-1`}>{item.label}</p>
                      <p className={`text-xl font-bold ${item.valueColor}`}>{item.value}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          )}

          <div className="flex gap-2 flex-wrap">
            {post.tags.map((tag, idx) => (
              <span key={idx} className={`px-3 py-1 ${tag.bg} ${tag.text} rounded-lg text-xs font-medium`}>
                #{tag.label}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-slate-800">
          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 text-gray-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition">
              <i className="fa-regular fa-thumbs-up"></i>
              <span className="text-sm font-medium">{post.likes}</span>
            </button>
            <button className="flex items-center gap-2 text-gray-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition">
              <i className="fa-regular fa-comment"></i>
              <span className="text-sm font-medium">{post.comments}</span>
            </button>
            <button className="flex items-center gap-2 text-gray-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition">
              <i className="fa-solid fa-share"></i>
              <span className="text-sm font-medium">{post.shares}</span>
            </button>
          </div>
          <button className="text-gray-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition">
            <i className="fa-regular fa-bookmark"></i>
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedCard;
