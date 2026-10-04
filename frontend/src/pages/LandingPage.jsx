import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function LandingPage() {
  const { user, loading } = useAuth();

  // A logged-in visitor landing on "/" should go straight to their shelf —
  // this page is for people who aren't signed in yet.
  if (!loading && user) {
    return <Navigate to="/shelf" replace />;
  }

  return (
    <div className="max-w-2xl mx-auto px-6 pt-20 pb-24 text-center">
      <p className="font-mono text-xs tracking-widest uppercase text-accent mb-3">
        Never run out again
      </p>
      <h1 className="font-display text-4xl font-semibold tracking-tight mb-4">
        Supplement Restock Tracker
      </h1>
      <p className="text-ink-soft text-base leading-relaxed max-w-md mx-auto mb-10">
        Tell it when you opened a supplement and how often you take it — it does
        the math on when you'll run out, so you're never caught reaching for
        an empty shelf.
      </p>

      <div className="flex items-center justify-center gap-3 mb-14 flex-wrap">
        <Link
          to="/register"
          className="bg-accent text-white font-semibold text-sm rounded-lg px-6 py-3 hover:shadow-lg hover:shadow-accent/25 active:translate-y-px transition"
        >
          Sign up
        </Link>
        <Link
          to="/login"
          className="bg-paper text-ink border border-line font-semibold text-sm rounded-lg px-6 py-3 hover:border-accent transition-colors"
        >
          Log in
        </Link>
      </div>

      <div className="flex items-center justify-center gap-6 text-sm">
        <Link to="/help" className="text-ink-soft font-semibold hover:text-accent transition-colors">
          Help
        </Link>
        <span className="text-line">·</span>
        <Link to="/about" className="text-ink-soft font-semibold hover:text-accent transition-colors">
          About
        </Link>
      </div>
    </div>
  );
}