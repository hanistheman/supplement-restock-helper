import { useState } from "react";
import "./SupplementForm.css";

const emptyForm = {
  name: "",
  start_date: new Date().toISOString().slice(0, 10),
  total_doses: "",
  doses_per_day: "1",
  notes: "",
};

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
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        <form onSubmit={handleSubmit}>
          <label>
            Name
            <input
              type="text"
              required
              value={values.name}
              onChange={handleChange("name")}
              placeholder="Vitamin D3"
            />
          </label>

          <div className="form-row">
            <label>
              Bottle started
              <input
                type="date"
                required
                value={values.start_date}
                onChange={handleChange("start_date")}
              />
            </label>
            <label>
              Doses per day
              <input
                type="number"
                required
                min="0.25"
                step="0.25"
                value={values.doses_per_day}
                onChange={handleChange("doses_per_day")}
              />
            </label>
          </div>

          <label>
            Total doses in bottle
            <input
              type="number"
              required
              min="1"
              value={values.total_doses}
              onChange={handleChange("total_doses")}
              placeholder="90"
            />
          </label>

          <label>
            Notes (optional)
            <input
              type="text"
              value={values.notes}
              onChange={handleChange("notes")}
              placeholder="5000 IU, from Costco"
            />
          </label>

          {!isEditing && (
            <div className="source-section">
              <p className="source-label">Where to restock (optional)</p>
              {sources.map((source, i) => (
                <div className="source-row" key={i}>
                  <input
                    type="text"
                    placeholder="Store name (e.g. Costco)"
                    value={source.name}
                    onChange={handleSourceChange(i, "name")}
                  />
                  <input
                    type="url"
                    placeholder="Link (optional)"
                    value={source.url}
                    onChange={handleSourceChange(i, "url")}
                  />
                  {sources.length > 1 && (
                    <button
                      type="button"
                      className="source-remove"
                      onClick={() => removeSourceRow(i)}
                      aria-label="Remove source"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button type="button" className="btn-text source-add" onClick={addSourceRow}>
                + Add another source
              </button>
            </div>
          )}

          {error && <p className="form-error">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}