import axios from 'axios';

const authClient = axios.create({
  baseURL: '/auth',
});

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

authClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      throw error;
    }
    throw new Error('Error de conexión');
  }
);

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

export const authAPI = {
  login: (username, password) => authClient.post('/login', { username, password }),
  register: (username, email, password) =>
    authClient.post('/register', { username, email, password }),
  verifyToken: () => authClient.get('/verify'),
  logout: () => authClient.post('/logout'),
};

export const tradingAPI = {
  getPrediction: () => tradingClient.get('/prediction'),
  getSignals: () => tradingClient.get('/signals'),
  getHistory: () => tradingClient.get('/history'),
  getAlarms: () => tradingClient.get('/alarms'),
};