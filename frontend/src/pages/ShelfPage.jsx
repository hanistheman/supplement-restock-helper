import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import SupplementList from "../components/SupplementList";
import SupplementForm from "../components/SupplementForm";
import ShelfControls from "../components/ShelfControls";

export default function ShelfPage() {
  const [supplements, setSupplements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("days_remaining");
  const [statusFilter, setStatusFilter] = useState("all");

  const load = async () => {
    try {
      setError(null);
      const data = await api.list();
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

  // Derived, filtered/sorted view — kept separate from the raw fetched data
  // so search/sort/filter never need to touch the network.
  const visibleSupplements = useMemo(() => {
    let result = supplements;

    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter((s) => s.name.toLowerCase().includes(q));
    }

    if (statusFilter !== "all") {
      result = result.filter((s) => s.status === statusFilter);
    }

    result = [...result].sort((a, b) => {
      if (sortBy === "name") return a.name.localeCompare(b.name);
      if (sortBy === "restock_date") return a.restock_date.localeCompare(b.restock_date);
      return a.days_remaining - b.days_remaining; // default: most urgent first
    });

    return result;
  }, [supplements, search, statusFilter, sortBy]);

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
        <>
          {supplements.length > 0 && (
            <ShelfControls
              search={search}
              onSearchChange={setSearch}
              sortBy={sortBy}
              onSortChange={setSortBy}
              statusFilter={statusFilter}
              onStatusChange={setStatusFilter}
            />
          )}
          <SupplementList
            supplements={visibleSupplements}
            onEdit={(s) => setEditingId(s.id)}
            onDelete={handleDelete}
            onRestock={handleRestock}
            isFiltered={supplements.length > 0 && visibleSupplements.length === 0}
          />
        </>
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
