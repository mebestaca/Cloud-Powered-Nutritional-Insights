"use client";

import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend);

// Small cards, so keep text and legend compact.
ChartJS.defaults.font.size = 10;
ChartJS.defaults.color = "#4b5563";
ChartJS.defaults.maintainAspectRatio = false;
ChartJS.defaults.plugins.legend.position = "bottom";
ChartJS.defaults.plugins.legend.labels.boxWidth = 6;
ChartJS.defaults.plugins.legend.labels.boxHeight = 6;
ChartJS.defaults.plugins.legend.labels.padding = 6;
ChartJS.defaults.plugins.legend.labels.usePointStyle = true;
ChartJS.defaults.plugins.tooltip.usePointStyle = true;
