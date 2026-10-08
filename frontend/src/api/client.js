import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fieldops_access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("fieldops_refresh");
      if (refresh) {
        try {
          const res = await axios.post("/api/auth/refresh/", { refresh });
          localStorage.setItem("fieldops_access", res.data.access);
          original.headers.Authorization = `Bearer ${res.data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem("fieldops_access");
          localStorage.removeItem("fieldops_refresh");
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
