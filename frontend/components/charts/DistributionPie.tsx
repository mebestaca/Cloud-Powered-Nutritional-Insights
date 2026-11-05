"use client";

import { Pie } from "react-chartjs-2";
import { dietColor, titleCase, withAlpha } from "@/lib/theme";
import type { InsightsResponse } from "@/lib/api";

// All diets: recipes per diet. One diet selected: that diet's recipes by cuisine,
// in shades of the diet's colour.
export default function DistributionPie({
  data,
  selectedDiet,
}: {
  data: InsightsResponse["distribution"];
  selectedDiet: string;
}) {
  const n = data.items.length;
  const colors =
    data.groupBy === "diet"
      ? data.items.map((i) => dietColor(i.label))
      : data.items.map((_, i) => withAlpha(dietColor(selectedDiet), Math.max(0.25, 1 - i * (0.75 / Math.max(1, n - 1)))));
  const total = data.items.reduce((s, i) => s + i.count, 0);

  return (
    <Pie
      aria-label={`Recipe distribution by ${data.groupBy}`}
      role="img"
      options={{
        plugins: {
          legend: { position: "right" },
          tooltip: {
            callbacks: { label: (c) => ` ${c.parsed} recipes (${((c.parsed / total) * 100).toFixed(1)}%)` },
          },
        },
      }}
      data={{
        labels: data.items.map((i) => titleCase(i.label)),
        datasets: [{ data: data.items.map((i) => i.count), backgroundColor: colors, borderColor: "#fff", borderWidth: 2 }],
      }}
    />
  );
}
