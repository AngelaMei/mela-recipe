"use client";

import useSWR from "swr";

import { Icon } from "@/components/core/Icon";
import { IconButton } from "@/components/core/IconButton";
import { RecipeTile } from "@/components/recipe/RecipeTile";
import { useRouter } from "next/navigation";
import { useMe, usePrefs } from "@/lib/prefs";
import type { RecipeList } from "@/lib/types";

export function HomeScreen() {
  const { t, lang } = usePrefs();
  const router = useRouter();
  const { data: me } = useMe();
  // Every recipe, most recently cooked first; ones not made yet come last (the API sorts them).
  const { data } = useSWR<RecipeList>("/api/recipes?filter=all");
  const recipes = data?.recipes ?? [];
  const household = me ? (lang === "zh" ? me.household.name_zh : me.household.name) : " ";

  return (
    <main className="screen">
      <div className="screen__head">
        <div>
          <h1 className="display">{t.homeTitle}</h1>
          <p className="subtitle">{household}</p>
        </div>
        <IconButton icon="settings" label={t.settings} onClick={() => router.push("/settings")} />
      </div>

      <button type="button" className="field__control field__control--button" onClick={() => router.push("/search")}>
        <Icon name="search" />
        <span className="field__placeholder">{t.searchPlaceholder}</span>
      </button>

      <section className="section" aria-labelledby="recent-head">
        <div className="section__head">
          <h2 id="recent-head" className="overline">
            {t.lastMadeFirst}
          </h2>
          {data && <span className="muted home-count">{t.total(data.counts.all)}</span>}
        </div>
        {data && recipes.length === 0 && <p className="empty">{t.recipesEmpty}</p>}
        <div className="home-grid">
          {recipes.map((r) => (
            <RecipeTile key={r.id} recipe={r} />
          ))}
        </div>
      </section>
    </main>
  );
}
