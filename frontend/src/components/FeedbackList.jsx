import { useState } from "react";

const styles = {
  filters: { display: "flex", gap: "12px", marginBottom: "16px", flexWrap: "wrap" },
  select: {
    padding: "8px 12px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    fontSize: "13px",
  },
  list: { listStyle: "none", padding: 0 },
  item: {
    background: "#fff",
    border: "1px solid #eee",
    borderRadius: "8px",
    padding: "16px",
    marginBottom: "8px",
  },
  header: { display: "flex", justifyContent: "space-between", marginBottom: "8px" },
  status: {
    fontSize: "12px",
    padding: "2px 8px",
    borderRadius: "12px",
    fontWeight: "600",
  },
  sentiment: { fontSize: "13px", color: "#666" },
  category: { fontSize: "12px", color: "#764ba2", fontWeight: "600" },
  date: { fontSize: "12px", color: "#999" },
  pagination: { display: "flex", justifyContent: "center", gap: "8px", marginTop: "16px" },
  pageBtn: {
    padding: "6px 16px",
    border: "1px solid #ddd",
    borderRadius: "6px",
    background: "#fff",
    cursor: "pointer",
    fontSize: "13px",
  },
  empty: { color: "#999", textAlign: "center", padding: "40px" },
};

function statusColor(status) {
  if (status === "processed") return { background: "#d4edda", color: "#155724" };
  if (status === "pending") return { background: "#fff3cd", color: "#856404" };
  return { background: "#f0f0f0", color: "#333" };
}

function sentimentLabel(score) {
  if (score === null || score === undefined) return "N/A";
  if (score > 0.3) return `Positive (${score.toFixed(2)})`;
  if (score < -0.3) return `Negative (${score.toFixed(2)})`;
  return `Neutral (${score.toFixed(2)})`;
}

export default function FeedbackList({ items, total, page, pageSize, onPageChange, onFilterChange }) {
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const handleFilterChange = (key, value) => {
    if (key === "status") setStatusFilter(value);
    if (key === "category") setCategoryFilter(value);
    onFilterChange?.({ status: key === "status" ? value : statusFilter, category: key === "category" ? value : categoryFilter });
  };

  const totalPages = Math.ceil((total || 0) / (pageSize || 20));

  return (
    <div>
      <div style={styles.filters}>
        <select style={styles.select} value={statusFilter} onChange={(e) => handleFilterChange("status", e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="processed">Processed</option>
        </select>
        <select style={styles.select} value={categoryFilter} onChange={(e) => handleFilterChange("category", e.target.value)}>
          <option value="">All Categories</option>
          <option value="bug">Bug</option>
          <option value="feature_request">Feature Request</option>
          <option value="praise">Praise</option>
          <option value="complaint">Complaint</option>
          <option value="question">Question</option>
          <option value="general">General</option>
        </select>
      </div>

      {(!items || items.length === 0) ? (
        <p style={styles.empty}>No feedback found</p>
      ) : (
        <ul style={styles.list}>
          {items.map((item) => (
            <li key={item.id} style={styles.item}>
              <div style={styles.header}>
                <span style={{ ...styles.status, ...statusColor(item.status) }}>{item.status}</span>
                <span style={styles.date}>{new Date(item.created_at).toLocaleDateString()}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={styles.sentiment}>{sentimentLabel(item.sentiment_score)}</span>
                {item.category && <span style={styles.category}>{item.category}</span>}
              </div>
            </li>
          ))}
        </ul>
      )}

      {totalPages > 1 && (
        <div style={styles.pagination}>
          <button style={styles.pageBtn} disabled={page <= 1} onClick={() => onPageChange?.(page - 1)}>Prev</button>
          <span style={{ padding: "6px 0", fontSize: "13px" }}>Page {page} of {totalPages}</span>
          <button style={styles.pageBtn} disabled={page >= totalPages} onClick={() => onPageChange?.(page + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
