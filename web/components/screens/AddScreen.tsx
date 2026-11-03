"use client";

import { useRouter } from "next/navigation";
import { useSWRConfig } from "swr";

import { logBody } from "@/components/recipe/LogFields";
import { RecipeEditor, type RecipeDraft } from "@/components/recipe/RecipeEditor";
import { api } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";
import type { Recipe } from "@/lib/types";

export function AddScreen() {
  const { t } = usePrefs();
  const router = useRouter();
  const { mutate } = useSWRConfig();

  const save = async ({ firstCook, ...draft }: RecipeDraft) => {
    const recipe = await api.post<Recipe>("/api/recipes", { ...draft, name: draft.name || null });
    // "We've made this": the first cook and its plate, saved with the recipe.
    if (firstCook) {
      await api.post(`/api/recipes/${recipe.id}/logs`, logBody(firstCook.log));
      await api.patch(`/api/recipes/${recipe.id}`, { plate_id: firstCook.plate_id });
    }
    await mutate((k) => typeof k === "string" && (k.startsWith("/api/recipes") || k.startsWith("/api/search")));
    router.replace(`/recipes/${recipe.id}`);
  };

  return <RecipeEditor title={t.newRecipe} onCancel={() => router.back()} onSave={save} />;
}
