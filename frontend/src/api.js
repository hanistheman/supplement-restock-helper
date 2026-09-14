const BASE_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "supplement_tracker_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response had no JSON body (e.g. 204) — fall back to statusText
    }
    // A 401 here means the token is missing/expired/invalid — clear it so
    // the app falls back to the logged-out state instead of retrying with
    // a token that will never work.
    if (res.status === 401) clearToken();
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const auth = {
  register: (email, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: async (email, password) => {
    // The backend's /auth/login endpoint is an OAuth2 "password flow"
    // endpoint (FastAPI's standard pattern), which expects form-encoded
    // fields named username/password rather than JSON.
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    const res = await fetch(`${BASE_URL}/auth/login`, { method: "POST", body });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Login failed");
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  },
  me: () => request("/auth/me"),
  logout: () => clearToken(),
};

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
  addSource: (supplementId, source) =>
    request(`/supplements/${supplementId}/sources`, {
      method: "POST",
      body: JSON.stringify(source),
    }),
  removeSource: (sourceId) => request(`/sources/${sourceId}`, { method: "DELETE" }),
};