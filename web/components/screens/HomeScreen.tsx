"use client";

import Link from "next/link";
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
  const { data } = useSWR<RecipeList>("/api/recipes?filter=made");

  // The 9 most recently cooked (API sorts by latest log date). Not-made never appear.
  const recent = (data?.recipes ?? []).slice(0, 9);
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
            {t.recentlyMade}
          </h2>
          <Link href="/recipes" className="link">
            {t.allRecipes}
          </Link>
        </div>
        {data && recent.length === 0 && <p className="empty">{t.homeEmpty}</p>}
        <div className="home-grid">
          {recent.map((r) => (
            <RecipeTile key={r.id} recipe={r} meta={t.madeTimes(r.made_count)} />
          ))}
        </div>
      </section>
    </main>
  );
}
