"use client";

import { Bar } from "react-chartjs-2";
import { MACRO_COLORS, titleCase } from "@/lib/theme";
import type { InsightsResponse } from "@/lib/api";

export default function MacroBarChart({ data }: { data: InsightsResponse["averageMacros"] }) {
  const mk = (label: string, key: "protein" | "carbs" | "fat") => ({
    label,
    data: data.map((d) => d[key] ?? 0),
    backgroundColor: MACRO_COLORS[key],
    borderRadius: 3,
    maxBarThickness: 14,
  });

  return (
    <Bar
      aria-label="Average protein, carbs and fat by diet type"
      role="img"
      options={{
        interaction: { mode: "index", intersect: false },
        plugins: { tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${c.parsed.y?.toFixed(1)} g` } } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, title: { display: true, text: "grams" } },
        },
      }}
      data={{
        labels: data.map((d) => titleCase(d.diet)),
        datasets: [mk("Protein", "protein"), mk("Carbs", "carbs"), mk("Fat", "fat")],
      }}
    />
  );
}
