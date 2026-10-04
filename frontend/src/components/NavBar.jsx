import { NavLink, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

const linkClass = ({ isActive }) =>
  `text-sm font-semibold px-3 py-1.5 rounded-md transition-colors ${
    isActive ? "text-accent bg-accent-soft" : "text-ink-soft hover:text-ink hover:bg-accent-soft"
  }`;

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="max-w-3xl mx-auto px-6 pt-6 flex items-center justify-between">
      <Link
        to={user ? "/shelf" : "/"}
        className="font-mono text-xs tracking-widest uppercase text-ink-soft hover:text-accent transition-colors"
      >
        Supplement Tracker
      </Link>
      <div className="flex items-center gap-1">
        {user && (
          <NavLink to="/shelf" className={linkClass}>Shelf</NavLink>
        )}
        <NavLink to="/help" className={linkClass}>Help</NavLink>
        <NavLink to="/about" className={linkClass}>About</NavLink>
        {user ? (
          <button
            onClick={handleLogout}
            className="text-sm font-semibold px-3 py-1.5 rounded-md text-ink-soft hover:text-critical hover:bg-accent-soft transition-colors"
          >
            Log out
          </button>
        ) : (
          <NavLink to="/login" className={linkClass}>Log in</NavLink>
        )}
      </div>
    </nav>
  );
}
