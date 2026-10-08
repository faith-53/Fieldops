import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import api from "../api/client";

export default function Notifications() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get("/api/notifications/")).data,
  });
  const mark = useMutation({
    mutationFn: async () => api.post("/api/notifications/mark_all_read/"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Notifications</h1>
        <button onClick={() => mark.mutate()} className="rounded border px-3 py-1 text-sm">
          Mark all read
        </button>
      </div>
      <div className="space-y-3">
        {(data?.results || []).map((n) => (
          <div key={n.id} className={`rounded-xl border p-4 ${n.is_read ? "border-[#d8ccb4] bg-[#fbf8f2]" : "border-[#c45c26] bg-[#f8e6d8]"}`}>
            <div className="font-medium">{n.title}</div>
            <p className="text-sm text-[#5c6f6a]">{n.message}</p>
            {n.job && (
              <Link className="text-sm text-[#1b4d43] underline" to={`/jobs/${n.job}`}>
                Open job
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
