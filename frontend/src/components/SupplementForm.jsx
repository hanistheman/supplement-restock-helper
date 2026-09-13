import { useState } from "react";

const emptyForm = {
  name: "",
  start_date: new Date().toISOString().slice(0, 10),
  total_doses: "",
  doses_per_day: "1",
  notes: "",
};

const labelClass = "flex flex-col gap-1.5 text-[13px] font-semibold text-ink-soft";
const inputClass =
  "font-body text-sm font-normal text-ink border border-line rounded-lg px-2.5 py-2 bg-bg focus:outline-none focus:border-accent";

export default function SupplementForm({ title, initial, onSubmit, onClose }) {
  const isEditing = Boolean(initial);
  const [values, setValues] = useState(
    initial
      ? {
          name: initial.name,
          start_date: initial.start_date,
          total_doses: String(initial.total_doses),
          doses_per_day: String(initial.doses_per_day),
          notes: initial.notes ?? "",
        }
      : emptyForm
  );
  // Sources are only collected here on create. On edit, they're managed
  // directly on the card via dedicated add/remove endpoints, since a
  // supplement's sources are their own sub-resource, not part of this form.
  const [sources, setSources] = useState([{ name: "", url: "" }]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (field) => (e) =>
    setValues((v) => ({ ...v, [field]: e.target.value }));

  const handleSourceChange = (index, field) => (e) => {
    const next = [...sources];
    next[index] = { ...next[index], [field]: e.target.value };
    setSources(next);
  };

  const addSourceRow = () => setSources((s) => [...s, { name: "", url: "" }]);
  const removeSourceRow = (index) => setSources((s) => s.filter((_, i) => i !== index));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload = {
        name: values.name.trim(),
        start_date: values.start_date,
        total_doses: Number(values.total_doses),
        doses_per_day: Number(values.doses_per_day),
        notes: values.notes.trim() || null,
      };
      if (!isEditing) {
        payload.sources = sources
          .filter((s) => s.name.trim())
          .map((s) => ({ name: s.name.trim(), url: s.url.trim() || null }));
      }
      await onSubmit(payload);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-ink/45 flex items-center justify-center p-5 z-10"
      onClick={onClose}
    >
      <div
        className="bg-paper rounded-2xl p-7 w-full max-w-[420px] shadow-2xl shadow-ink/25"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="font-display text-xl mb-4.5 mt-0">{title}</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          <label className={labelClass}>
            Name
            <input
              type="text"
              required
              value={values.name}
              onChange={handleChange("name")}
              placeholder="Vitamin D3"
              className={inputClass}
            />
          </label>

          <div className="grid grid-cols-2 gap-3.5">
            <label className={labelClass}>
              Bottle started
              <input
                type="date"
                required
                value={values.start_date}
                onChange={handleChange("start_date")}
                className={inputClass}
              />
            </label>
            <label className={labelClass}>
              Doses per day
              <input
                type="number"
                required
                min="0.25"
                step="0.25"
                value={values.doses_per_day}
                onChange={handleChange("doses_per_day")}
                className={inputClass}
              />
            </label>
          </div>

          <label className={labelClass}>
            Total doses in bottle
            <input
              type="number"
              required
              min="1"
              value={values.total_doses}
              onChange={handleChange("total_doses")}
              placeholder="90"
              className={inputClass}
            />
          </label>

          <label className={labelClass}>
            Notes (optional)
            <input
              type="text"
              value={values.notes}
              onChange={handleChange("notes")}
              placeholder="5000 IU, from Costco"
              className={inputClass}
            />
          </label>

          {!isEditing && (
            <div className="border-t border-line pt-3.5">
              <p className="text-[13px] font-semibold text-ink-soft mb-2 mt-0">
                Where to restock (optional)
              </p>
              {sources.map((source, i) => (
                <div key={i} className="grid grid-cols-[1fr_1fr_auto] gap-2 mb-2 items-center">
                  <input
                    type="text"
                    placeholder="Store name (e.g. Costco)"
                    value={source.name}
                    onChange={handleSourceChange(i, "name")}
                    className={`${inputClass} text-[13px] px-2.5 py-2`}
                  />
                  <input
                    type="url"
                    placeholder="Link (optional)"
                    value={source.url}
                    onChange={handleSourceChange(i, "url")}
                    className={`${inputClass} text-[13px] px-2.5 py-2`}
                  />
                  {sources.length > 1 && (
                    <button
                      type="button"
                      className="bg-transparent border-none text-ink-soft hover:text-critical text-lg leading-none cursor-pointer px-1.5"
                      onClick={() => removeSourceRow(i)}
                      aria-label="Remove source"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                className="text-ink-soft text-[13px] py-1 hover:text-accent transition-colors"
                onClick={addSourceRow}
              >
                + Add another source
              </button>
            </div>
          )}

          {error && <p className="text-critical text-[13px] m-0">{error}</p>}

          <div className="flex justify-end gap-2.5 mt-1.5">
            <button
              type="button"
              className="bg-paper text-ink border border-line rounded-lg px-4.5 py-2.5 font-semibold text-sm hover:border-accent transition-colors"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-accent text-white font-semibold text-sm rounded-lg px-4.5 py-2.5 hover:shadow-lg hover:shadow-accent/25 active:translate-y-px transition disabled:opacity-60"
              disabled={submitting}
            >
              {submitting ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}