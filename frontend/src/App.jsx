import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import ShelfPage from "./pages/ShelfPage";
import AboutPage from "./pages/AboutPage";
import HelpPage from "./pages/HelpPage";
import "./App.css";

export default function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<ShelfPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/help" element={<HelpPage />} />
      </Routes>
    </>
  );
}