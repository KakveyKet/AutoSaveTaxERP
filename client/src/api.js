import axios from 'axios';
import { io } from "socket.io-client"; // 1. Import Socket Client

// Define Base URL separately so both Axios and Socket can use it
const BASE_URL = 'http://127.0.0.1:8000';

// --- AXIOS SETUP ---
const api = axios.create({
  baseURL: `${BASE_URL}/api/`,
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
      // Optional: Redirect to login or clear token here
    }
    return Promise.reject(error);
  }
);

// --- SOCKET.IO SETUP ---
const socket = io(BASE_URL, {
  autoConnect: false, // Better to connect manually in App.vue or layouts
  transports: ['websocket', 'polling'], // Try websocket first for speed
});

// Export both
export { socket }; 
export default api;