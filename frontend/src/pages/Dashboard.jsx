import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import FeedbackForm from "../components/FeedbackForm";
import FeedbackList from "../components/FeedbackList";
import SentimentChart from "../components/SentimentChart";
import CategoryChart from "../components/CategoryChart";

const styles = {
  nav: {
    background: "#fff",
    padding: "12px 24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom: "1px solid #eee",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  },
  logo: { fontSize: "20px", fontWeight: "700", color: "#667eea" },
  logoutBtn: {
    padding: "8px 16px",
    background: "transparent",
    border: "1px solid #ddd",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "13px",
  },
  container: { maxWidth: "1200px", margin: "0 auto", padding: "24px" },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" },
  card: {
    background: "#fff",
    borderRadius: "12px",
    padding: "24px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
  },
  cardTitle: { fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "#1a1a2e" },
  section: { marginBottom: "24px" },
  sectionTitle: { fontSize: "18px", fontWeight: "700", marginBottom: "16px", color: "#1a1a2e" },
  loading: { textAlign: "center", padding: "40px", color: "#999" },
  orgSelect: {
    padding: "8px 12px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    fontSize: "14px",
    marginBottom: "16px",
  },
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [orgs, setOrgs] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState("");
  const [sentimentData, setSentimentData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [feedbackData, setFeedbackData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ status: "", category: "" });
  const [loading, setLoading] = useState(true);

  // Fetch user's organizations
  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const res = await api.get("/organizations");
        setOrgs(res.data);
        if (res.data.length > 0) {
          setSelectedOrg(res.data[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch orgs", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrgs();
  }, []);

  const fetchAnalytics = useCallback(async () => {
    if (!selectedOrg) return;
    try {
      const [sentRes, catRes] = await Promise.all([
        api.get("/analytics/sentiment-trends", { params: { org_id: selectedOrg } }),
        api.get("/analytics/category-breakdown", { params: { org_id: selectedOrg } }),
      ]);
      setSentimentData(sentRes.data.trends);
      setCategoryData(catRes.data.categories);
    } catch (err) {
      console.error("Failed to fetch analytics", err);
    }
  }, [selectedOrg]);

  const fetchFeedback = useCallback(async () => {
    if (!selectedOrg) return;
    try {
      const params = { org_id: selectedOrg, page, page_size: 20 };
      if (filters.status) params.status = filters.status;
      if (filters.category) params.category = filters.category;
      const res = await api.get("/feedback", { params });
      setFeedbackData(res.data);
    } catch (err) {
      console.error("Failed to fetch feedback", err);
    }
  }, [selectedOrg, page, filters]);

  useEffect(() => {
    fetchAnalytics();
    fetchFeedback();
  }, [fetchAnalytics, fetchFeedback]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleSubmitted = () => {
    setTimeout(() => {
      fetchFeedback();
      fetchAnalytics();
    }, 1000);
  };

  return (
    <div>
      <nav style={styles.nav}>
        <span style={styles.logo}>InsightFlow</span>
        <button style={styles.logoutBtn} onClick={handleLogout}>Logout</button>
      </nav>

      <div style={styles.container}>
        {orgs.length > 1 && (
          <div style={styles.section}>
            <label style={{ fontSize: "14px", fontWeight: "600", marginRight: "8px" }}>
              Organization:
            </label>
            <select
              style={styles.orgSelect}
              value={selectedOrg}
              onChange={(e) => setSelectedOrg(e.target.value)}
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>
        )}

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Submit Feedback</h2>
          <div style={styles.card}>
            <FeedbackForm orgId={selectedOrg} onSubmitted={handleSubmitted} />
          </div>
        </div>

        <div style={styles.grid}>
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Sentiment Trends</h3>
            <SentimentChart data={sentimentData} />
          </div>
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Category Breakdown</h3>
            <CategoryChart data={categoryData} />
          </div>
        </div>

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Feedback</h2>
          <div style={styles.card}>
            <FeedbackList
              items={feedbackData.items}
              total={feedbackData.total}
              page={page}
              pageSize={20}
              onPageChange={setPage}
              onFilterChange={setFilters}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
