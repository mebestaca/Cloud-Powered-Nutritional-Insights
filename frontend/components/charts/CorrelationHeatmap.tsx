"use client";

import { divergingColor } from "@/lib/theme";
import type { InsightsResponse } from "@/lib/api";

// Chart.js has no heatmap, so this is a CSS grid. Each cell shows its value,
// coloured blue (negative) -> grey (0) -> red (positive).
const SHORT: Record<string, string> = {
  Protein: "Prot",
  Carbs: "Carb",
  Fat: "Fat",
  "Protein:Carbs": "P:C",
  "Carbs:Fat": "C:F",
};

export default function CorrelationHeatmap({ data }: { data: InsightsResponse["correlation"] }) {
  const { labels, matrix } = data;
  if (!labels.length) return <p className="text-sm text-gray-500">Not enough data.</p>;

  return (
    <div
      role="table"
      aria-label="Correlation matrix between nutrients"
      className="grid h-full gap-0.5 text-[10px]"
      style={{ gridTemplateColumns: `auto repeat(${labels.length}, minmax(0,1fr))` }}
    >
      <div />
      {labels.map((l) => (
        <div key={l} role="columnheader" title={l} className="text-center font-medium text-gray-500">
          {SHORT[l] ?? l}
        </div>
      ))}
      {matrix.map((row, r) => (
        <div key={labels[r]} role="row" className="contents">
          <div role="rowheader" title={labels[r]} className="flex items-center justify-end pr-1 font-medium text-gray-500">
            {SHORT[labels[r]] ?? labels[r]}
          </div>
          {row.map((v, c) => (
            <div
              key={c}
              role="cell"
              title={`${labels[r]} vs ${labels[c]}: ${v?.toFixed(2) ?? "n/a"}`}
              className="flex items-center justify-center rounded-sm tabular-nums"
              style={{
                background: v == null ? "transparent" : divergingColor(v),
                color: v != null && Math.abs(v) > 0.5 ? "#fff" : "#111827",
              }}
            >
              {v == null ? "–" : v.toFixed(2)}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
