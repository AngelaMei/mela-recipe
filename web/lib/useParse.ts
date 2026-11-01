"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api";
import type { ParseResult, ParsedStep, SplitOptions } from "./types";

export const DEFAULT_SPLIT: SplitOptions = { line: true, comma: true, number: true, period: false };

/**
 * Live, debounced parse preview from the API (the single source of parsing rules).
 * Steps are kept locally so "Merge ↑" edits survive until the input changes.
 */
export function useParse(input: string, caption: string, split: SplitOptions, delay = 300) {
  const [result, setResult] = useState<ParseResult | null>(null);
  const [steps, setSteps] = useState<ParsedStep[]>([]);
  const [loading, setLoading] = useState(false);
  const keyRef = useRef("");
  const seq = useRef(0);

  const key = JSON.stringify([input.trim(), caption.trim(), split]);

  const run = useCallback(async (): Promise<ParseResult | null> => {
    const k = JSON.stringify([input.trim(), caption.trim(), split]);
    if (!input.trim()) {
      setResult(null);
      setSteps([]);
      keyRef.current = k;
      return null;
    }
    const id = ++seq.current;
    setLoading(true);
    try {
      const r = await api.post<ParseResult>("/api/parse", { input, caption: caption || null, split });
      if (id === seq.current) {
        setResult(r);
        setSteps(r.steps);
        keyRef.current = k;
      }
      return r;
    } catch {
      return null;
    } finally {
      if (id === seq.current) setLoading(false);
    }
  }, [input, caption, split]);

  useEffect(() => {
    const t = setTimeout(run, delay);
    return () => clearTimeout(t);
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  /** Latest result for the current input; parses now if the preview is stale. */
  const ensure = useCallback(async () => {
    if (keyRef.current === key && result) return { result, steps };
    const r = await run();
    return { result: r, steps: r?.steps ?? [] };
  }, [key, result, steps, run]);

  const merge = useCallback((index: number) => {
    setSteps((prev) => {
      if (index <= 0) return prev;
      const next = [...prev];
      const joined = `${next[index - 1].text}${/[㐀-鿿]$/.test(next[index - 1].text) ? "" : " "}${next[index].text}`;
      next.splice(index - 1, 2, { text: joined, short: joined.length < 8 });
      return next;
    });
  }, []);

  return { result, steps, loading, merge, ensure };
}
