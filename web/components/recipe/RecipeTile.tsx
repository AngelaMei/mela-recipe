import Link from "next/link";

import type { Recipe } from "@/lib/types";

import { Plate } from "./Plate";

/** Home grid tile: plate and name only. */
export function RecipeTile({ recipe }: { recipe: Recipe }) {
  return (
    <Link href={`/recipes/${recipe.id}`} className="recipe-tile pressable">
      <Plate plateId={recipe.plate_id} photoUrl={recipe.photo_url} photoCrop={recipe.photo_crop} size={102} label={recipe.name} />
      <span className="recipe-tile__name">{recipe.name}</span>
    </Link>
  );
}
