import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Session from "./pages/Session";
import Practice from "./pages/Practice";
import AllQA from "./pages/AllQA";
import "./index.css";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/session/:id" element={<Session />} />
        <Route path="/session/:id/practice" element={<Practice />} />
        <Route path="/session/:id/all-qa" element={<AllQA />} />
      </Routes>
    </Router>
  );
}