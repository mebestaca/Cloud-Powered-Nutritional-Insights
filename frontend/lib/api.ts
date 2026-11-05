// Client for the Azure Function API. Everything runs in the browser.

export const API_BASE_URL: string = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "development" ? "http://localhost:7071/api" : "")
).replace(/\/+$/, "");

export type DataSource = {
  type: "azure-blob" | "local-file";
  account?: string;
  container?: string;
  blob?: string;
  path?: string;
  sizeBytes?: number;
  lastModified?: string | null;
};

export type Metadata = {
  executionTimeMs: number;
  dataLoadMs: number;
  computeMs: number;
  cacheHit: boolean;
  generatedAt: string;
  datasetLoadedAt: string;
  totalRecords: number;
  filteredRecords: number;
  cleaning: {
    rowsIn: number;
    rowsOut: number;
    rowsWithoutDietDropped: number;
    missingValuesFilled: number;
    duplicatesRemoved: number;
  };
  dataSource: DataSource;
  apiVersion: string;
};

export type Filters = { diet: string; search: string; availableDiets: string[] };

type Envelope = { metadata: Metadata; filters: Filters };

export type Macro = { protein: number | null; carbs: number | null; fat: number | null };

export type InsightsResponse = Envelope & {
  averageMacros: ({ diet: string } & Macro)[];
  distribution: { groupBy: "diet" | "cuisine"; items: { label: string; count: number }[] };
  scatter: ({ recipe: string; diet: string; cuisine: string } & Macro)[];
  correlation: { labels: string[]; matrix: (number | null)[][] };
  topCuisines: { diet: string; cuisine: string; count: number }[];
  topProteinRecipes: { diet: string; recipe: string; cuisine: string; protein: number }[];
  highestProteinDiet: { diet: string; avgProtein: number } | null;
  summary: {
    recipes: number;
    diets: number;
    cuisines: number;
    avgProtein?: number;
    avgCarbs?: number;
    avgFat?: number;
  };
};

export type Recipe = { recipe: string; diet: string; cuisine: string } & Macro;

export type RecipesResponse = Envelope & {
  items: Recipe[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  sort: string;
  order: "asc" | "desc";
};

export type ClustersResponse = Envelope & {
  k: number;
  clusters: {
    id: number;
    name: string;
    size: number;
    centroid: Macro;
    dietMix: { diet: string; count: number }[];
  }[];
  points: ({ recipe: string; diet: string; cluster: number } & Macro)[];
  note?: string;
};

export type Timed<T> = { data: T; roundTripMs: number };

export class ApiError extends Error {}

export async function getJson<T>(
  path: string,
  params: Record<string, string | number | boolean | undefined>,
  signal?: AbortSignal,
): Promise<Timed<T>> {
  if (!API_BASE_URL) {
    throw new ApiError(
      "NEXT_PUBLIC_API_BASE_URL is not set. Add it to your build environment (see docs/DEPLOYMENT_GUIDE.md).",
    );
  }
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "" && v !== false) qs.set(k, String(v));
  }
  const url = `${API_BASE_URL}/${path}${qs.size ? `?${qs}` : ""}`;
  const started = performance.now();
  let res: Response;
  try {
    res = await fetch(url, { signal, cache: "no-store" });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError(
      `Could not reach the API at ${API_BASE_URL}. Check the URL, that the Function App is running, and that CORS allows this site.`,
    );
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(body?.error ? `API error: ${body.error}` : `API returned HTTP ${res.status}`);
  }
  return { data: body as T, roundTripMs: Math.round(performance.now() - started) };
}
