import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function SentimentChart({ data }) {
  if (!data || data.length === 0) {
    return <p style={{ color: "#999", textAlign: "center", padding: "40px" }}>No sentiment data yet</p>;
  }

  const chartData = {
    labels: data.map((d) => d.date),
    datasets: [
      {
        label: "Avg Sentiment",
        data: data.map((d) => d.avg_sentiment),
        borderColor: "#667eea",
        backgroundColor: "rgba(102, 126, 234, 0.1)",
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      title: { display: true, text: "Sentiment Trends" },
      legend: { display: false },
    },
    scales: {
      y: { min: -1, max: 1, title: { display: true, text: "Sentiment" } },
    },
  };

  return <Line data={chartData} options={options} />;
}
