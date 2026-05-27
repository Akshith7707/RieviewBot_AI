import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchFeedback, fetchStats } from "../api";

export default function FeedbackLog() {
  const [feedback, setFeedback] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    Promise.all([fetchFeedback(), fetchStats()]).then(([f, s]) => {
      setFeedback(f.feedback || []);
      setStats(s);
    });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">RL Feedback Log</h1>
        <p className="text-slate-500 mt-1">
          Every 👍/👎 trains future reviews. Need 50+ samples before full RL fine-tune.
        </p>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500">Total feedback</p>
            <p className="text-2xl font-bold">{stats.feedback_total}</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500">Helpful</p>
            <p className="text-2xl font-bold text-emerald-400">
              {stats.feedback_helpful}
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500">RL training ready</p>
            <p className="text-2xl font-bold">
              {stats.rl_training_ready ? "✅" : "⏳"}
            </p>
          </div>
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
        {feedback.length === 0 && (
          <p className="p-6 text-slate-500 text-sm">
            No feedback yet. Open a job and rate findings.
          </p>
        )}
        {feedback.map((f) => (
          <div key={f.id} className="p-4 flex justify-between gap-4">
            <div>
              <p className="font-medium">
                {f.rating === "helpful" ? "👍" : "👎"}{" "}
                Issue #{f.issue_id}
              </p>
              <p className="text-sm text-slate-500">
                by {f.user || "anonymous"} ·{" "}
                {new Date(f.created_at).toLocaleString()}
              </p>
            </div>
            <Link
              to={`/jobs/${f.job_id}?issue=${f.issue_id}`}
              className="text-sm text-emerald-400 hover:underline shrink-0"
            >
              View job →
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
