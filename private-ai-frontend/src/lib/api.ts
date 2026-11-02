import axios from "axios";

const baseURL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export const api = axios.create({
  baseURL,
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("private-ai-token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item?.msg || "Invalid request").join(", ");
    }
    if (error.code === "ERR_NETWORK") {
      return `Cannot reach the API at ${baseURL}. Check that FastAPI is running and CORS allows this frontend.`;
    }
    return error.response?.status
      ? `Request failed (${error.response.status}).`
      : error.message;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}
