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
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (field) => (e) =>
    setValues((v) => ({ ...v, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({
        name: values.name.trim(),
        start_date: values.start_date,
        total_doses: Number(values.total_doses),
        doses_per_day: Number(values.doses_per_day),
        notes: values.notes.trim() || null,
      });
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