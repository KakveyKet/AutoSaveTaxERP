import axios from 'axios';
import { io } from "socket.io-client";

// Ensure this matches your Uvicorn port (usually 8000)
const BASE_URL = 'http://127.0.0.1:8000';

// --- AXIOS SETUP ---
const api = axios.create({
  baseURL: `${BASE_URL}/api/`,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// --- SOCKET.IO SETUP ---
const socket = io(BASE_URL, {
  autoConnect: false,
  // Allow both transports. Polling helps verify if the endpoint exists at all.
  transports: ['websocket', 'polling'], 
  reconnectionAttempts: 5,
  reconnectionDelay: 3000,
});

export { socket }; 
export default api;