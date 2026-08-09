import "./SupplementCard.css";

const STATUS_LABEL = {
  ok: "On hand",
  low: "Running low",
  critical: "Critical",
  overdue: "Overdue",
};

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function SupplementCard({ supplement, onEdit, onDelete, onRestock }) {
  const { name, notes, days_remaining, restock_date, status, total_doses, doses_per_day } = supplement;

  const totalDaysSupply = total_doses / doses_per_day;
  // Clamp so an overdue supplement still shows a spent-down bar rather than a negative one.
  const fillPct = Math.max(0, Math.min(1, days_remaining / totalDaysSupply)) * 100;

  return (
    <article className={`supp-card status-${status}`}>
      <div className="supp-main">
        <div className="supp-heading">
          <h2>{name}</h2>
          <span className={`badge badge-${status}`}>{STATUS_LABEL[status]}</span>
        </div>
        {notes && <p className="supp-notes">{notes}</p>}

        <div className="capsule-track" role="img" aria-label={`${Math.max(days_remaining, 0)} days of supply remaining`}>
          <div className="capsule-fill" style={{ width: `${fillPct}%` }} />
        </div>

        <div className="supp-meta">
          <span className="days-count">
            {days_remaining >= 0 ? days_remaining : Math.abs(days_remaining)}
            <span className="days-unit">{days_remaining >= 0 ? " days left" : " days overdue"}</span>
          </span>
          <span className="supp-dot">·</span>
          <span>Restock by {formatDate(restock_date)}</span>
        </div>
      </div>

      <div className="supp-actions">
        <button className="btn btn-primary" onClick={onRestock}>
          Restocked today
        </button>
        <div className="supp-actions-row">
          <button className="btn-text" onClick={onEdit}>Edit</button>
          <button className="btn-text" onClick={onDelete}>Delete</button>
        </div>
      </div>
    </article>
  );
}