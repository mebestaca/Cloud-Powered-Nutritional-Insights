"use client";

import { useCallback, useRef, useState } from "react";
import { ApiError, getJson, type Metadata } from "./api";

export type EndpointState<T> = {
  data?: T;
  loading: boolean;
  error?: string;
  roundTripMs?: number;
  at?: number;
};

// Calls one API endpoint, cancels any older in-flight request for the same
// endpoint (so fast filter changes never show stale data), and keeps timing.
export function useEndpoint<T extends { metadata: Metadata }>(path: string) {
  const [state, setState] = useState<EndpointState<T>>({ loading: false });
  const ctrl = useRef<AbortController | null>(null);

  const load = useCallback(
    async (params: Record<string, string | number | boolean | undefined>) => {
      ctrl.current?.abort();
      const c = new AbortController();
      ctrl.current = c;
      setState((s) => ({ ...s, loading: true, error: undefined }));
      try {
        const { data, roundTripMs } = await getJson<T>(path, params, c.signal);
        if (c.signal.aborted) return;
        setState({ data, roundTripMs, loading: false, at: Date.now() });
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        setState((s) => ({
          ...s,
          loading: false,
          at: Date.now(),
          error: e instanceof ApiError ? e.message : "Unexpected error talking to the API.",
        }));
      }
    },
    [path],
  );

  return { ...state, load };
}
