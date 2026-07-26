import axios from 'axios';

const authClient = axios.create({
  baseURL: '/auth',
});

authClient.interceptors.response.use(
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