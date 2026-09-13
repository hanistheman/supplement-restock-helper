import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }) =>
  `text-sm font-semibold px-3 py-1.5 rounded-md transition-colors ${
    isActive ? "text-accent bg-accent-soft" : "text-ink-soft hover:text-ink hover:bg-accent-soft"
  }`;

export default function NavBar() {
  return (
    <nav className="max-w-3xl mx-auto px-6 pt-6 flex items-center justify-between">
      <span className="font-mono text-xs tracking-widest uppercase text-ink-soft">
        Supplement Tracker
      </span>
      <div className="flex gap-1">
        <NavLink to="/" end className={linkClass}>Shelf</NavLink>
        <NavLink to="/help" className={linkClass}>Help</NavLink>
        <NavLink to="/about" className={linkClass}>About</NavLink>
      </div>
    </nav>
  );
}
