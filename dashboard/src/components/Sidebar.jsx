import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Shield, Activity, FileText, AlertTriangle, BarChart3, LogOut, Radio } from 'lucide-react';

export default function Sidebar({ user, onLogout }) {
  const navItems = [
    { path: '/', label: 'SOC Overview', icon: Activity },
    { path: '/logs', label: 'Logs Explorer', icon: FileText },
    { path: '/alerts', label: 'Alert Triage', icon: AlertTriangle },
    { path: '/analytics', label: 'Analytics & Trends', icon: BarChart3 },
    { path: '/reports', label: 'Reports Export', icon: Shield },
  ];

  return (
    <aside className="w-64 bg-[#0c1220] border-r border-slate-800/80 flex flex-col justify-between h-screen sticky top-0 z-30">
      <div>
        {/* Brand Logo Header */}
        <div className="p-6 border-b border-slate-800/80 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide leading-tight">AEGIS SIEM</h1>
            <p className="text-xs text-sky-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              LIVE ANALYTICS
            </p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-sm shadow-sky-500/10'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* User Info Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-[#080d18]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-sky-400 text-sm">
              {user?.username?.[0]?.toUpperCase() || 'A'}
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200 leading-none">{user?.username || 'Analyst'}</p>
              <p className="text-xs text-slate-500 capitalize mt-1">{user?.role || 'SOC Analyst'}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            title="Log Out"
            className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
