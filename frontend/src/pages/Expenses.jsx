import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import { money } from "../components/ui.jsx";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Expenses() {
  const { isTechnician } = useAuth();
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["expenses"],
    queryFn: async () => (await api.get("/api/expenses/")).data,
  });
  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => (await api.get("/api/jobs/")).data,
  });

  const create = useMutation({
    mutationFn: async (form) => api.post("/api/expenses/", form),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["expenses"] }),
  });

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Expenses</h1>
      {isTechnician && (
        <form
          className="mb-6 grid gap-2 rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-4 md:grid-cols-5"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.target);
            const payload = new FormData();
            payload.append("job", f.get("job"));
            payload.append("amount", f.get("amount"));
            payload.append("category", f.get("category"));
            payload.append("description", f.get("description"));
            if (f.get("receipt")?.size) payload.append("receipt", f.get("receipt"));
            create.mutate(payload);
            e.target.reset();
          }}
        >
          <select name="job" required className="rounded border px-2 py-2">
            <option value="">Job</option>
            {(jobs?.results || []).map((j) => (
              <option key={j.id} value={j.id}>
                #{j.id} {j.title}
              </option>
            ))}
          </select>
          <input name="amount" type="number" step="0.01" placeholder="Amount" className="rounded border px-2 py-2" required />
          <select name="category" className="rounded border px-2 py-2">
            {["TRANSPORT", "FUEL", "MATERIALS", "TOOLS", "OTHER"].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <input name="description" placeholder="Description" className="rounded border px-2 py-2" required />
          <input name="receipt" type="file" className="text-xs" />
          <button className="md:col-span-5 rounded bg-[#1b4d43] py-2 text-white">Record expense</button>
        </form>
      )}
      <div className="overflow-hidden rounded-xl border border-[#d8ccb4] bg-[#fbf8f2]">
        {(data?.results || []).map((e) => (
          <div key={e.id} className="flex justify-between border-b border-[#eadfcb] px-4 py-3">
            <div>
              <div className="font-medium">{e.description}</div>
              <div className="text-sm text-[#5c6f6a]">
                {e.job_title} · {e.category} · {e.submitted_by_name}
              </div>
            </div>
            <div className="font-mono">{money(e.amount)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
