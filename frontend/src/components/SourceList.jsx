import { useState } from "react";

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
    <div className="mt-2.5">
      {sources.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {sources.map((s) => (
            <span
              key={s.id}
              className="inline-flex items-center gap-1 bg-accent-soft text-accent rounded-full pl-2.5 pr-1.5 py-1 text-xs font-semibold"
            >
              {s.url ? (
                <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-accent no-underline hover:underline">
                  {s.name} ↗
                </a>
              ) : (
                <span>{s.name}</span>
              )}
              <button
                type="button"
                className="bg-transparent border-none text-accent opacity-60 hover:opacity-100 text-sm leading-none cursor-pointer px-0.5"
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
        <form className="flex gap-1.5 flex-wrap items-center" onSubmit={handleAdd}>
          <input
            type="text"
            placeholder="Store name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
            className="text-xs px-2 py-1.5 border border-line rounded-md bg-bg text-ink min-w-[120px] focus:outline-none focus:border-accent"
          />
          <input
            type="url"
            placeholder="Link (optional)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="text-xs px-2 py-1.5 border border-line rounded-md bg-bg text-ink min-w-[120px] focus:outline-none focus:border-accent"
          />
          <button type="submit" className="text-ink-soft text-[13px] px-1 hover:text-accent" disabled={submitting}>
            {submitting ? "Adding…" : "Add"}
          </button>
          <button type="button" className="text-ink-soft text-[13px] px-1 hover:text-critical" onClick={() => setAdding(false)}>
            Cancel
          </button>
        </form>
      ) : (
        <button
          type="button"
          className="text-ink-soft text-xs py-0.5 hover:text-accent transition-colors"
          onClick={() => setAdding(true)}
        >
          + Add restock source
        </button>
      )}
      {error && <p className="text-critical text-xs mt-1.5 mb-0">{error}</p>}
    </div>
  );
}