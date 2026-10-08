import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";

export default function Customers() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["customers"],
    queryFn: async () => (await api.get("/api/customers/")).data,
  });
  const create = useMutation({
    mutationFn: async (payload) => api.post("/api/customers/", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["customers"] }),
  });

  return (
    <div className="grid gap-6 md:grid-cols-[1fr_320px]">
      <div>
        <h1 className="mb-4 text-2xl font-semibold">Customers</h1>
        <div className="overflow-hidden rounded-xl border border-[#d8ccb4] bg-[#fbf8f2]">
          {(data?.results || []).map((c) => (
            <div key={c.id} className="border-b border-[#eadfcb] px-4 py-3">
              <div className="font-medium">{c.name}</div>
              <div className="text-sm text-[#5c6f6a]">
                {c.phone} · {c.address}
              </div>
            </div>
          ))}
        </div>
      </div>
      <form
        className="rounded-xl border border-[#d8ccb4] bg-[#fbf8f2] p-4"
        onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.target);
          create.mutate({
            name: f.get("name"),
            phone: f.get("phone"),
            email: f.get("email"),
            address: f.get("address"),
            latitude: f.get("latitude") || null,
            longitude: f.get("longitude") || null,
          });
          e.target.reset();
        }}
      >
        <h2 className="font-semibold">Add customer</h2>
        <input name="name" required placeholder="Name" className="mt-3 w-full rounded border px-3 py-2" />
        <input name="phone" required placeholder="Phone" className="mt-2 w-full rounded border px-3 py-2" />
        <input name="email" placeholder="Email" className="mt-2 w-full rounded border px-3 py-2" />
        <input name="address" required placeholder="Address" className="mt-2 w-full rounded border px-3 py-2" />
        <div className="mt-2 grid grid-cols-2 gap-2">
          <input name="latitude" placeholder="Lat" className="rounded border px-3 py-2" />
          <input name="longitude" placeholder="Lng" className="rounded border px-3 py-2" />
        </div>
        <button className="mt-3 w-full rounded bg-[#1b4d43] py-2 text-white">Save</button>
      </form>
    </div>
  );
}
