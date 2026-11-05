"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import "@/lib/chartSetup";
import type { ClustersResponse, InsightsResponse, Metadata, RecipesResponse } from "@/lib/api";
import { titleCase } from "@/lib/theme";
import { useEndpoint } from "@/lib/useEndpoint";

// Charts draw on <canvas>, so they only render in the browser.
const MacroBarChart = dynamic(() => import("./charts/MacroBarChart"), { ssr: false });
const ProteinCarbScatter = dynamic(() => import("./charts/ProteinCarbScatter"), { ssr: false });
const CorrelationHeatmap = dynamic(() => import("./charts/CorrelationHeatmap"), { ssr: false });
const DistributionPie = dynamic(() => import("./charts/DistributionPie"), { ssr: false });

const DEFAULT_DIETS = ["dash", "keto", "mediterranean", "paleo", "vegan"];

function ChartCard({ title, text, children }: { title: string; text: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-lg">
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm text-gray-600">{text}</p>
      <div className="relative mt-2 h-48 w-full">{children}</div>
    </div>
  );
}

// "Show metadata such as function execution time"
function RunInfo({ endpoint, meta, roundTripMs }: { endpoint: string; meta?: Metadata; roundTripMs?: number }) {
  if (!meta) return null;
  const src = meta.dataSource;
  return (
    <p className="text-sm text-gray-600">
      <span className="font-mono">/{endpoint}</span> · function execution time{" "}
      <strong className="text-gray-900">{meta.executionTimeMs} ms</strong> (round trip {roundTripMs} ms) ·{" "}
      {meta.filteredRecords.toLocaleString()} of {meta.totalRecords.toLocaleString()} records ·{" "}
      {meta.cacheHit ? "cached data" : "loaded from Blob Storage"} · source{" "}
      <span className="font-mono">{src.type === "azure-blob" ? `${src.account}/${src.container}/${src.blob}` : src.path}</span> ·{" "}
      {new Date(meta.generatedAt).toLocaleTimeString()}
    </p>
  );
}

