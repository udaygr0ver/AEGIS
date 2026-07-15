import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Activity, Database, ArrowUpRight, CheckCircle, Clock, ExternalLink } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { statsAPI, alertsAPI } from '../services/api';
import Header from '../components/Header';

export default function Overview() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [statsRes, alertsRes, trendsRes] = await Promise.all([
        statsAPI.getOverview(),
        alertsAPI.getAlerts({ page: 1, page_size: 6 }),
        alertsAPI.getTrends(24)
      ]);
      setStats(statsRes.data);
      setAlerts(alertsRes.data.items);
      setTrends(trendsRes.data);
    } catch (err) {
      console.error("Error fetching overview telemetry:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'critical':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/40 uppercase">Critical</span>;
      case 'high':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-500/20 text-orange-400 border border-orange-500/40 uppercase">High</span>;
      case 'medium':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 uppercase">Medium</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/40 uppercase">Low</span>;
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header title="Security Operations Center (SOC)" onRefresh={handleRefresh} isRefreshing={refreshing} />

      <main className="p-8 space-y-8 max-w-[1600px] w-full mx-auto">
        {/* KPI Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Total Ingested Logs */}
          <div className="p-6 rounded-2xl glass-panel glass-panel-hover relative overflow-hidden">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ingested Logs</p>
                <h3 className="text-3xl font-extrabold text-white mt-2 font-mono">{stats?.total_logs?.toLocaleString() || 0}</h3>
              </div>
              <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
                <Database className="w-6 h-6" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-xs text-emerald-400">
              <Activity className="w-3.5 h-3.5 mr-1 animate-pulse" />
              <span>Real-time normalized stream</span>
            </div>
          </div>

          {/* Card 2: Active Alerts */}
          <div className="p-6 rounded-2xl glass-panel glass-panel-hover">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Open Incidents</p>
                <h3 className="text-3xl font-extrabold text-white mt-2 font-mono">{stats?.open_alerts?.toLocaleString() || 0}</h3>
              </div>
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
            </div>
            <div className="mt-4 text-xs text-slate-400">
              <span>Out of {stats?.total_alerts || 0} total generated</span>
            </div>
          </div>

          {/* Card 3: Critical Severity */}
          <div className="p-6 rounded-2xl glass-panel glass-panel-hover relative">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Critical Threats</p>
                <h3 className="text-3xl font-extrabold text-red-400 mt-2 font-mono">{stats?.critical_alerts?.toLocaleString() || 0}</h3>
              </div>
              <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/40 flex items-center justify-center text-red-400 glow-critical">
                <Shield className="w-6 h-6" />
              </div>
            </div>
            <div className="mt-4 text-xs text-red-400 font-medium flex items-center">
              <span>Requires immediate analyst action</span>
            </div>
          </div>

          {/* Card 4: Top Attacker IP */}
          <div className="p-6 rounded-2xl glass-panel glass-panel-hover">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Top Threat Vector</p>
                <h3 className="text-xl font-bold text-sky-400 mt-2 font-mono truncate max-w-[180px]">
                  {stats?.top_attackers?.[0]?.src_ip || 'None Detected'}
                </h3>
              </div>
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <ArrowUpRight className="w-6 h-6" />
              </div>
            </div>
            <div className="mt-4 text-xs text-slate-400 font-mono">
              <span>{stats?.top_attackers?.[0]?.alert_count || 0} triggered security alerts</span>
            </div>
          </div>
        </div>

        {/* Middle Section: Attack Trends Chart */}
        <div className="p-6 rounded-2xl glass-panel">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold text-white">Threat Detection Timeline (24 Hours)</h3>
              <p className="text-xs text-slate-400">Alert frequency trends bucketed by detection rule</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={11} tickFormatter={(str) => str.split(' ')[1] || str} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Area type="monotone" dataKey="total" stroke="#0ea5e9" strokeWidth={2} fillOpacity={1} fill="url(#colorTotal)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bottom Grid: Recent Alerts & Top Attacking IPs */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Alerts Feed (2 cols) */}
          <div className="lg:col-span-2 p-6 rounded-2xl glass-panel space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold text-white">Live Security Alert Stream</h3>
              <a href="/alerts" className="text-xs text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1">
                View All <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            <div className="space-y-3">
              {alerts.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">No security alerts triggered yet.</div>
              ) : (
                alerts.map((a) => (
                  <div key={a.id} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-all">
                    <div className="space-y-1 max-w-lg">
                      <div className="flex items-center space-x-3">
                        {getSeverityBadge(a.severity)}
                        <span className="font-semibold text-sm text-slate-100">{a.title}</span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-1">{a.description}</p>
                      <div className="flex items-center space-x-4 text-[11px] text-slate-500 font-mono">
                        <span>IP: {a.src_ip || 'N/A'}</span>
                        <span>Time: {new Date(a.triggered_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                    <div>
                      <span className={`px-3 py-1 rounded-lg text-xs font-mono capitalize ${a.status === 'open' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
                        {a.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Top Attackers Table (1 col) */}
          <div className="p-6 rounded-2xl glass-panel space-y-4">
            <h3 className="text-lg font-bold text-white">Top Attacking IPs</h3>

            <div className="space-y-3">
              {stats?.top_attackers?.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">No attacker IPs logged.</div>
              ) : (
                stats?.top_attackers?.map((att, i) => (
                  <div key={att.src_ip} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="w-6 h-6 rounded-md bg-slate-800 text-xs font-bold text-sky-400 flex items-center justify-center font-mono">
                        #{i + 1}
                      </span>
                      <div>
                        <p className="text-sm font-mono font-bold text-slate-200">{att.src_ip}</p>
                        <p className="text-xs text-slate-500">{att.log_count} total log events</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-red-400 font-mono">{att.alert_count} Alerts</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
