import React, { useState, useRef } from "react";

const REQUEST_TIMEOUT = 15000;

export default function JobFinder() {
  const [keywords, setKeywords] = useState("");
  const [region, setRegion] = useState("");
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const abortRef = useRef(null);

  const fetchJobs = async () => {
    if (!keywords.trim() && !region.trim()) {
      setError("Please enter role keywords or a region.");
      return;
    }

    if (abortRef.current) abortRef.current.abort();

    const controller = new AbortController();
    abortRef.current = controller;

    const timeout = setTimeout(() => {
      controller.abort();
    }, REQUEST_TIMEOUT);

    setLoading(true);
    setError("");
    setJobs([]);
    setHasSearched(true);

    try {
      const response = await fetch("http://localhost:5000/api/jobs/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
        body: JSON.stringify({
          keywords: keywords.trim(),
          region: region.trim(),
        }),
      });

      clearTimeout(timeout);

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Request failed");
      }

      const data = await response.json();

      if (!data || !Array.isArray(data.jobs)) {
        throw new Error("Invalid response format");
      }

      setJobs(data.jobs);
    } catch (err) {
      if (err.name === "AbortError") {
        setError("Request timed out.");
      } else {
        setError(err.message || "Unexpected error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") fetchJobs();
  };

  const getDecisionColor = (decision) => {
    if (decision === "APPLY") return "#22c55e";
    if (decision === "MAYBE") return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Find Jobs</h2>

      <div style={styles.inputs}>
        <input
          type="text"
          placeholder="Role keywords"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          onKeyDown={handleKeyDown}
          style={styles.input}
        />

        <input
          type="text"
          placeholder="Region"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          onKeyDown={handleKeyDown}
          style={styles.input}
        />

        <button
          onClick={fetchJobs}
          disabled={loading}
          style={styles.button}
        >
          {loading ? "Searching…" : "Find Jobs"}
        </button>
      </div>

      {error && <div style={styles.error}>{error}</div>}
      {loading && <div style={styles.loading}>Searching jobs…</div>}

      {!loading && jobs.length > 0 && (
        <div style={styles.results}>
          {jobs.map((job) => (
            <div key={job.id} style={styles.card}>
              
              {/* HEADER */}
              <div style={styles.cardHeader}>
                <div>
                  <div style={styles.jobTitle}>{job.title}</div>
                  <div style={styles.meta}>
                    {job.company} • {job.location}
                  </div>
                </div>

                {/* SCORE */}
                <div style={styles.scoreBox}>
                  <div style={styles.fitScore}>{job.fitScore || 0}%</div>
                  <div style={styles.fitLabel}>Fit</div>
                </div>
              </div>

              {/* DECISION */}
              <div
                style={{
                  ...styles.decisionBadge,
                  backgroundColor: getDecisionColor(job.decision),
                }}
              >
                {job.decision || "UNKNOWN"}
              </div>

              {/* CONFIDENCE */}
              <div style={styles.confidence}>
                Confidence: {job.confidence || 0}%
              </div>

              {/* EXPLANATION */}
              {job.explanation && (
                <div style={styles.explanation}>
                  <div>
                    ✔ Matches: {job.explanation.matched_keywords.join(", ")}
                  </div>
                  <div>
                    ❌ Missing: {job.explanation.missing_keywords.join(", ")}
                  </div>
                </div>
              )}

              {/* LINK */}
              <a href={job.url} target="_blank" rel="noreferrer" style={styles.link}>
                View job →
              </a>
            </div>
          ))}
        </div>
      )}

      {!loading && hasSearched && jobs.length === 0 && (
        <div style={styles.empty}>No jobs found</div>
      )}
    </div>
  );
}

/* ---------------- STYLES ---------------- */

const styles = {
  container: {
    maxWidth: 800,
    margin: "0 auto",
    padding: 20,
    color: "#fff",
    fontFamily: "sans-serif",
  },
  title: { fontSize: 22, marginBottom: 16 },
  inputs: { display: "flex", flexDirection: "column", gap: 10 },
  input: {
    padding: 10,
    background: "#1f1f1f",
    border: "1px solid #444",
    borderRadius: 6,
    color: "#fff",
  },
  button: {
    padding: 12,
    background: "#2563eb",
    border: "none",
    borderRadius: 6,
    color: "#fff",
    fontWeight: 600,
  },
  error: { color: "#ef4444" },
  loading: { color: "#aaa" },
  results: { marginTop: 20, display: "flex", flexDirection: "column", gap: 12 },
  card: {
    background: "#111",
    border: "1px solid #333",
    padding: 14,
    borderRadius: 8,
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
  },
  jobTitle: { fontSize: 16, fontWeight: 600 },
  meta: { fontSize: 12, color: "#aaa" },
  scoreBox: { textAlign: "right" },
  fitScore: { color: "#22c55e", fontWeight: 700 },
  fitLabel: { fontSize: 10, color: "#888" },
  decisionBadge: {
    marginTop: 10,
    padding: "4px 8px",
    borderRadius: 4,
    fontSize: 12,
    fontWeight: 600,
    width: "fit-content",
  },
  confidence: { marginTop: 6, fontSize: 12, color: "#ccc" },
  explanation: { marginTop: 8, fontSize: 12, color: "#bbb" },
  link: { display: "block", marginTop: 10, color: "#3b82f6" },
  empty: { marginTop: 20, color: "#aaa" },
};