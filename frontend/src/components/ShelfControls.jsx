import "./ShelfControls.css";

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

export default function ShelfControls({ search, onSearchChange, sortBy, onSortChange, statusFilter, onStatusChange }) {
  return (
    <div className="shelf-controls">
      <input
        type="text"
        className="search-input"
        placeholder="Search supplements…"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
      />

      <select value={statusFilter} onChange={(e) => onStatusChange(e.target.value)}>
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>

      <select value={sortBy} onChange={(e) => onSortChange(e.target.value)}>
        {SORT_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>Sort: {opt.label}</option>
        ))}
      </select>
    </div>
  );
}
