"use client";

import { useState } from "react";
import useSWR from "swr";

import { Chip } from "@/components/core/Chip";
import { TextField } from "@/components/forms/TextField";
import { SearchResult } from "@/components/recipe/SearchResult";
import { useDebounced } from "@/lib/hooks";
import { usePrefs } from "@/lib/prefs";
import type { RecipeList } from "@/lib/types";

type Filter = "all" | "not_made" | "made";

export function RecipesScreen() {
  const { t } = usePrefs();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const query = useDebounced(q.trim(), 150);
  const { data } = useSWR<RecipeList>(`/api/recipes?filter=${filter}&q=${encodeURIComponent(query)}`);

  const counts = data?.counts;
  const filters: { value: Filter; label: string; count?: number }[] = [
    { value: "all", label: t.filterAll },
    { value: "not_made", label: t.filterNotMade, count: counts?.not_made },
    { value: "made", label: t.filterMade },
  ];

  return (
    <main className="screen">
      <div className="screen__head">
        <div>
          <h1 className="display">{t.recipesTitle}</h1>
          <p className="subtitle">{counts ? t.total(counts.all) : " "}</p>
        </div>
      </div>

      <TextField
        id="recipes-search"
        label={t.recipesSearch}
        hideLabel
        icon="search"
        type="search"
        autoComplete="off"
        placeholder={t.recipesSearch}
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />

      <div className="chip-row" style={{ marginTop: 14 }} role="group" aria-label={t.recipesTitle}>
        {filters.map((f) => (
          <Chip key={f.value} selected={filter === f.value} count={f.count} onClick={() => setFilter(f.value)}>
            {f.label}
          </Chip>
        ))}
      </div>

      <section style={{ marginTop: 8 }}>
        {data && data.recipes.length === 0 && (
          <p className="empty">{counts?.all ? t.recipesNoMatch : t.recipesEmpty}</p>
        )}
        <ul className="list">
          {data?.recipes.map((r) => (
            <SearchResult key={r.id} recipe={r} t={t} matchedIndex={query ? r.matched_index : null} showNote />
          ))}
        </ul>
      </section>
    </main>
  );
}
