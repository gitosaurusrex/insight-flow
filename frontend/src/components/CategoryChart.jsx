import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

const COLORS = ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b", "#fa709a", "#fee140"];

export default function CategoryChart({ data }) {
  if (!data || data.length === 0) {
    return <p style={{ color: "#999", textAlign: "center", padding: "40px" }}>No category data yet</p>;
  }

  const chartData = {
    labels: data.map((d) => d.category),
    datasets: [
      {
        data: data.map((d) => d.count),
        backgroundColor: COLORS.slice(0, data.length),
        borderWidth: 2,
        borderColor: "#fff",
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      title: { display: true, text: "Category Breakdown" },
      legend: { position: "bottom" },
    },
  };

  return <Doughnut data={chartData} options={options} />;
}
