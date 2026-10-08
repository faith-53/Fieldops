import { createContext, useContext, useEffect, useMemo, useState } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("fieldops_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("fieldops_access");
    if (!token) {
      setReady(true);
      return;
    }
    api
      .get("/api/auth/me/")
      .then((res) => {
        setUser(res.data);
        localStorage.setItem("fieldops_user", JSON.stringify(res.data));
      })
      .catch(() => {
        localStorage.removeItem("fieldops_access");
        localStorage.removeItem("fieldops_refresh");
        localStorage.removeItem("fieldops_user");
        setUser(null);
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo(
    () => ({
      user,
      ready,
      isManager: user?.role === "ADMIN" || user?.role === "MANAGER",
      isTechnician: user?.role === "TECHNICIAN",
      async login(email, password) {
        const res = await api.post("/api/auth/login/", { email, password });
        localStorage.setItem("fieldops_access", res.data.access);
        localStorage.setItem("fieldops_refresh", res.data.refresh);
        localStorage.setItem("fieldops_user", JSON.stringify(res.data.user));
        setUser(res.data.user);
      },
      logout() {
        localStorage.removeItem("fieldops_access");
        localStorage.removeItem("fieldops_refresh");
        localStorage.removeItem("fieldops_user");
        setUser(null);
      },
    }),
    [user, ready]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
