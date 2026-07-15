import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Attach JWT token if logged in
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('siem_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor for auth expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('siem_token');
      localStorage.removeItem('siem_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  getMe: () => api.get('/auth/me')
};

export const logsAPI = {
  getLogs: (params) => api.get('/logs', { params }),
  getLogById: (id) => api.get(`/logs/${id}`),
  exportCSV: (params) => api.get('/logs/export.csv', { params, responseType: 'blob' })
};

export const alertsAPI = {
  getAlerts: (params) => api.get('/alerts', { params }),
  getAlertDetail: (id) => api.get(`/alerts/${id}`),
  updateStatus: (id, status) => api.patch(`/alerts/${id}/status`, { status }),
  getTrends: (hours = 24) => api.get(`/alerts/trends`, { params: { hours } })
};

export const statsAPI = {
  getOverview: () => api.get('/stats/overview')
};

export default api;
