import { NavLink } from "react-router-dom";
import "./NavBar.css";

export default function NavBar() {
  return (
    <nav className="nav-bar">
      <span className="nav-brand">Supplement Tracker</span>
      <div className="nav-links">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
          Shelf
        </NavLink>
        <NavLink to="/help" className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
          Help
        </NavLink>
        <NavLink to="/about" className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
          About
        </NavLink>
      </div>
    </nav>
  );
}
