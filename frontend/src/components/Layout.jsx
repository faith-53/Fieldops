import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import { useAuth } from "../auth/AuthContext.jsx";

const managerLinks = [
  ["/", "Dashboard"],
  ["/jobs", "Jobs"],
  ["/customers", "Customers"],
  ["/expenses", "Expenses"],
  ["/reports", "Reports"],
  ["/users", "Users"],
];

const techLinks = [
  ["/", "Today"],
  ["/jobs", "My Jobs"],
  ["/expenses", "Expenses"],
];

export default function Layout() {
  const { user, logout, isManager } = useAuth();
  const navigate = useNavigate();
  const links = isManager ? managerLinks : techLinks;
  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get("/api/notifications/")).data,
    refetchInterval: 30000,
  });
  const unread = (data?.results || []).filter((n) => !n.is_read).length;

  return (
    <div className="min-h-screen bg-[#efe8da]">
      <header className="border-b border-[#d8ccb4] bg-[#10231f] text-[#f4efe6]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <div>
            <div className="font-mono text-xs tracking-[0.35em] text-[#e0c48a]">FIELDOPS</div>
            <div className="text-sm text-[#c9d7d2]">Field service & operations</div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <button onClick={() => navigate("/notifications")} className="relative">
              Notifications
              {unread > 0 && (
                <span className="ml-2 rounded-full bg-[#c45c26] px-2 py-0.5 text-xs">{unread}</span>
              )}
            </button>
            <span className="text-[#c9d7d2]">
              {user?.name} · {user?.role}
            </span>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="rounded border border-[#3d5f58] px-3 py-1"
            >
              Sign out
            </button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 px-5 pb-3">
          {links.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `rounded px-3 py-1.5 text-sm ${isActive ? "bg-[#2f6f62] text-white" : "text-[#d7e4df] hover:bg-[#1b4d43]"}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-5 py-6">
        <Outlet />
      </main>
    </div>
  );
}
