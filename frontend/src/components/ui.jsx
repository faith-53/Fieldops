export function money(value) {
  const n = Number(value || 0);
  return `KES ${n.toLocaleString("en-KE", { maximumFractionDigits: 0 })}`;
}

export const PRIORITY = {
  LOW: "border-[#8aa39b] text-[#3d5f58]",
  MEDIUM: "border-[#c4a35a] text-[#7a5b14]",
  HIGH: "border-[#c45c26] text-[#c45c26]",
  URGENT: "border-[#9b1c1c] bg-[#9b1c1c] text-white",
};

export const STATUS = {
  PENDING: "bg-[#eadfcb] text-[#5c4a28]",
  ASSIGNED: "bg-[#d7e4df] text-[#1b4d43]",
  ACCEPTED: "bg-[#cfe0f5] text-[#1e3a5f]",
  IN_PROGRESS: "bg-[#f3d2b5] text-[#8a3b0f]",
  COMPLETED: "bg-[#cfe8c9] text-[#215c28]",
  VERIFIED: "bg-[#b7d4c8] text-[#10231f]",
  CLOSED: "bg-[#d9d4cb] text-[#444]",
  CANCELLED: "bg-[#e8cfcf] text-[#7a1f1f]",
};

export function Badge({ map, value }) {
  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs font-semibold tracking-wide ${map[value] || ""}`}>
      {value?.replaceAll("_", " ")}
    </span>
  );
}
