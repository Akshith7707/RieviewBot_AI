export default function StatsCards({ stats }) {
  const cards = [
    { label: "PRs Reviewed", value: stats.total_jobs, color: "text-blue-400" },
    { label: "Completed", value: stats.completed_jobs, color: "text-emerald-400" },
    { label: "Failed", value: stats.failed_jobs, color: "text-red-400" },
    { label: "Issues Found", value: stats.total_issues, color: "text-amber-400" },
    {
      label: "Helpfulness",
      value: `${stats.helpfulness_percent}%`,
      color: "text-purple-400",
    },
    {
      label: "RL Ready",
      value: stats.rl_training_ready ? "Yes (50+)" : "Need feedback",
      color: stats.rl_training_ready ? "text-emerald-400" : "text-slate-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="bg-slate-900 border border-slate-800 rounded-xl p-4"
        >
          <p className="text-xs text-slate-500 uppercase tracking-wide">{c.label}</p>
          <p className={`text-2xl font-bold mt-1 ${c.color}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}
