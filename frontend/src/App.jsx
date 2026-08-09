import { useEffect, useState } from "react";
import { api } from "./api";
import SupplementList from "./components/SupplementList";
import SupplementForm from "./components/SupplementForm";
import "./App.css";

export default function App() {
  const [supplements, setSupplements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const load = async () => {
    try {
      setError(null);
      const data = await api.list();
      // Soonest-to-run-out first, so what needs attention sits at the top.
      data.sort((a, b) => a.days_remaining - b.days_remaining);
      setSupplements(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (values) => {
    await api.create(values);
    setFormOpen(false);
    load();
  };

  const handleUpdate = async (id, values) => {
    await api.update(id, values);
    setEditingId(null);
    load();
  };

  const handleDelete = async (id) => {
    await api.remove(id);
    load();
  };

  const handleRestock = async (id) => {
    await api.restock(id);
    load();
  };

  const editingSupplement = supplements.find((s) => s.id === editingId) ?? null;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Personal stock room</p>
          <h1>Supplement Restock Tracker</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setFormOpen(true)}>
          + Add supplement
        </button>
      </header>

      {loading && <p className="status-text">Loading your shelf…</p>}
      {error && (
        <p className="status-text status-error">
          Couldn't reach the server — is the backend running on port 8000?
        </p>
      )}

      {!loading && !error && (
        <SupplementList
          supplements={supplements}
          onEdit={(s) => setEditingId(s.id)}
          onDelete={handleDelete}
          onRestock={handleRestock}
        />
      )}

      {formOpen && (
        <SupplementForm
          title="Add supplement"
          onSubmit={handleCreate}
          onClose={() => setFormOpen(false)}
        />
      )}

      {editingSupplement && (
        <SupplementForm
          title="Edit supplement"
          initial={editingSupplement}
          onSubmit={(values) => handleUpdate(editingId, values)}
          onClose={() => setEditingId(null)}
        />
      )}
    </div>
  );
}