import { useState } from "react";
import api from "../api/axios";

const styles = {
  form: { marginBottom: "24px" },
  textarea: {
    width: "100%",
    padding: "12px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    fontSize: "14px",
    minHeight: "100px",
    resize: "vertical",
    marginBottom: "12px",
    fontFamily: "inherit",
  },
  row: { display: "flex", gap: "12px", alignItems: "center" },
  select: {
    padding: "10px 12px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    fontSize: "14px",
    flex: 1,
  },
  button: {
    padding: "10px 24px",
    background: "#667eea",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
  },
  success: { color: "#27ae60", marginTop: "8px", fontSize: "14px" },
  error: { color: "#e74c3c", marginTop: "8px", fontSize: "14px" },
};

export default function FeedbackForm({ orgId, onSubmitted }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim() || !orgId) return;

    setLoading(true);
    setMessage({ type: "", text: "" });
    try {
      await api.post("/feedback", { text: text.trim(), org_id: orgId });
      setText("");
      setMessage({ type: "success", text: "Feedback submitted! Processing..." });
      onSubmitted?.();
    } catch (err) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Submission failed" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form style={styles.form} onSubmit={handleSubmit}>
      <textarea
        style={styles.textarea}
        placeholder="Enter your feedback..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        required
      />
      <div style={styles.row}>
        <button style={styles.button} type="submit" disabled={loading || !orgId}>
          {loading ? "Submitting..." : "Submit Feedback"}
        </button>
      </div>
      {message.text && (
        <p style={message.type === "success" ? styles.success : styles.error}>
          {message.text}
        </p>
      )}
    </form>
  );
}
