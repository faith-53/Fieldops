import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/client";
import { Badge, PRIORITY, STATUS } from "../components/ui.jsx";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Jobs() {
  const { isManager } = useAuth();
  const [status, setStatus] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["jobs", status],
    queryFn: async () => (await api.get("/api/jobs/", { params: status ? { status } : {} })).data,
  });

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{isManager ? "Jobs" : "My Jobs"}</h1>
        {isManager && <CreateJobButton />}
      </div>
      <div className="mb-4 flex flex-wrap gap-2">
        {["", "PENDING", "ASSIGNED", "ACCEPTED", "IN_PROGRESS", "COMPLETED"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setStatus(s)}
            className={`rounded-full px-3 py-1 text-sm ${status === s ? "bg-[#1b4d43] text-white" : "bg-white border border-[#d8ccb4]"}`}
          >
            {s || "All"}
          </button>
        ))}
      </div>
      {isLoading ? (
        <p>Loading jobs…</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {(data?.results || []).map((job) => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-lg font-semibold">{job.title}</h2>
                <Badge map={PRIORITY} value={job.priority} />
              </div>
              <p className="mt-2 text-sm text-[#5c6f6a]">Customer: {job.customer_name}</p>
              <p className="text-sm text-[#5c6f6a]">Due: {job.scheduled_date || "Unscheduled"} {job.is_overdue ? "· Overdue" : ""}</p>
              <div className="mt-3">
                <Badge map={STATUS} value={job.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateJobButton() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const { data: customers } = useQuery({
    queryKey: ["customers"],
    queryFn: async () => (await api.get("/api/customers/")).data,
    enabled: open,
  });
  const { data: skills } = useQuery({
    queryKey: ["skills"],
    queryFn: async () => (await api.get("/api/auth/skills/")).data,
    enabled: open,
  });
  const create = useMutation({
    mutationFn: async (payload) => (await api.post("/api/jobs/", payload)).data,
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      setOpen(false);
      navigate(`/jobs/${job.id}`);
    },
  });

  return (
    <>
      <button onClick={() => setOpen(true)} className="rounded bg-[#c45c26] px-4 py-2 text-white">
        New job
      </button>
      {open && (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4">
          <form
            className="w-full max-w-lg rounded-xl bg-white p-6"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.target);
              create.mutate({
                title: f.get("title"),
                description: f.get("description"),
                customer: Number(f.get("customer")),
                priority: f.get("priority"),
                scheduled_date: f.get("scheduled_date") || null,
                required_skill: f.get("required_skill") ? Number(f.get("required_skill")) : null,
                estimated_cost: f.get("estimated_cost") || 0,
                location: f.get("location"),
              });
            }}
          >
            <h2 className="text-lg font-semibold">Create service job</h2>
            <input name="title" required placeholder="Title" className="mt-4 w-full rounded border px-3 py-2" />
            <textarea name="description" placeholder="Description" className="mt-2 w-full rounded border px-3 py-2" />
            <select name="customer" required className="mt-2 w-full rounded border px-3 py-2">
              <option value="">Customer</option>
              {(customers?.results || []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <input name="location" placeholder="Location / area" className="mt-2 w-full rounded border px-3 py-2" />
            <div className="mt-2 grid grid-cols-2 gap-2">
              <select name="priority" defaultValue="MEDIUM" className="rounded border px-3 py-2">
                {["LOW", "MEDIUM", "HIGH", "URGENT"].map((p) => (
                  <option key={p}>{p}</option>
                ))}
              </select>
              <input type="date" name="scheduled_date" className="rounded border px-3 py-2" />
            </div>
            <select name="required_skill" className="mt-2 w-full rounded border px-3 py-2">
              <option value="">Required skill</option>
              {(skills?.results || []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <input name="estimated_cost" type="number" placeholder="Estimated cost (KES)" className="mt-2 w-full rounded border px-3 py-2" />
            {create.error && <p className="mt-2 text-sm text-red-700">Could not create job.</p>}
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={() => setOpen(false)} className="px-3 py-2">
                Cancel
              </button>
              <button className="rounded bg-[#1b4d43] px-4 py-2 text-white">Create</button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
