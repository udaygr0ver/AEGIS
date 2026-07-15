import React, { useState, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { statsAPI, alertsAPI } from '../services/api';
import Header from '../components/Header';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6'
};

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, trendsRes] = await Promise.all([
        statsAPI.getOverview(),
        alertsAPI.getTrends(24)
      ]);
      setStats(statsRes.data);
      setTrends(trendsRes.data);
    } catch (err) {
      console.error("Error fetching analytics data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const severityPieData = stats?.alerts_by_severity ? [
    { name: 'Critical', value: stats.alerts_by_severity.critical, color: SEVERITY_COLORS.critical },
    { name: 'High', value: stats.alerts_by_severity.high, color: SEVERITY_COLORS.high },
    { name: 'Medium', value: stats.alerts_by_severity.medium, color: SEVERITY_COLORS.medium },
    { name: 'Low', value: stats.alerts_by_severity.low, color: SEVERITY_COLORS.low }
  ].filter(d => d.value > 0) : [];

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header title="Security Intelligence & Analytics" onRefresh={fetchData} isRefreshing={loading} />

      <main className="p-8 space-y-8 max-w-[1600px] w-full mx-auto">
        {/* Top Chart: 24h Attack Trend */}
        <div className="p-6 rounded-2xl glass-panel space-y-4">
          <div>
            <h3 className="text-lg font-bold text-white">Rule Evaluation & Attack Volume (24h)</h3>
            <p className="text-xs text-slate-400">Total detected incidents aggregated hourly</p>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends}>
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={11} tickFormatter={(t) => t.split(' ')[1] || t} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }} />
                <Area type="monotone" dataKey="total" stroke="#0ea5e9" strokeWidth={2} fill="url(#areaGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Grid: Pie & Bar Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pie Chart: Alert Severity Distribution */}
          <div className="p-6 rounded-2xl glass-panel space-y-4">
            <h3 className="text-lg font-bold text-white">Incident Severity Distribution</h3>
            <div className="h-64 w-full flex items-center justify-center">
              {severityPieData.length === 0 ? (
                <div className="text-slate-500 text-sm">No severity data available</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={severityPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {severityPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }} />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Bar Chart: Top Attacker IPs */}
          <div className="p-6 rounded-2xl glass-panel space-y-4">
            <h3 className="text-lg font-bold text-white">Top Attacking Source IPs</h3>
            <div className="h-64 w-full">
              {!stats?.top_attackers || stats.top_attackers.length === 0 ? (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm">No attacker IPs logged</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.top_attackers} layout="vertical" margin={{ left: 20 }}>
                    <XAxis type="number" stroke="#475569" fontSize={11} />
                    <YAxis dataKey="src_ip" type="category" stroke="#94a3b8" fontSize={11} width={100} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }} />
                    <Bar dataKey="alert_count" fill="#38bdf8" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
