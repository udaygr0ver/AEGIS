import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Clock, ShieldAlert, Eye, Filter, ArrowRight } from 'lucide-react';
import { alertsAPI } from '../services/api';
import Header from '../components/Header';

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [selectedAlertDetail, setSelectedAlertDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await alertsAPI.getAlerts({
        page,
        page_size: 15,
        status: statusFilter || undefined,
        severity: severityFilter || undefined
      });
      setAlerts(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error("Error fetching alerts:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [page, statusFilter, severityFilter]);

  const handleStatusChange = async (alertId, newStatus) => {
    try {
      await alertsAPI.updateStatus(alertId, newStatus);
      fetchAlerts();
      if (selectedAlertDetail?.alert?.id === alertId) {
        setSelectedAlertDetail(prev => prev ? { ...prev, alert: { ...prev.alert, status: newStatus } } : null);
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const handleViewDetail = async (alertId) => {
    try {
      const res = await alertsAPI.getAlertDetail(alertId);
      setSelectedAlertDetail(res.data);
    } catch (err) {
      console.error("Failed to load alert detail:", err);
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'critical':
        return <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-red-500/20 text-red-400 border border-red-500/40 uppercase">Critical</span>;
      case 'high':
        return <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-orange-500/20 text-orange-400 border border-orange-500/40 uppercase">High</span>;
      case 'medium':
        return <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 uppercase">Medium</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-blue-500/20 text-blue-400 border border-blue-500/40 uppercase">Low</span>;
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header title="Alert Triage & Incident Management" onRefresh={fetchAlerts} isRefreshing={loading} />

      <main className="p-8 space-y-6 max-w-[1600px] w-full mx-auto">
        {/* Filter Bar */}
        <div className="p-6 rounded-2xl glass-panel flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <Filter className="w-4 h-4 text-sky-400" />
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-slate-900 border border-slate-800 rounded-xl py-2 px-4 text-slate-300 text-sm focus:outline-none focus:border-sky-500"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
            </select>

            <select
              value={severityFilter}
              onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
              className="bg-slate-900 border border-slate-800 rounded-xl py-2 px-4 text-slate-300 text-sm focus:outline-none focus:border-sky-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Showing {alerts.length} of {total} incidents
          </div>
        </div>

        {/* Incident Alert Cards */}
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="p-12 text-center rounded-2xl glass-panel text-slate-500">
              No security alerts matching current filter criteria.
            </div>
          ) : (
            alerts.map((a) => (
              <div
                key={a.id}
                className={`p-6 rounded-2xl glass-panel transition-all ${
                  a.severity === 'critical' ? 'border-l-4 border-l-red-500' :
                  a.severity === 'high' ? 'border-l-4 border-l-orange-500' : 'border-l-4 border-l-yellow-500'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-3">
                      {getSeverityBadge(a.severity)}
                      <span className="font-mono text-xs text-slate-400 uppercase bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        Rule: {a.rule_name}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">
                        {new Date(a.triggered_at).toLocaleString()}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-white tracking-tight">{a.title}</h3>
                    <p className="text-sm text-slate-300">{a.description}</p>

                    <div className="flex items-center space-x-6 text-xs font-mono text-slate-400 pt-1">
                      <span>Source IP: <strong className="text-sky-400">{a.src_ip || 'N/A'}</strong></span>
                      <span>Target: <strong className="text-slate-200">{a.dest_ip || '127.0.0.1'}</strong></span>
                    </div>
                  </div>

                  {/* Actions & Status Dropdown */}
                  <div className="flex items-center space-x-3 shrink-0">
                    <button
                      onClick={() => handleViewDetail(a.id)}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 flex items-center gap-2 transition-all"
                    >
                      <Eye className="w-3.5 h-3.5 text-sky-400" />
                      <span>Investigate Logs</span>
                    </button>

                    <div className="flex rounded-xl bg-slate-900 border border-slate-800 p-1 space-x-1">
                      <button
                        onClick={() => handleStatusChange(a.id, 'open')}
                        className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all ${a.status === 'open' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'text-slate-400 hover:text-white'}`}
                      >
                        Open
                      </button>
                      <button
                        onClick={() => handleStatusChange(a.id, 'acknowledged')}
                        className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all ${a.status === 'acknowledged' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-white'}`}
                      >
                        Ack
                      </button>
                      <button
                        onClick={() => handleStatusChange(a.id, 'resolved')}
                        className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all ${a.status === 'resolved' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-400 hover:text-white'}`}
                      >
                        Resolved
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal: Related Log Inspection Drawer */}
        {selectedAlertDetail && (
          <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl">
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/80">
                <div>
                  <h3 className="font-bold text-white text-lg">{selectedAlertDetail.alert.title}</h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">UUID: {selectedAlertDetail.alert.alert_uuid}</p>
                </div>
                <button onClick={() => setSelectedAlertDetail(null)} className="text-slate-400 hover:text-white">✕</button>
              </div>

              <div className="p-6 overflow-y-auto space-y-6 flex-1">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Alert Summary</h4>
                  <p className="text-sm text-slate-200 p-4 rounded-xl bg-slate-900 border border-slate-800">
                    {selectedAlertDetail.alert.description}
                  </p>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                    Evidence & Related Raw Logs ({selectedAlertDetail.related_logs.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedAlertDetail.related_logs.map((log) => (
                      <div key={log.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-1">
                        <div className="flex justify-between text-slate-500 text-[10px]">
                          <span>{new Date(log.timestamp).toLocaleString()}</span>
                          <span className="text-sky-400 font-bold">{log.source_type}</span>
                        </div>
                        <p className="text-slate-200">{log.message_raw}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="p-4 bg-slate-900 border-t border-slate-800 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedAlertDetail(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
