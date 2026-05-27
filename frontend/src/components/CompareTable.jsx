const ROWS = [
  {
    feature: "OWASP pre-scan (no API cost)",
    reviewbot: true,
    copilot: false,
  },
  {
    feature: "Learns from 👍/👎 feedback (RL)",
    reviewbot: true,
    copilot: false,
  },
  {
    feature: "Full audit dashboard",
    reviewbot: true,
    copilot: false,
  },
  {
    feature: "Self-hosted / data stays yours",
    reviewbot: true,
    copilot: false,
  },
  {
    feature: "Open model chain (Groq/Ollama)",
    reviewbot: true,
    copilot: false,
  },
  {
    feature: "Inline PR comments",
    reviewbot: true,
    copilot: true,
  },
  {
    feature: "GitHub native UI",
    reviewbot: false,
    copilot: true,
  },
];

export default function CompareTable() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800">
        <h2 className="font-semibold">ReviewBot vs GitHub Copilot Review</h2>
        <p className="text-sm text-slate-500 mt-1">
          Why self-hosted ReviewBot wins for serious teams
        </p>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-500 border-b border-slate-800">
            <th className="text-left p-3">Feature</th>
            <th className="p-3">ReviewBot</th>
            <th className="p-3">Copilot</th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.feature} className="border-b border-slate-800/50">
              <td className="p-3">{row.feature}</td>
              <td className="p-3 text-center">
                {row.reviewbot ? "✅" : "—"}
              </td>
              <td className="p-3 text-center">
                {row.copilot ? "✅" : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
