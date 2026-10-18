import { createContext, useContext, useEffect, useState } from "react";
import { auth, getAccessToken, getRefreshToken } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // Distinguishes "we haven't checked yet" from "checked, and there's no
  // user" — without this, a logged-in user briefly flashes the login page
  // on every page refresh while the /auth/me call is in flight.
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Either token being present is enough to attempt /auth/me: if the
    // access token has already expired by the time the page loads (it's
    // only good for 15 minutes), the request() helper in api.js
    // transparently refreshes it using the refresh token and retries —
    // no special handling needed here.
    if (!getAccessToken() && !getRefreshToken()) {
      setLoading(false);
      return;
    }
    auth
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    await auth.login(email, password);
    const me = await auth.me();
    setUser(me);
    return me;
  };

  const register = async (email, password) => {
    await auth.register(email, password);
    return login(email, password);
  };

  const logout = async () => {
    await auth.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}