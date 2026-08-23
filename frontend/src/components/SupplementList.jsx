import SupplementCard from "./SupplementCard";
import "./SupplementList.css";

export default function SupplementList({ supplements, onEdit, onDelete, onRestock, isFiltered = false }) {
  if (supplements.length === 0) {
    return (
      <div className="empty-state">
        <p className="empty-title">{isFiltered ? "No matches." : "Shelf's empty."}</p>
        <p className="empty-body">
          {isFiltered
            ? "Try a different search term or status filter."
            : "Add a supplement to start tracking when you'll run out."}
        </p>
      </div>
    );
  }

  return (
    <div className="supplement-list">
      {supplements.map((s) => (
        <SupplementCard
          key={s.id}
          supplement={s}
          onEdit={() => onEdit(s)}
          onDelete={() => onDelete(s.id)}
          onRestock={() => onRestock(s.id)}
        />
      ))}
    </div>
  );
}