import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_SERVER_URL ?? "http://localhost:8000";

// ── Singleton instance ──────────────────────────────────────────────────────
const axiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "69420",
  },
  timeout: 30_000,
});

// ── Request interceptor — attach Bearer token ───────────────────────────────
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Token lives in localStorage (set by authStore on login)
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("tm_access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// ── Response interceptor — unwrap data / handle 401 ────────────────────────
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    if (error.response?.status === 401) {
      // Clear stale token and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("tm_access_token");
        document.cookie = "tm_auth=; path=/; max-age=0";
        window.location.href = "/login";
      }
    }
    // Normalize error message for consumers
    const message =
      error.response?.data?.detail ??
      error.response?.data?.message ??
      error.message ??
      "An unexpected error occurred.";
    return Promise.reject(new Error(message));
  }
);

export default axiosInstance;
