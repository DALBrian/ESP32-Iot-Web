import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 8000,
});

// 基礎 token auth（從 .env.local 讀值，或用 localStorage）
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token") || import.meta.env.VITE_AUTH_TOKEN;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
