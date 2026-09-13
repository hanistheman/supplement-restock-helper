const SORT_OPTIONS = [
  { value: "days_remaining", label: "Days remaining" },
  { value: "name", label: "Name (A–Z)" },
  { value: "restock_date", label: "Restock date" },
];

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: "overdue", label: "Overdue" },
  { value: "critical", label: "Critical" },
  { value: "low", label: "Running low" },
  { value: "ok", label: "On hand" },
];

const selectClass =
  "font-body text-sm font-medium border border-line rounded-lg px-2.5 py-2.5 bg-paper text-ink focus:outline-none focus:border-accent";

export default function ShelfControls({ search, onSearchChange, sortBy, onSortChange, statusFilter, onStatusChange }) {
  return (
    <div className="flex gap-2.5 mb-5 flex-wrap">
      <input
        type="text"
        className="flex-1 min-w-45 font-body text-sm border border-line rounded-lg px-3 py-2.5 bg-paper text-ink focus:outline-none focus:border-accent"
        placeholder="Search supplements…"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
      />

      <select className={selectClass} value={statusFilter} onChange={(e) => onStatusChange(e.target.value)}>
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>

      <select className={selectClass} value={sortBy} onChange={(e) => onSortChange(e.target.value)}>
        {SORT_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>Sort: {opt.label}</option>
        ))}
      </select>
    </div>
  );
}
