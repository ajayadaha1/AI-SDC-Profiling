import axios from 'axios';

const api = axios.create({
  baseURL: '/ai-sdc-profiling-api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
