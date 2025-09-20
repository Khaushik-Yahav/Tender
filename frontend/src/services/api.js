import axios from 'axios';
import toast from 'react-hot-toast';

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    if (error.response?.status !== 401) {
      toast.error(message);
    }
    return Promise.reject(error);
  }
);

// API methods
export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),
  
  // Statistics  
  getStatistics: () => api.get('/statistics'),
  
  // Ask questions
  askQuestion: async (questionData) => {
    const response = await api.post('/ask', questionData);
    return response.data;
  },
  
  // Document operations
  uploadDocument: async (formData) => {
    const response = await api.post('/upload-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  // Vendor evaluation
  evaluateVendor: async (evaluationData) => {
    const response = await api.post('/evaluate-vendor', evaluationData);
    return response.data;
  },
};

export default api;
