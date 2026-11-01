"use client";

import { useEffect, useRef, useState } from "react";
import useSWR from "swr";

import { Chip } from "@/components/core/Chip";
import { TextField } from "@/components/forms/TextField";
import { SearchResult } from "@/components/recipe/SearchResult";
import { useDebounced } from "@/lib/hooks";
import { usePrefs } from "@/lib/prefs";
import type { SearchResponse } from "@/lib/types";

export function SearchScreen() {
  const { t } = usePrefs();
  const [q, setQ] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const query = useDebounced(q.trim(), 150);
  const { data } = useSWR<SearchResponse>(query ? `/api/search?q=${encodeURIComponent(query)}` : null);

  useEffect(() => {
    input.current?.focus();
  }, []);

  return (
    <main className="screen">
      <h1 className="visually-hidden">{t.tabSearch}</h1>
      <TextField
        ref={input}
        id="search"
        label={t.searchPlaceholder}
        hideLabel
        icon="search"
        type="search"
        enterKeyHint="search"
        autoComplete="off"
        placeholder={t.searchPlaceholder}
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />

      {!q.trim() && (
        <section className="section">
          <h2 className="overline" style={{ marginBottom: 10 }}>
            {t.tryLabel}
          </h2>
          <div className="chip-row chip-row--wrap">
            {t.tryIngredients.map((ing) => (
              <Chip key={ing} onClick={() => setQ(ing)}>
                {ing}
              </Chip>
            ))}
          </div>
        </section>
      )}

      {query && data && data.query === query && (
        <section className="section" aria-live="polite">
          {data.count > 0 ? (
            <>
              <h2 className="overline">{t.recipesUse(data.count, data.query)}</h2>
              <ul className="list">
                {data.results.map((r) => (
                  <SearchResult key={r.id} recipe={r} t={t} matchedIndex={r.matched_index} />
                ))}
              </ul>
            </>
          ) : (
            <p className="empty">{t.searchNothing(data.query)}</p>
          )}
        </section>
      )}
    </main>
  );
}
