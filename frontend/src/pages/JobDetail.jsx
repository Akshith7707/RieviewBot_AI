import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { fetchJob, submitFeedback } from "../api";

const SEV = {
  critical: "border-red-500 bg-red-500/10",
  high: "border-orange-500 bg-orange-500/10",
  medium: "border-amber-500 bg-amber-500/10",
  low: "border-blue-500 bg-blue-500/10",
  info: "border-slate-500 bg-slate-500/10",
};

export default function JobDetail() {
  const { jobId } = useParams();
  const [search] = useSearchParams();
  const highlightIssue = search.get("issue");

  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(null);
  const [user, setUser] = useState("");

  const load = async () => {
    try {
      setData(await fetchJob(jobId));
      setError("");
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [jobId]);

  const rate = async (issueId, rating) => {
    setSubmitting(issueId + rating);
    try {
      await submitFeedback({
        job_id: jobId,
        issue_id: issueId,
        rating,
        user: user || "dashboard-user",
      });
      await load();
    } catch (e) {
      alert(e.message);
    } finally {
      setSubmitting(null);
    }
  };

  if (error) {
    return (
      <div className="text-red-400">
        {error}{" "}
        <Link to="/" className="underline">
          Back
        </Link>
      </div>
    );
  }

  if (!data) return <p className="text-slate-500">Loading job…</p>;

  const { job, issues, feedback } = data;
  const feedbackByIssue = {};
  for (const f of feedback) {
    feedbackByIssue[f.issue_id] = feedbackByIssue[f.issue_id] || [];
    feedbackByIssue[f.issue_id].push(f);
  }

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-slate-500 hover:text-white">
        ← Back to dashboard
      </Link>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-wrap justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold">
              {job.owner}/{job.repo} PR #{job.pr_number}
            </h1>
            <p className="text-slate-400 mt-1">{job.title}</p>
          </div>
          <div className="text-right text-sm">
            <p>
              Status:{" "}
              <span className="font-medium text-emerald-400">{job.status}</span>
            </p>
            <p className="text-slate-500 font-mono text-xs mt-1">{job.id}</p>
          </div>
        </div>
        {job.error_message && (
          <p className="mt-4 text-red-400 text-sm bg-red-900/20 p-3 rounded">
            {job.error_message}
          </p>
        )}
        {job.review_summary && (
          <div className="mt-4 p-4 bg-slate-950 rounded-lg text-sm whitespace-pre-wrap border border-slate-800 max-h-48 overflow-y-auto">
            {job.review_summary.slice(0, 1200)}
            {job.review_summary.length > 1200 && "…"}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm text-slate-500">Your name (for RL):</label>
        <input
          className="bg-slate-900 border border-slate-700 rounded px-3 py-1 text-sm"
          placeholder="github-username"
          value={user}
          onChange={(e) => setUser(e.target.value)}
        />
      </div>

      <h2 className="font-semibold">
        Findings ({issues.length}) — rate to train ReviewBot
      </h2>

      <div className="space-y-4">
        {issues.map((issue) => (
          <div
            key={issue.id}
            id={`issue-${issue.id}`}
            className={`border rounded-xl p-4 ${SEV[issue.severity] || SEV.info} ${
              String(issue.id) === highlightIssue ? "ring-2 ring-emerald-500" : ""
            }`}
          >
            <div className="flex flex-wrap justify-between gap-2">
              <div>
                <span className="text-xs uppercase text-slate-500">{issue.source}</span>
                <h3 className="font-semibold mt-1">{issue.title}</h3>
                <p className="text-sm text-slate-400 mt-1">
                  {issue.file_path}:{issue.line_number} · {issue.category}
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">
                {Math.round(issue.confidence * 100)}% conf
              </span>
            </div>
            <p className="mt-3 text-sm">{issue.description}</p>
            {issue.suggestion && (
              <pre className="mt-2 p-3 bg-slate-950 rounded text-xs overflow-x-auto">
                {issue.suggestion}
              </pre>
            )}
            <div className="mt-4 flex gap-2 items-center">
              <button
                disabled={submitting}
                onClick={() => rate(issue.id, "helpful")}
                className="px-3 py-1.5 bg-emerald-600/80 hover:bg-emerald-600 rounded-lg text-sm"
              >
                👍 Helpful
              </button>
              <button
                disabled={submitting}
                onClick={() => rate(issue.id, "not_helpful")}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm"
              >
                👎 Not helpful
              </button>
              {feedbackByIssue[issue.id]?.length > 0 && (
                <span className="text-xs text-slate-500 ml-2">
                  {feedbackByIssue[issue.id].length} feedback
                </span>
              )}
            </div>
          </div>
        ))}
        {issues.length === 0 && (
          <p className="text-slate-500">No issues stored for this job.</p>
        )}
      </div>
    </div>
  );
}
