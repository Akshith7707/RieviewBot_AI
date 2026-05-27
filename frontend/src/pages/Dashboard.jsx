import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchHealth, fetchJobs, fetchStats } from "../api";
import StatsCards from "../components/StatsCards";
import CompareTable from "../components/CompareTable";

const STATUS_COLOR = {
  completed: "text-emerald-400 bg-emerald-400/10",
  failed: "text-red-400 bg-red-400/10",
  running: "text-amber-400 bg-amber-400/10",
  pending: "text-slate-400 bg-slate-400/10",
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      setError("");
      const [s, j, h] = await Promise.all([
        fetchStats(),
        fetchJobs(),
        fetchHealth(),
      ]);
      setStats(s);
      setJobs(j.jobs || []);
      setHealth(h);
    } catch (e) {
      setError(e.message + " — Is backend running on :8000?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, []);

  if (loading) {
    return <p className="text-slate-500">Loading dashboard…</p>;
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-800 rounded-xl p-6">
        <p className="text-red-300 font-medium">Cannot reach backend</p>
        <p className="text-sm text-red-400 mt-2">{error}</p>
        <p className="text-sm text-slate-400 mt-4">
          Run: <code className="bg-slate-800 px-2 py-1 rounded">.\scripts\run_server.ps1</code>
        </p>
        <button
          onClick={load}
          className="mt-4 px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Review Activity</h1>
        <p className="text-slate-500 mt-1">
          Live view of every PR review — security scan + LLM + your feedback loop
        </p>
        {health?.warnings?.length > 0 && (
          <div className="mt-3 text-sm text-amber-400 bg-amber-400/10 border border-amber-800/50 rounded-lg p-3">
            {health.warnings.join(" · ")}
          </div>
        )}
      </div>

      <StatsCards stats={stats} />

      <div className="grid lg:grid-cols-2 gap-6">
        <CompareTable />

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h2 className="font-semibold mb-3">Issues by severity</h2>
          <div className="space-y-2">
            {Object.entries(stats.issues_by_severity || {}).map(([sev, n]) => (
              <div key={sev} className="flex justify-between text-sm">
                <span className="capitalize text-slate-400">{sev}</span>
                <span className="font-mono">{n}</span>
              </div>
            ))}
            {!Object.keys(stats.issues_by_severity || {}).length && (
              <p className="text-slate-500 text-sm">No issues yet — open a test PR</p>
            )}
          </div>
          <h3 className="font-semibold mt-6 mb-2 text-sm text-slate-400">By source</h3>
          {Object.entries(stats.issues_by_source || {}).map(([src, n]) => (
            <div key={src} className="flex justify-between text-sm">
              <span>{src}</span>
              <span className="font-mono">{n}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 flex justify-between">
          <h2 className="font-semibold">Recent reviews</h2>
          <button onClick={load} className="text-xs text-slate-500 hover:text-white">
            Refresh
          </button>
        </div>
        <div className="divide-y divide-slate-800">
          {jobs.length === 0 && (
            <p className="p-6 text-slate-500 text-sm">
              No reviews yet. Trigger via webhook or POST /api/review
            </p>
          )}
          {jobs.map((job) => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="block px-4 py-3 hover:bg-slate-800/50 transition"
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="font-medium">
                    {job.owner}/{job.repo} #{job.pr_number}
                  </p>
                  <p className="text-sm text-slate-500 truncate max-w-md">
                    {job.title || "Untitled PR"}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <span
                    className={`text-xs px-2 py-1 rounded ${STATUS_COLOR[job.status] || STATUS_COLOR.pending}`}
                  >
                    {job.status}
                  </span>
                  <p className="text-xs text-slate-500 mt-1">
                    {job.issues_count} issues
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
