import axios from 'axios';

// 1. Create the Axios instance
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  // CRITICAL FIX: I removed the 'headers' object here.
  // Do NOT set 'Content-Type': 'application/json'. 
  // Let Axios handle it automatically.
});

// 2. Request Interceptor: Attach Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 3. Response Interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      console.error('Unauthorized');
    }
    return Promise.reject(error);
  }
);

export default api;