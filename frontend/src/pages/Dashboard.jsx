import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api/client";
import { money } from "../components/ui.jsx";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Dashboard() {
  const { isManager } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get("/api/reports/dashboard/")).data,
  });

  if (isLoading || !data) return <p>Loading dashboard…</p>;

  const statusOrder = ["PENDING", "ASSIGNED", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"];
  const chart = statusOrder
    .filter((s) => data.jobs_by_status[s])
    .map((s) => ({ status: s.replaceAll("_", " "), count: data.jobs_by_status[s] }));

  return (
    <div>
      <div className="mb-6 font-mono text-sm tracking-[0.3em] text-[#7a5b14]">FIELDOPS</div>
      <div className="stat-grid">
        <Card label="Today's Jobs" value={data.today_jobs} />
        <Card label="Completed" value={data.completed} />
        <Card label="Overdue" value={data.overdue} accent />
      </div>
      <div className="stat-grid mt-3">
        <Card label="Revenue" value={money(data.revenue)} />
        <Card label="Expenses" value={money(data.expenses)} />
        <Card label="Profit" value={money(data.profit)} />
      </div>

      <section className="mt-8 rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-5">
        <h2 className="mb-4 text-lg font-semibold">Jobs by status</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <XAxis dataKey="status" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#1b4d43" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {isManager && (
        <section className="mt-6 rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-5">
          <h2 className="mb-4 text-lg font-semibold">Technician performance</h2>
          <div className="space-y-3">
            {(data.technician_performance || []).map((t) => (
              <div key={t.id} className="flex items-center justify-between border-b border-[#eee4d2] pb-2">
                <span className="font-medium">{t.name}</span>
                <span className="text-sm text-[#5c6f6a]">
                  {t.jobs} jobs · {t.rate}% completion
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function Card({ label, value, accent }) {
  return (
    <div className={`rounded-xl border p-4 ${accent ? "border-[#c45c26] bg-[#f8e6d8]" : "border-[#d8ccb4] bg-[#fbf8f2]"}`}>
      <div className="text-xs uppercase tracking-wider text-[#7a6a4e]">{label}</div>
      <div className="mt-2 font-mono text-3xl">{value}</div>
    </div>
  );
}
