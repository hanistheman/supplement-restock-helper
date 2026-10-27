import { useState } from "react";
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

const UNIT_LABEL = { day: "day", week: "week", month: "month", year: "year" };

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function localToday() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function formatFrequency(doseAmount, frequencyCount, frequencyUnit) {
  const dosePart = doseAmount === 1 ? "1 dose" : `${doseAmount} doses`;
  const unit = UNIT_LABEL[frequencyUnit] ?? frequencyUnit;
  if (frequencyCount === 1) return `${dosePart}, every ${unit}`;
  return `${dosePart}, ${frequencyCount}x per ${unit}`;
}

export default function SupplementCard({ supplement, onEdit, onDelete, onRestock, onAddSource, onRemoveSource, onAddSkippedDay, onRemoveSkippedDay }) {
  const {
    name,
    notes,
    days_remaining,
    restock_date,
    status,
    total_doses,
    dose_amount,
    frequency_count,
    frequency_unit,
    sources,
    skipped_days,
    start_date,
  } = supplement;
  const [skipDate, setSkipDate] = useState("");
  const [skipError, setSkipError] = useState("");

  // The progress bar needs "total days of supply" as a denominator, which
  // isn't returned directly by the API — so it's reconstructed here from
  // the same frequency fields the backend used to compute days_remaining.
  const daysPerUnit = { day: 1, week: 7, month: 30.44, year: 365.25 }[frequency_unit] ?? 1;
  const dosesPerDay = (dose_amount * frequency_count) / daysPerUnit;
  const totalDaysSupply = total_doses / dosesPerDay;
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
        {notes && <p className="text-ink-soft text-[13px] mb-1 mt-0">{notes}</p>}
        <p className="text-ink-soft text-xs mb-3 mt-0">
          {formatFrequency(dose_amount, frequency_count, frequency_unit)}
        </p>

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
        <section className="mt-3 border-t border-line pt-3">
          <p className="text-ink-soft text-xs mb-2 mt-0">Skipped days ({skipped_days?.length ?? 0})</p>
          <form className="flex items-center gap-2 flex-wrap" onSubmit={async (event) => {
            event.preventDefault();
            if (!skipDate) return;
            try {
              setSkipError("");
              await onAddSkippedDay(supplement.id, skipDate);
              setSkipDate("");
            } catch (error) {
              setSkipError(error.message);
            }
          }}>
            <input aria-label={`Skipped date for ${name}`} type="date" min={start_date} max={localToday()} value={skipDate} onChange={(event) => setSkipDate(event.target.value)} className="border border-line rounded-md px-2 py-1 text-xs" />
            <button type="submit" disabled={!skipDate} className="text-accent text-xs font-semibold disabled:opacity-50">Record missed dose</button>
          </form>
          {skipError && <p role="alert" className="text-critical text-xs mb-0 mt-1">{skipError}</p>}
          {!!skipped_days?.length && <ul className="mt-2 mb-0 pl-4 text-xs text-ink-soft space-y-1">
            {skipped_days.map((day) => <li key={day.id}>
              {formatDate(day.date)} <button type="button" aria-label={`Remove skipped day ${formatDate(day.date)}`} onClick={() => onRemoveSkippedDay(supplement.id, day.id)} className="ml-1 text-ink-soft hover:text-critical">×</button>
            </li>)}
          </ul>}
        </section>
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
