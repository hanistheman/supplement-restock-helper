import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-sm mx-auto px-6 pt-20">
      <p className="font-mono text-xs tracking-widest uppercase text-accent mb-1.5">Welcome back</p>
      <h1 className="font-display text-2xl font-semibold mb-6 mt-0">Log in</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <label className="flex flex-col gap-1.5 text-[13px] font-semibold text-ink-soft">
          Email
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="font-body text-sm font-normal text-ink border border-line rounded-lg px-2.5 py-2 bg-paper focus:outline-none focus:border-accent"
          />
        </label>

        <label className="flex flex-col gap-1.5 text-[13px] font-semibold text-ink-soft">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="font-body text-sm font-normal text-ink border border-line rounded-lg px-2.5 py-2 bg-paper focus:outline-none focus:border-accent"
          />
        </label>

        {error && <p className="text-critical text-[13px] m-0">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="bg-accent text-white font-semibold text-sm rounded-lg px-4.5 py-2.5 hover:shadow-lg hover:shadow-accent/25 active:translate-y-px transition disabled:opacity-60 mt-1"
        >
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="text-sm text-ink-soft mt-5">
        Don't have an account?{" "}
        <Link to="/register" className="text-accent font-semibold hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}