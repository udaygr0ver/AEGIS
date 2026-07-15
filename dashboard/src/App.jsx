import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Overview from './pages/Overview';
import LogsExplorer from './pages/LogsExplorer';
import AlertsPanel from './pages/AlertsPanel';
import Analytics from './pages/Analytics';
import Reports from './pages/Reports';

export default function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('siem_user');
    return saved ? JSON.parse(saved) : null;
  });

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('siem_token');
    localStorage.removeItem('siem_user');
    setUser(null);
  };

  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <Router>
      <div className="flex min-h-screen bg-[#090d16] text-slate-100">
        <Sidebar user={user} onLogout={handleLogout} />
        <div className="flex-1 flex flex-col min-w-0">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/logs" element={<LogsExplorer />} />
            <Route path="/alerts" element={<AlertsPanel />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
