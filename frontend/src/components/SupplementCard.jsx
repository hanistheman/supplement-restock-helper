import SourceList from "./SourceList";

const STATUS_LABEL = {
  ok: "On hand",
  low: "Running low",
  critical: "Critical",
  overdue: "Overdue",
};

// Tailwind needs full class strings at build time (no dynamic string
// concatenation), so status-based styling is looked up from these maps
// rather than built with template literals.
const BORDER_BY_STATUS = {
  ok: "border-l-ok",
  low: "border-l-low",
  critical: "border-l-critical",
  overdue: "border-l-overdue",
};

const BADGE_BY_STATUS = {
  ok: "bg-accent-soft text-ok",
  low: "bg-[#fbead1] text-low",
  critical: "bg-[#fbe1d9] text-critical",
  overdue: "bg-[#f6d9d9] text-overdue",
};

const FILL_BY_STATUS = {
  ok: "bg-ok",
  low: "bg-low",
  critical: "bg-critical",
  overdue: "bg-critical",
};

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function SupplementCard({ supplement, onEdit, onDelete, onRestock, onAddSource, onRemoveSource }) {
  const { name, notes, days_remaining, restock_date, status, total_doses, doses_per_day, sources } = supplement;

  const totalDaysSupply = total_doses / doses_per_day;
  // Clamp so an overdue supplement still shows a spent-down bar rather than a negative one.
  const fillPct = Math.max(0, Math.min(1, days_remaining / totalDaysSupply)) * 100;

  return (
    <article className={`bg-paper rounded-xl border border-line border-l-4 ${BORDER_BY_STATUS[status]} px-5.5 py-5 flex justify-between items-center gap-5 flex-wrap`}>
      <div className="flex-1 min-w-[220px]">
        <div className="flex items-center gap-2.5 mb-1">
          <h2 className="font-display text-[19px] font-semibold m-0">{name}</h2>
          <span className={`font-mono text-[11px] tracking-wider uppercase px-2 py-0.5 rounded-full ${BADGE_BY_STATUS[status]}`}>
            {STATUS_LABEL[status]}
          </span>
        </div>
        {notes && <p className="text-ink-soft text-[13px] mb-3 mt-0">{notes}</p>}

        <div
          className="h-2.5 rounded-full bg-accent-soft overflow-hidden my-3 max-w-80"
          role="img"
          aria-label={`${Math.max(days_remaining, 0)} days of supply remaining`}
        >
          <div
            className={`h-full rounded-full transition-[width] duration-[400ms] ${FILL_BY_STATUS[status]}`}
            style={{ width: `${fillPct}%` }}
          />
        </div>

        <div className="font-mono text-[13px] text-ink-soft flex items-center gap-2">
          <span className="font-semibold text-ink">
            {days_remaining >= 0 ? days_remaining : Math.abs(days_remaining)}
            <span className="font-medium text-ink-soft">
              {days_remaining >= 0 ? " days left" : " days overdue"}
            </span>
          </span>
          <span className="text-line">·</span>
          <span>Restock by {formatDate(restock_date)}</span>
        </div>

        <SourceList
          sources={sources ?? []}
          onAdd={(source) => onAddSource(supplement.id, source)}
          onRemove={onRemoveSource}
        />
      </div>

      <div className="flex flex-col items-end gap-2">
        <button
          className="bg-accent text-white font-semibold text-sm rounded-lg px-4.5 py-2.5 hover:shadow-lg hover:shadow-accent/25 active:translate-y-px transition"
          onClick={onRestock}
        >
          Restocked today
        </button>
        <div className="flex gap-1">
          <button className="text-ink-soft text-[13px] px-2 py-1.5 hover:text-critical transition-colors" onClick={onEdit}>
            Edit
          </button>
          <button className="text-ink-soft text-[13px] px-2 py-1.5 hover:text-critical transition-colors" onClick={onDelete}>
            Delete
          </button>
        </div>
      </div>
    </article>
  );
}