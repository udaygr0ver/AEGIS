import React, { useState } from 'react';
import { Download, FileText, Shield, CheckCircle2, Calendar } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { statsAPI, alertsAPI, logsAPI } from '../services/api';
import Header from '../components/Header';

export default function Reports() {
  const [range, setRange] = useState('24h');
  const [generating, setGenerating] = useState(false);

  const handleGeneratePDF = async () => {
    setGenerating(true);
    try {
      const [statsRes, alertsRes] = await Promise.all([
        statsAPI.getOverview(),
        alertsAPI.getAlerts({ page: 1, page_size: 50 })
      ]);

      const stats = statsRes.data;
      const alerts = alertsRes.data.items;

      const doc = new jsPDF();

      // Title Header
      doc.setFillColor(15, 23, 42); // dark blue background
      doc.rect(0, 0, 210, 40, 'F');
      
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(20);
      doc.setFont('helvetica', 'bold');
      doc.text('SIEM Executive Threat Report', 14, 22);

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(148, 163, 184);
      doc.text(`Generated: ${new Date().toUTCString()} | Period: ${range.toUpperCase()}`, 14, 32);

      // Section 1: Summary Statistics
      doc.setTextColor(15, 23, 42);
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('1. Executive Telemetry Summary', 14, 52);

      const summaryData = [
        ['Total Ingested Log Events', stats.total_logs.toLocaleString()],
        ['Total Incidents Triggered', stats.total_alerts.toLocaleString()],
        ['Active Open Incidents', stats.open_alerts.toLocaleString()],
        ['Critical Threats', stats.critical_alerts.toLocaleString()],
      ];

      autoTable(doc, {
        startY: 56,
        head: [['Metric', 'Count']],
        body: summaryData,
        theme: 'striped',
        headStyles: { fillStyle: 'F', fillColor: [14, 165, 233] }
      });

      // Section 2: Top Incidents Table
      const finalY = doc.lastAutoTable.previous.finalY || 100;
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('2. Critical & High Security Incidents', 14, finalY + 14);

      const alertRows = alerts.map(a => [
        new Date(a.triggered_at).toLocaleTimeString(),
        a.severity.toUpperCase(),
        a.rule_name,
        a.src_ip || 'N/A',
        a.title
      ]);

      autoTable(doc, {
        startY: finalY + 18,
        head: [['Timestamp', 'Severity', 'Rule', 'Source IP', 'Description']],
        body: alertRows,
        theme: 'grid',
        headStyles: { fillColor: [15, 23, 42] }
      });

      doc.save(`siem_executive_report_${range}_${Date.now()}.pdf`);
    } catch (err) {
      console.error("Failed to generate PDF report:", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const res = await logsAPI.exportCSV({});
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `siem_raw_logs_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Export failed:", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header title="Reports & Audit Compliance" />

      <main className="p-8 space-y-8 max-w-[1200px] w-full mx-auto">
        <div className="p-8 rounded-2xl glass-panel space-y-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Generate Executive Security Report</h3>
              <p className="text-xs text-slate-400">Download formatted PDF reports containing threat telemetry, incident breakdowns, and attacker rankings.</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 pt-4 border-t border-slate-800">
            <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-xl p-1">
              {['24h', '7d', '30d'].map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase transition-all ${
                    range === r ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Last {r}
                </button>
              ))}
            </div>

            <button
              onClick={handleGeneratePDF}
              disabled={generating}
              className="px-6 py-3 bg-gradient-to-r from-sky-500 to-cyan-500 hover:from-sky-400 hover:to-cyan-400 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-sky-500/20 flex items-center gap-2 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>{generating ? 'Compiling PDF Report...' : 'Download PDF Executive Report'}</span>
            </button>
          </div>
        </div>

        {/* CSV Raw Export Card */}
        <div className="p-8 rounded-2xl glass-panel space-y-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Raw Security Log Dump (CSV)</h3>
              <p className="text-xs text-slate-400">Export raw normalized log entries for external SIEM integration or compliance archiving.</p>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={handleExportCSV}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl font-semibold text-sm flex items-center gap-2 transition-all"
            >
              <Download className="w-4 h-4 text-emerald-400" />
              <span>Export Raw Logs to CSV</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
