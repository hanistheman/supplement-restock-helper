import { useState } from "react";
import "./SourceList.css";

export default function SourceList({ sources, onAdd, onRemove }) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleAdd = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onAdd({ name: name.trim(), url: url.trim() || null });
      setName("");
      setUrl("");
      setAdding(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="source-list">
      {sources.length > 0 && (
        <div className="source-chips">
          {sources.map((s) => (
            <span className="source-chip" key={s.id}>
              {s.url ? (
                <a href={s.url} target="_blank" rel="noopener noreferrer">
                  {s.name} ↗
                </a>
              ) : (
                <span>{s.name}</span>
              )}
              <button
                type="button"
                className="chip-remove"
                onClick={() => onRemove(s.id)}
                aria-label={`Remove ${s.name}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {adding ? (
        <form className="source-add-form" onSubmit={handleAdd}>
          <input
            type="text"
            placeholder="Store name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
          <input
            type="url"
            placeholder="Link (optional)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button type="submit" className="btn-text" disabled={submitting}>
            {submitting ? "Adding…" : "Add"}
          </button>
          <button type="button" className="btn-text" onClick={() => setAdding(false)}>
            Cancel
          </button>
        </form>
      ) : (
        <button type="button" className="btn-text source-add-trigger" onClick={() => setAdding(true)}>
          + Add restock source
        </button>
      )}
      {error && <p className="source-error">{error}</p>}
    </div>
  );
}