import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import api from "../api/client";
import { Badge, PRIORITY, STATUS, money } from "../components/ui.jsx";
import { useAuth } from "../auth/AuthContext.jsx";

export default function JobDetail() {
  const { id } = useParams();
  const { isManager, isTechnician, user } = useAuth();
  const qc = useQueryClient();
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  const { data: job, isLoading } = useQuery({
    queryKey: ["job", id],
    queryFn: async () => (await api.get(`/api/jobs/${id}/`)).data,
  });
  const { data: suggestions } = useQuery({
    queryKey: ["suggestions", id],
    queryFn: async () => (await api.get(`/api/jobs/${id}/suggestions/`)).data,
    enabled: Boolean(isManager && job && ["PENDING", "ASSIGNED", "ACCEPTED"].includes(job.status)),
  });

  const run = useMutation({
    mutationFn: async ({ path, payload }) => (await api.post(`/api/jobs/${id}/${path}/`, payload)).data,
    onSuccess: () => {
      setError("");
      qc.invalidateQueries({ queryKey: ["job", id] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (err) => setError(err.response?.data?.detail || JSON.stringify(err.response?.data) || "Action failed"),
  });

  if (isLoading || !job) return <p>Loading job…</p>;
  const mine = job.assigned_to === user?.id;

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
      <div className="rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-5">
        <div className="font-mono text-xs text-[#7a5b14]">JOB #{job.id}</div>
        <h1 className="mt-1 text-2xl font-semibold">{job.title}</h1>
        <p className="mt-2 text-[#5c6f6a]">Customer: {job.customer_detail?.name}</p>
        <p className="text-[#5c6f6a]">{job.location || job.customer_detail?.address}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge map={PRIORITY} value={job.priority} />
          <Badge map={STATUS} value={job.status} />
        </div>
        <p className="mt-4">{job.description}</p>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-[#7a6a4e]">Due</dt>
            <dd>{job.scheduled_date || "—"} {job.is_overdue ? "(overdue)" : ""}</dd>
          </div>
          <div>
            <dt className="text-[#7a6a4e]">Technician</dt>
            <dd>{job.assigned_to_detail?.name || "Unassigned"}</dd>
          </div>
          <div>
            <dt className="text-[#7a6a4e]">Estimated</dt>
            <dd>{money(job.estimated_cost)}</dd>
          </div>
          <div>
            <dt className="text-[#7a6a4e]">Materials cost</dt>
            <dd>{money(job.actual_cost)}</dd>
          </div>
        </dl>
        {job.completion_note && (
          <div className="mt-4 rounded border border-[#cfe8c9] bg-[#f3faef] p-3 text-sm">
            <div className="font-semibold">Completion note</div>
            {job.completion_note}
          </div>
        )}

        {error && <p className="mt-4 text-sm text-[#9b1c1c]">{error}</p>}

        <div className="mt-5 flex flex-wrap gap-2">
          {isTechnician && mine && job.status === "ASSIGNED" && (
            <Action onClick={() => run.mutate({ path: "accept", payload: {} })}>Accept job</Action>
          )}
          {isTechnician && mine && job.status === "ACCEPTED" && (
            <Action onClick={() => run.mutate({ path: "start", payload: {} })}>Start job</Action>
          )}
          {isTechnician && mine && job.status === "IN_PROGRESS" && (
            <CompleteBox note={note} setNote={setNote} onSubmit={() => run.mutate({ path: "complete", payload: { note } })} />
          )}
          {isManager && job.status === "COMPLETED" && (
            <>
              <Action onClick={() => run.mutate({ path: "verify", payload: {} })}>Verify</Action>
              <Action
                tone="warn"
                onClick={() =>
                  run.mutate({ path: "reopen", payload: { comment: window.prompt("Why send this back?") || "" } })
                }
              >
                Send back
              </Action>
            </>
          )}
          {isManager && job.status === "VERIFIED" && (
            <Action onClick={() => run.mutate({ path: "close", payload: {} })}>Close job</Action>
          )}
          {isManager && !["CLOSED", "CANCELLED"].includes(job.status) && (
            <Action tone="warn" onClick={() => run.mutate({ path: "cancel", payload: { comment: "Cancelled by manager" } })}>
              Cancel
            </Action>
          )}
        </div>

        <Notes job={job} onAdd={(comment) => run.mutate({ path: "notes", payload: { comment } })} />
        <Uploads job={job} jobId={id} />
        <Materials job={job} jobId={id} canEdit={isTechnician && mine && job.status === "IN_PROGRESS"} />
      </div>

      <aside className="space-y-4">
        {isManager && suggestions && (
          <div className="rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-5">
            <h2 className="font-semibold">Suggested technicians</h2>
            <p className="text-xs text-[#7a6a4e]">
              Score = skill match + availability + workload + distance
            </p>
            <div className="mt-3 space-y-3">
              {suggestions.map((t) => (
                <div key={t.id} className="rounded border border-[#eadfcb] p-3">
                  <div className="flex justify-between">
                    <strong>{t.name}</strong>
                    <span className="font-mono text-xs">score {t.score}</span>
                  </div>
                  <p className="text-sm">{t.skill_match ? "✓ Skill match" : "Missing required skill"}</p>
                  <p className="text-sm">{t.available ? "✓ Available" : "⚠ Busy"} · {t.current_jobs} current jobs</p>
                  <p className="text-sm">Distance: {t.distance_km != null ? `${t.distance_km} km` : "unknown"}</p>
                  <button
                    className="mt-2 rounded bg-[#1b4d43] px-3 py-1 text-sm text-white"
                    onClick={() => run.mutate({ path: "assign", payload: { technician_id: t.id } })}
                  >
                    Assign {t.name.split(" ")[0]}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-5">
          <h2 className="font-semibold">Audit log</h2>
          <ol className="mt-3 space-y-2 text-sm">
            {(job.updates || []).map((u) => (
              <li key={u.id} className="border-b border-[#eee4d2] pb-2">
                <div className="font-medium">
                  {u.old_status || "—"} → {u.new_status}
                </div>
                <div className="text-[#5c6f6a]">
                  {u.user_name} · {new Date(u.created_at).toLocaleString()}
                </div>
                {u.comment && <div>{u.comment}</div>}
              </li>
            ))}
          </ol>
        </div>
      </aside>
    </div>
  );
}

function Action({ children, onClick, tone }) {
  return (
    <button
      onClick={onClick}
      className={`rounded px-4 py-2 text-sm text-white ${tone === "warn" ? "bg-[#8a3b0f]" : "bg-[#1b4d43]"}`}
    >
      {children}
    </button>
  );
}

function CompleteBox({ note, setNote, onSubmit }) {
  return (
    <div className="w-full rounded border border-[#f3d2b5] bg-white p-3">
      <label className="text-sm font-medium">Completion note (required)</label>
      <textarea className="mt-1 w-full rounded border px-3 py-2" value={note} onChange={(e) => setNote(e.target.value)} />
      <button onClick={onSubmit} className="mt-2 rounded bg-[#215c28] px-4 py-2 text-white">
        Complete job
      </button>
    </div>
  );
}

function Notes({ job, onAdd }) {
  const [text, setText] = useState("");
  return (
    <div className="mt-8">
      <h3 className="font-semibold">Notes</h3>
      <div className="mt-2 flex gap-2">
        <input className="flex-1 rounded border px-3 py-2" value={text} onChange={(e) => setText(e.target.value)} />
        <button
          className="rounded border px-3"
          onClick={() => {
            onAdd(text);
            setText("");
          }}
        >
          Add
        </button>
      </div>
    </div>
  );
}

function Uploads({ job, jobId }) {
  const qc = useQueryClient();
  async function upload(kind, file) {
    const form = new FormData();
    form.append("kind", kind);
    form.append("file", file);
    await api.post(`/api/jobs/${jobId}/attachments/`, form);
    qc.invalidateQueries({ queryKey: ["job", jobId] });
  }
  const groups = { BEFORE: [], AFTER: [], RECEIPT: [], DOCUMENT: [] };
  (job.attachments || []).forEach((a) => groups[a.kind]?.push(a));
  return (
    <div className="mt-8">
      <h3 className="font-semibold">Files</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {Object.entries(groups).map(([kind, files]) => (
          <div key={kind} className="rounded border border-[#eadfcb] p-3">
            <div className="text-sm font-medium">{kind}</div>
            {files.map((f) => (
              <a key={f.id} href={f.file} className="mt-1 block truncate text-sm text-[#1b4d43] underline" target="_blank" rel="noreferrer">
                {f.file.split("/").pop()}
              </a>
            ))}
            <input type="file" className="mt-2 text-xs" onChange={(e) => e.target.files[0] && upload(kind, e.target.files[0])} />
          </div>
        ))}
      </div>
    </div>
  );
}

function Materials({ job, jobId, canEdit }) {
  const qc = useQueryClient();
  return (
    <div className="mt-8">
      <h3 className="font-semibold">Materials used</h3>
      <ul className="mt-2 text-sm">
        {(job.materials || []).map((m) => (
          <li key={m.id}>
            {m.name} × {m.quantity} · {money(m.line_total)}
          </li>
        ))}
      </ul>
      {canEdit && (
        <form
          className="mt-3 grid grid-cols-3 gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            const f = new FormData(e.target);
            await api.post(`/api/jobs/${jobId}/materials/`, {
              name: f.get("name"),
              quantity: f.get("quantity"),
              unit_cost: f.get("unit_cost"),
            });
            e.target.reset();
            qc.invalidateQueries({ queryKey: ["job", jobId] });
          }}
        >
          <input name="name" placeholder="Item" className="rounded border px-2 py-1" required />
          <input name="quantity" type="number" step="0.01" placeholder="Qty" className="rounded border px-2 py-1" />
          <input name="unit_cost" type="number" step="0.01" placeholder="Unit cost" className="rounded border px-2 py-1" />
          <button className="col-span-3 rounded bg-[#1b4d43] py-1 text-white">Add material</button>
        </form>
      )}
    </div>
  );
}
