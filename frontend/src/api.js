const BASE_URL = "http://127.0.0.1:8000";
const ACCESS_TOKEN_KEY = "supplement_tracker_access_token";
const REFRESH_TOKEN_KEY = "supplement_tracker_refresh_token";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setTokens({ access_token, refresh_token }) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Shared across concurrent requests: if several requests 401 at the same
// moment, they must not each call /auth/refresh independently — the
// backend rotates (single-uses) refresh tokens, so a second concurrent
// refresh call would be rejected since the first already consumed it.
// Instead every caller awaits this one in-flight promise.
let refreshPromise = null;

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refreshToken = getRefreshToken();
      if (!refreshToken) throw new Error("No refresh token available");

      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        clearTokens();
        throw new Error("Session expired — please log in again");
      }
      const data = await res.json();
      setTokens(data);
      return data.access_token;
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function request(path, options = {}, _isRetry = false) {
  const token = getAccessToken();
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && !_isRetry && getRefreshToken()) {
    // Access token is short-lived (15 min) by design — a 401 here most
    // often just means it expired mid-session, not that the person is
    // truly logged out. Try to transparently refresh and retry once,
    // rather than bouncing them to the login screen for routine expiry.
    try {
      await refreshAccessToken();
      return request(path, options, true);
    } catch {
      clearTokens();
      throw new Error("Session expired — please log in again");
    }
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response had no JSON body (e.g. 204) — fall back to statusText
    }
    if (res.status === 401) clearTokens();
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const auth = {
  register: (email, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: async (email, password) => {
    // Keep the existing form-encoded username/password login contract.
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    const res = await fetch(`${BASE_URL}/auth/login`, { method: "POST", body });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Login failed");
    }
    const data = await res.json();
    setTokens(data);
    return data;
  },
  me: () => request("/auth/me"),
  logout: async () => {
    const refreshToken = getRefreshToken();
    clearTokens();
    if (refreshToken) {
      // Best-effort: revoke server-side so a copied-out refresh token
      // can't keep working after logout. If this fails (e.g. offline),
      // the local tokens are already cleared either way.
      try {
        await fetch(`${BASE_URL}/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // Network error on logout shouldn't block the user from leaving.
      }
    }
  },
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
  addSkippedDay: (supplementId, skippedDate) =>
    request(`/supplements/${supplementId}/skipped-days`, {
      method: "POST",
      body: JSON.stringify({ date: skippedDate }),
    }),
  removeSkippedDay: (supplementId, skippedDayId) =>
    request(`/supplements/${supplementId}/skipped-days/${skippedDayId}`, { method: "DELETE" }),
};
