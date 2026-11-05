"use client";

import { Scatter } from "react-chartjs-2";
import { dietColor, dietShape, titleCase, withAlpha } from "@/lib/theme";
import type { InsightsResponse } from "@/lib/api";

type Pt = { x: number; y: number; recipe: string };

export default function ProteinCarbScatter({ data }: { data: InsightsResponse["scatter"] }) {
  const byDiet = new Map<string, Pt[]>();
  for (const d of data) {
    if (d.protein == null || d.carbs == null) continue;
    byDiet.set(d.diet, [...(byDiet.get(d.diet) ?? []), { x: d.carbs, y: d.protein, recipe: d.recipe }]);
  }

  const datasets = [...byDiet.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([diet, pts]) => {
      const color = dietColor(diet);
      const shape = dietShape(diet);
      return {
        label: titleCase(diet),
        data: pts,
        pointStyle: shape,
        backgroundColor: withAlpha(color, 0.55),
        // "star" is drawn as an outline only, so it needs a coloured border
        borderColor: shape === "star" ? color : "#ffffff",
        borderWidth: 1,
        pointRadius: 3,
        pointHoverRadius: 6,
      };
    });

  return (
    <Scatter
      aria-label="Protein versus carbs per recipe, by diet"
      role="img"
      options={{
        plugins: {
          tooltip: {
            callbacks: {
              title: (items) => (items[0]?.raw as Pt)?.recipe ?? "",
              label: (c) => ` ${c.dataset.label}: ${(c.raw as Pt).y.toFixed(0)} g protein, ${(c.raw as Pt).x.toFixed(0)} g carbs`,
            },
          },
        },
        scales: {
          x: { beginAtZero: true, title: { display: true, text: "Carbs (g)" } },
          y: { beginAtZero: true, title: { display: true, text: "Protein (g)" } },
        },
      }}
      data={{ datasets }}
    />
  );
}
