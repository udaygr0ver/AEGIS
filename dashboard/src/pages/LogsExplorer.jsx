import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, ChevronLeft, ChevronRight, Eye, Code } from 'lucide-react';
import { logsAPI } from '../services/api';
import Header from '../components/Header';

export default function LogsExplorer() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [srcIp, setSrcIp] = useState('');
  const [severity, setSeverity] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await logsAPI.getLogs({
        page,
        page_size: pageSize,
        search: search || undefined,
        src_ip: srcIp || undefined,
        severity: severity || undefined,
        source_type: sourceType || undefined
      });
      setLogs(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error("Error fetching logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, severity, sourceType]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const handleExportCSV = async () => {
    try {
      const res = await logsAPI.exportCSV({ search, src_ip: srcIp, severity, source_type: sourceType });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `siem_export_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Failed to export CSV:", err);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  const getSeverityPill = (sev) => {
    switch (sev) {
      case 'critical':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 uppercase">Critical</span>;
      case 'high':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30 uppercase">High</span>;
      case 'medium':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 uppercase">Medium</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30 uppercase">Low</span>;
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header title="Logs Explorer & Search" onRefresh={fetchLogs} isRefreshing={loading} />

      <main className="p-8 space-y-6 max-w-[1600px] w-full mx-auto">
        {/* Filter Controls Bar */}
        <div className="p-6 rounded-2xl glass-panel space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-4">
            {/* Search Input */}
            <div className="flex-1 min-w-[300px] relative">
              <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search raw log message, user, or IP..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-white text-sm focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>

            {/* IP Filter */}
            <div className="w-44">
              <input
                type="text"
                value={srcIp}
                onChange={(e) => setSrcIp(e.target.value)}
                placeholder="Filter by Source IP..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl py-2.5 px-3 text-white text-sm focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>

            {/* Source Type Filter */}
            <select
              value={sourceType}
              onChange={(e) => { setSourceType(e.target.value); setPage(1); }}
              className="bg-slate-900 border border-slate-800 rounded-xl py-2.5 px-3 text-slate-300 text-sm focus:outline-none focus:border-sky-500"
            >
              <option value="">All Source Types</option>
              <option value="ssh">SSH Auth</option>
              <option value="nginx">Nginx / Apache</option>
              <option value="syslog">Syslog</option>
              <option value="custom">Custom / Fallback</option>
            </select>

            {/* Severity Filter */}
            <select
              value={severity}
              onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
              className="bg-slate-900 border border-slate-800 rounded-xl py-2.5 px-3 text-slate-300 text-sm focus:outline-none focus:border-sky-500"
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>

            <button
              type="submit"
              className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-white rounded-xl font-medium text-sm transition-all shadow-md shadow-sky-500/20"
            >
              Filter Logs
            </button>

            <button
              type="button"
              onClick={handleExportCSV}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl font-medium text-sm flex items-center gap-2 transition-all ml-auto"
            >
              <Download className="w-4 h-4 text-sky-400" />
              <span>Export CSV</span>
            </button>
          </form>
        </div>

        {/* Logs Data Table */}
        <div className="rounded-2xl glass-panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/90 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-6">Timestamp</th>
                  <th className="py-3.5 px-6">Severity</th>
                  <th className="py-3.5 px-6">Source</th>
                  <th className="py-3.5 px-6">Event Type</th>
                  <th className="py-3.5 px-6">Source IP</th>
                  <th className="py-3.5 px-6">User</th>
                  <th className="py-3.5 px-6">Raw Log Message</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12 text-slate-500 font-sans">
                      {loading ? 'Fetching log events...' : 'No matching log entries found.'}
                    </td>
                  </tr>
                ) : (
                  logs.map((l) => (
                    <tr key={l.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-6 text-slate-400 whitespace-nowrap">
                        {new Date(l.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-6 whitespace-nowrap">{getSeverityPill(l.severity)}</td>
                      <td className="py-3 px-6 text-sky-400 font-bold uppercase whitespace-nowrap">{l.source_type}</td>
                      <td className="py-3 px-6 text-slate-300 capitalize whitespace-nowrap">{l.event_type}</td>
                      <td className="py-3 px-6 text-slate-200 whitespace-nowrap">{l.src_ip || '-'}</td>
                      <td className="py-3 px-6 text-amber-400 whitespace-nowrap">{l.user || '-'}</td>
                      <td className="py-3 px-6 text-slate-300 truncate max-w-md" title={l.message_raw}>
                        {l.message_raw}
                      </td>
                      <td className="py-3 px-6 text-right whitespace-nowrap">
                        <button
                          onClick={() => setSelectedLog(l)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-sky-400 hover:bg-slate-800 transition-colors"
                          title="View JSON details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-900/50">
            <span className="text-xs text-slate-400">
              Showing page <strong className="text-white">{page}</strong> of <strong className="text-white">{totalPages}</strong> ({total} total logs)
            </span>

            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Modal: View Raw Log JSON */}
        {selectedLog && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
              <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <Code className="w-5 h-5 text-sky-400" />
                  <h3 className="font-bold text-white text-lg">Log Event Detail</h3>
                </div>
                <button onClick={() => setSelectedLog(null)} className="text-slate-400 hover:text-white">✕</button>
              </div>
              <div className="p-6 max-h-[70vh] overflow-y-auto">
                <pre className="p-4 rounded-xl bg-slate-950 text-sky-300 text-xs font-mono overflow-x-auto border border-slate-800">
                  {JSON.stringify(selectedLog, null, 2)}
                </pre>
              </div>
              <div className="p-4 bg-slate-900 border-t border-slate-800 text-right">
                <button
                  onClick={() => setSelectedLog(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm"
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
