const BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response had no JSON body (e.g. 204) — fall back to statusText
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  list: () => request("/supplements"),
  create: (data) =>
    request("/supplements", { method: "POST", body: JSON.stringify(data) }),
  update: (id, data) =>
    request(`/supplements/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  remove: (id) => request(`/supplements/${id}`, { method: "DELETE" }),
  restock: (id, newTotalDoses) => {
    const query = newTotalDoses ? `?new_total_doses=${newTotalDoses}` : "";
    return request(`/supplements/${id}/restock${query}`, { method: "POST" });
  },
};