import axios from 'axios';

const authClient = axios.create({
  baseURL: '/auth',
});

authClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

authClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      sessionStorage.setItem('sessionExpired', 'true');
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