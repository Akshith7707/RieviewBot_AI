import { Link, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import JobDetail from "./pages/JobDetail";
import FeedbackLog from "./pages/FeedbackLog";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🤖</span>
            <span className="font-bold text-lg">ReviewBot AI</span>
            <span className="text-xs bg-emerald-600/30 text-emerald-400 px-2 py-0.5 rounded">
              Dashboard
            </span>
          </Link>
          <nav className="flex gap-4 text-sm text-slate-400">
            <Link to="/" className="hover:text-white">
              Overview
            </Link>
            <Link to="/feedback" className="hover:text-white">
              RL Feedback
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white"
            >
              API Docs
            </a>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs/:jobId" element={<JobDetail />} />
          <Route path="/feedback" element={<FeedbackLog />} />
        </Routes>
      </main>
    </div>
  );
}
