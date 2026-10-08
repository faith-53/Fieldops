import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Users() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get("/api/auth/users/")).data,
  });
  const { data: skills } = useQuery({
    queryKey: ["skills"],
    queryFn: async () => (await api.get("/api/auth/skills/")).data,
  });
  const create = useMutation({
    mutationFn: async (payload) => api.post("/api/auth/users/", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  const isAdmin = user?.role === "ADMIN";

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Users</h1>
      <div className="overflow-hidden rounded-xl border border-[#d8ccb4] bg-[#fbf8f2]">
        {(data?.results || []).map((u) => (
          <div key={u.id} className="flex justify-between border-b border-[#eadfcb] px-4 py-3">
            <div>
              <div className="font-medium">{u.name}</div>
              <div className="text-sm text-[#5c6f6a]">{u.email}</div>
            </div>
            <div className="text-sm">
              {u.role} {u.is_active ? "" : "· inactive"}
            </div>
          </div>
        ))}
      </div>
      {isAdmin && (
        <form
          className="mt-6 grid gap-2 rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-4 md:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.target);
            create.mutate({
              name: f.get("name"),
              email: f.get("email"),
              role: f.get("role"),
              password: f.get("password"),
              phone: f.get("phone"),
              skill_ids: f.get("skill") ? [Number(f.get("skill"))] : [],
            });
            e.target.reset();
          }}
        >
          <h2 className="md:col-span-2 font-semibold">Create user</h2>
          <input name="name" placeholder="Name" required className="rounded border px-3 py-2" />
          <input name="email" placeholder="Email" required className="rounded border px-3 py-2" />
          <input name="phone" placeholder="Phone" className="rounded border px-3 py-2" />
          <input name="password" placeholder="Password" required className="rounded border px-3 py-2" />
          <select name="role" className="rounded border px-3 py-2">
            <option>TECHNICIAN</option>
            <option>MANAGER</option>
            <option>ADMIN</option>
          </select>
          <select name="skill" className="rounded border px-3 py-2">
            <option value="">Skill</option>
            {(skills?.results || skills || []).map?.((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <button className="md:col-span-2 rounded bg-[#1b4d43] py-2 text-white">Save user</button>
        </form>
      )}
    </div>
  );
}
