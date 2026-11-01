import Link from "next/link";

import type { Recipe } from "@/lib/types";

import { Plate } from "./Plate";

export function RecipeTile({ recipe, meta }: { recipe: Recipe; meta: string }) {
  return (
    <Link href={`/recipes/${recipe.id}`} className="recipe-tile pressable">
      <Plate plateId={recipe.plate_id} photoUrl={recipe.photo_url} size={102} label={recipe.name} />
      <span className="recipe-tile__name">{recipe.name}</span>
      <span className="recipe-tile__meta">{meta}</span>
    </Link>
  );
}
