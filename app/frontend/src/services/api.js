import axios from 'axios';

const tradingClient = axios.create({
  baseURL: '/api',
});

tradingClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

tradingClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    throw error;
  }
);

export const tradingAPI = {
  getPrediction: ({ spread_multiplier } = {}) => tradingClient.get('/prediction', { params: { spread_multiplier: spread_multiplier ?? 1 } }),
  getSignals: () => tradingClient.get('/signals'),
  getHistory: (params) => tradingClient.get('/history', { params }),
  getPriceHistory: (params) => tradingClient.get('/history/prices', { params }),
  getAlarms: () => tradingClient.get('/alarms'),
};

export const bankAPI = {
  listBanks: () => tradingClient.get('/banks'),
  getBank: (id) => tradingClient.get(`/banks/${id}`),
};

export const accountAPI = {
  getBalance: () => tradingClient.get('/account/balance'),
  getSolBalance: () => tradingClient.get('/account/sol-balance'),
  getBalanceHistory: (days) => tradingClient.get('/account/balance-history', { params: { days } }),
  getOptimalTrade: () => tradingClient.get('/account/optimal-trade'),
  getOrders: () => tradingClient.get('/orders'),
  createOrder: (data) => tradingClient.post('/orders', data),
};