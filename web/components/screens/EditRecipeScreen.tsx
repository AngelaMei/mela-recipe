"use client";

import { useRouter } from "next/navigation";
import useSWR, { useSWRConfig } from "swr";

import { RecipeEditor, type RecipeDraft } from "@/components/recipe/RecipeEditor";
import { api } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";
import type { Recipe } from "@/lib/types";

export function EditRecipeScreen({ id }: { id: string }) {
  const { t } = usePrefs();
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { data: recipe, error } = useSWR<Recipe>(`/api/recipes/${id}`, { revalidateOnFocus: false });

  if (error) return <p className="empty">{t.genericError}</p>;
  if (!recipe) return null;

  const save = async (draft: RecipeDraft) => {
    const updated = await api.patch<Recipe>(`/api/recipes/${id}`, { ...draft, name: draft.name || null });
    await mutate(`/api/recipes/${id}`, updated, { revalidate: false });
    await mutate((k) => typeof k === "string" && (k.startsWith("/api/recipes?") || k.startsWith("/api/search")));
    router.replace(`/recipes/${id}`);
  };

  return <RecipeEditor title={t.editRecipe} initial={recipe} onCancel={() => router.back()} onSave={save} />;
}
