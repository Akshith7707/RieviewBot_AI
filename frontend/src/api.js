const API = import.meta.env.VITE_API_URL || "";

export async function fetchStats() {
  const r = await fetch(`${API}/api/stats`);
  if (!r.ok) throw new Error("Failed to load stats");
  return r.json();
}

export async function fetchJobs(limit = 30) {
  const r = await fetch(`${API}/api/reviews?limit=${limit}`);
  if (!r.ok) throw new Error("Failed to load jobs");
  return r.json();
}

export async function fetchJob(jobId) {
  const r = await fetch(`${API}/api/reviews/${jobId}`);
  if (!r.ok) throw new Error("Job not found");
  return r.json();
}

export async function fetchFeedback(jobId = null) {
  const q = jobId ? `?job_id=${jobId}` : "";
  const r = await fetch(`${API}/api/feedback${q}`);
  if (!r.ok) throw new Error("Failed to load feedback");
  return r.json();
}

export async function submitFeedback({ job_id, issue_id, rating, user = "", comment = "" }) {
  const r = await fetch(`${API}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id, issue_id, rating, user, comment }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Feedback failed");
  }
  return r.json();
}

export async function fetchHealth() {
  const r = await fetch(`${API}/health`);
  return r.json();
}