export default function Dashboard() {
  const [diet, setDiet] = useState("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [view, setView] = useState<"recipes" | "clusters">("recipes");

  const insights = useEndpoint<InsightsResponse>("insights");
  const recipes = useEndpoint<RecipesResponse>("recipes");
  const clusters = useEndpoint<ClustersResponse>("clusters");
  const { load: loadInsights } = insights;
  const { load: loadRecipes } = recipes;
  const { load: loadClusters } = clusters;

  // Wait until the user stops typing before calling the API.
  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 400);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    loadInsights({ diet, search });
  }, [diet, search, loadInsights]);

  useEffect(() => {
    loadRecipes({ diet, search, page, pageSize: 10 });
  }, [diet, search, page, loadRecipes]);

  const I = insights.data;
  const diets = I?.filters.availableDiets ?? DEFAULT_DIETS;
  const totalPages = recipes.data?.totalPages ?? 1;
  const error = insights.error || (view === "recipes" ? recipes.error : clusters.error);

  const chartBody = (node: React.ReactNode) =>
    !I ? (
      <div className="h-full animate-pulse rounded bg-gray-100" />
    ) : I.summary.recipes === 0 ? (
      <p className="pt-16 text-center text-sm text-gray-500">No recipes match.</p>
    ) : (
      node
    );

  // Page buttons: 1 2 3 … last (around the current page)
  const pageButtons: (number | "…")[] = [];
  for (let p = 1; p <= totalPages; p++) {
    if (p === 1 || p === totalPages || Math.abs(p - page) <= 1) pageButtons.push(p);
    else if (pageButtons[pageButtons.length - 1] !== "…") pageButtons.push("…");
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-100">
      <header className="bg-blue-600 p-4 text-white">
        <h1 className="text-3xl font-semibold">Nutritional Insights</h1>
      </header>

      <main className="container mx-auto flex-1 p-6">
        {error && (
          <div role="alert" className="mb-6 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
            {error}
          </div>
        )}

        <section className="mb-8">
          <h2 className="mb-4 text-2xl font-semibold">Explore Nutritional Insights</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <ChartCard title="Bar Chart" text="Average macronutrient content by diet type.">
              {chartBody(I && <MacroBarChart data={I.averageMacros} />)}
            </ChartCard>
            <ChartCard title="Scatter Plot" text="Nutrient relationships (protein vs carbs).">
              {chartBody(I && <ProteinCarbScatter data={I.scatter} />)}
            </ChartCard>
            <ChartCard title="Heatmap" text="Nutrient correlations.">
              {chartBody(I && <CorrelationHeatmap data={I.correlation} />)}
            </ChartCard>
            <ChartCard
              title="Pie Chart"
              text={I?.distribution.groupBy === "cuisine" ? `${titleCase(diet)} recipes by cuisine.` : "Recipe distribution by diet type."}
            >
              {chartBody(I && <DistributionPie data={I.distribution} selectedDiet={diet} />)}
            </ChartCard>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="mb-4 text-2xl font-semibold">Filters and Data Interaction</h2>
          <div className="flex flex-wrap gap-4">
            <input
              type="text"
              placeholder="Search by Diet Type"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full rounded border bg-white p-2 sm:w-auto"
            />
            <select
              value={diet}
              onChange={(e) => {
                setDiet(e.target.value);
                setPage(1);
              }}
              className="w-full rounded border bg-white p-2 sm:w-auto"
            >
              <option value="all">All Diet Types</option>
              {diets.map((d) => (
                <option key={d} value={d}>
                  {titleCase(d)}
                </option>
              ))}
            </select>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="mb-4 text-2xl font-semibold">API Data Interaction</h2>
          <div className="flex flex-wrap gap-4">
            <button
              className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-60"
              disabled={insights.loading}
              onClick={() => loadInsights({ diet, search, refresh: true })}
            >
              {insights.loading ? "Loading…" : "Get Nutritional Insights"}
            </button>
            <button
              className="rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-60"
              disabled={recipes.loading}
              onClick={() => {
                setView("recipes");
                loadRecipes({ diet, search, page, pageSize: 10 });
              }}
            >
              {recipes.loading ? "Loading…" : "Get Recipes"}
            </button>
            <button
              className="rounded bg-purple-600 px-4 py-2 text-white hover:bg-purple-700 disabled:opacity-60"
              disabled={clusters.loading}
              onClick={() => {
                setView("clusters");
                loadClusters({ diet, search, k: 3 });
              }}
            >
              {clusters.loading ? "Loading…" : "Get Clusters"}
            </button>
          </div>

          <div className="mt-4 space-y-1">
            <RunInfo endpoint="insights" meta={I?.metadata} roundTripMs={insights.roundTripMs} />
            {view === "recipes" ? (
              <RunInfo endpoint="recipes" meta={recipes.data?.metadata} roundTripMs={recipes.roundTripMs} />
            ) : (
              <RunInfo endpoint="clusters" meta={clusters.data?.metadata} roundTripMs={clusters.roundTripMs} />
            )}
          </div>

          <div className="mt-4 overflow-x-auto rounded-lg bg-white p-4 shadow-lg">
            {view === "recipes" && recipes.data && (
              <table className="w-full text-left text-sm">
                <thead className="text-gray-600">
                  <tr>
                    <th className="p-2">Recipe</th>
                    <th className="p-2">Diet</th>
                    <th className="p-2">Cuisine</th>
                    <th className="p-2 text-right">Protein (g)</th>
                    <th className="p-2 text-right">Carbs (g)</th>
                    <th className="p-2 text-right">Fat (g)</th>
                  </tr>
                </thead>
                <tbody>
                  {recipes.data.items.map((r, i) => (
                    <tr key={i} className="border-t">
                      <td className="p-2">{r.recipe}</td>
                      <td className="p-2">{titleCase(r.diet)}</td>
                      <td className="p-2">{titleCase(r.cuisine)}</td>
                      <td className="p-2 text-right">{r.protein?.toFixed(1)}</td>
                      <td className="p-2 text-right">{r.carbs?.toFixed(1)}</td>
                      <td className="p-2 text-right">{r.fat?.toFixed(1)}</td>
                    </tr>
                  ))}
                  {!recipes.data.items.length && (
                    <tr>
                      <td colSpan={6} className="p-4 text-center text-gray-500">
                        No recipes match.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
            {view === "clusters" && clusters.data && (
              <ul className="space-y-2 text-sm">
                {clusters.data.clusters.map((c) => (
                  <li key={c.id}>
                    <strong>{c.name}</strong> — {c.size} recipes · avg {Math.round(c.centroid.protein ?? 0)} g protein,{" "}
                    {Math.round(c.centroid.carbs ?? 0)} g carbs, {Math.round(c.centroid.fat ?? 0)} g fat · mostly{" "}
                    {c.dietMix.slice(0, 2).map((d) => titleCase(d.diet)).join(" and ")}
                  </li>
                ))}
                {!clusters.data.clusters.length && <li className="text-gray-500">{clusters.data.note ?? "No recipes match."}</li>}
              </ul>
            )}
            {((view === "recipes" && !recipes.data) || (view === "clusters" && !clusters.data)) && (
              <p className="text-sm text-gray-500">Loading…</p>
            )}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-2xl font-semibold">Pagination</h2>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <button
              className="rounded bg-gray-300 px-3 py-1 hover:bg-gray-400 disabled:opacity-50"
              disabled={page <= 1 || view !== "recipes"}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </button>
            {pageButtons.map((p, i) =>
              p === "…" ? (
                <span key={`gap${i}`} className="px-1 py-1">
                  …
                </span>
              ) : (
                <button
                  key={p}
                  aria-current={p === page ? "page" : undefined}
                  disabled={view !== "recipes"}
                  onClick={() => setPage(p)}
                  className={`rounded px-3 py-1 disabled:opacity-50 ${
                    p === page ? "bg-blue-600 text-white" : "bg-gray-300 hover:bg-gray-400"
                  }`}
                >
                  {p}
                </button>
              ),
            )}
            <button
              className="rounded bg-gray-300 px-3 py-1 hover:bg-gray-400 disabled:opacity-50"
              disabled={page >= totalPages || view !== "recipes"}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </section>
      </main>

      <footer className="mt-10 bg-blue-600 p-4 text-center text-white">
        <p>&copy; {new Date().getFullYear()} Nutritional Insights. All Rights Reserved.</p>
      </footer>
    </div>
  );
}
