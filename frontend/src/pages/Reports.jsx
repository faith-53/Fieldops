import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";

export default function Reports() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const params = { ...(start ? { start } : {}), ...(end ? { end } : {}) };
  const jobs = useQuery({
    queryKey: ["job-report", start, end],
    queryFn: async () => (await api.get("/api/reports/jobs/", { params })).data,
  });
  const techs = useQuery({
    queryKey: ["tech-report", start, end],
    queryFn: async () => (await api.get("/api/reports/technicians/", { params })).data,
  });

  async function exportFile(path, format) {
    const res = await api.get(`/api/${path}`, { params: { ...params, format }, responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = format === "pdf" ? "fieldops-report.pdf" : "fieldops-report.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const r = jobs.data;
  return (
    <div>
      <h1 className="text-2xl font-semibold">Reports</h1>
      <div className="mt-4 flex flex-wrap gap-2">
        <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="rounded border px-2 py-1" />
        <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="rounded border px-2 py-1" />
      </div>
      {r && (
        <section className="mt-6 rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Job report</h2>
            <div className="flex gap-2">
              <button onClick={() => exportFile("reports/jobs/", "csv")} className="rounded border px-3 py-1 text-sm">
                CSV
              </button>
              <button onClick={() => exportFile("reports/jobs/", "pdf")} className="rounded border px-3 py-1 text-sm">
                PDF
              </button>
            </div>
          </div>
          <p className="mt-1 text-sm text-[#5c6f6a]">
            Period: {r.start} – {r.end}
          </p>
          <dl className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Total jobs" value={r.total_jobs} />
            <Stat label="Completed" value={r.completed} />
            <Stat label="Cancelled" value={r.cancelled} />
            <Stat label="Overdue" value={r.overdue} />
          </dl>
          <p className="mt-4 font-mono">Completion rate: {r.completion_rate}%</p>
        </section>
      )}
      {techs.data && (
        <section className="mt-6 rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Technician report</h2>
            <div className="flex gap-2">
              <button onClick={() => exportFile("reports/technicians/", "csv")} className="rounded border px-3 py-1 text-sm">
                CSV
              </button>
              <button onClick={() => exportFile("reports/technicians/", "pdf")} className="rounded border px-3 py-1 text-sm">
                PDF
              </button>
            </div>
          </div>
          <table className="mt-4 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#d8ccb4]">
                <th className="py-2">Technician</th>
                <th>Jobs</th>
                <th>Completed</th>
                <th>Rate</th>
              </tr>
            </thead>
            <tbody>
              {techs.data.rows.map((row) => (
                <tr key={row.technician} className="border-b border-[#eee4d2]">
                  <td className="py-2">{row.technician}</td>
                  <td>{row.jobs}</td>
                  <td>{row.completed}</td>
                  <td>{row.rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-[#7a6a4e]">{label}</div>
      <div className="font-mono text-2xl">{value}</div>
    </div>
  );
}
