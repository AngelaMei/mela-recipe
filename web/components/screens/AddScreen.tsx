"use client";

import { useRouter } from "next/navigation";
import { useSWRConfig } from "swr";

import { RecipeEditor, type RecipeDraft } from "@/components/recipe/RecipeEditor";
import { api } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";
import type { Recipe } from "@/lib/types";

export function AddScreen() {
  const { t } = usePrefs();
  const router = useRouter();
  const { mutate } = useSWRConfig();

  const save = async (draft: RecipeDraft) => {
    // A new recipe starts as "Not made yet"; open its detail page.
    const recipe = await api.post<Recipe>("/api/recipes", { ...draft, name: draft.name || null });
    await mutate((k) => typeof k === "string" && (k.startsWith("/api/recipes") || k.startsWith("/api/search")));
    router.replace(`/recipes/${recipe.id}`);
  };

  return <RecipeEditor title={t.newRecipe} onCancel={() => router.back()} onSave={save} />;
}
