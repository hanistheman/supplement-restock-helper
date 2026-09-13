import SupplementCard from "./SupplementCard";

export default function SupplementList({ supplements, onEdit, onDelete, onRestock, onAddSource, onRemoveSource, isFiltered = false }) {
  if (supplements.length === 0) {
    return (
      <div className="border border-dashed border-line rounded-xl px-6 py-12 text-center bg-paper">
        <p className="font-display text-xl font-semibold mb-1.5">
          {isFiltered ? "No matches." : "Shelf's empty."}
        </p>
        <p className="text-ink-soft text-sm m-0">
          {isFiltered
            ? "Try a different search term or status filter."
            : "Add a supplement to start tracking when you'll run out."}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3.5">
      {supplements.map((s) => (
        <SupplementCard
          key={s.id}
          supplement={s}
          onEdit={() => onEdit(s)}
          onDelete={() => onDelete(s.id)}
          onRestock={() => onRestock(s.id)}
          onAddSource={onAddSource}
          onRemoveSource={onRemoveSource}
        />
      ))}
    </div>
  );
}