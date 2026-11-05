import type { PointStyle } from "chart.js";

// Colours checked for colour-blind separation. A diet keeps its colour
// no matter which filter is active.
const DIET_ORDER = ["dash", "keto", "mediterranean", "paleo", "vegan"];
const DIET_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"];
const DIET_SHAPES: PointStyle[] = ["circle", "triangle", "rect", "rectRot", "star"];

export const MACRO_COLORS = { protein: "#008300", carbs: "#6250d6", fat: "#e34948" };

export function dietColor(diet: string): string {
  const i = DIET_ORDER.indexOf(diet.toLowerCase());
  return i >= 0 ? DIET_COLORS[i] : "#898781";
}

export function dietShape(diet: string): PointStyle {
  const i = DIET_ORDER.indexOf(diet.toLowerCase());
  return i >= 0 ? DIET_SHAPES[i] : "crossRot";
}

export function titleCase(s: string): string {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}

export function withAlpha(hex: string, alpha: number): string {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}

// Heatmap scale: blue (-1) -> grey (0) -> red (+1).
function mix(a: string, b: string, t: number): string {
  const pa = parseInt(a.slice(1), 16);
  const pb = parseInt(b.slice(1), 16);
  const ch = (s: number) => Math.round(((pa >> s) & 255) + (((pb >> s) & 255) - ((pa >> s) & 255)) * t);
  return `rgb(${ch(16)}, ${ch(8)}, ${ch(0)})`;
}

export function divergingColor(v: number): string {
  const t = Math.max(-1, Math.min(1, v));
  return t < 0 ? mix("#f0efec", "#1c5cab", -t) : mix("#f0efec", "#c42f2f", t);
}
