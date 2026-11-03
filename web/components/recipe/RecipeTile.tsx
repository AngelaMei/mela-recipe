import Link from "next/link";

import { sourceGlyph } from "@/lib/format";
import type { Recipe } from "@/lib/types";

import { Plate } from "./Plate";

/** Home grid tile: plate and name only. Not made yet = dashed plate. */
export function RecipeTile({ recipe }: { recipe: Recipe }) {
  const made = recipe.made_count > 0;
  return (
    <Link href={`/recipes/${recipe.id}`} className="recipe-tile pressable">
      <Plate
        plateId={recipe.plate_id}
        photoUrl={recipe.photo_url}
        photoCrop={recipe.photo_crop}
        size={102}
        label={recipe.name}
        empty={!made}
        glyph={!made ? sourceGlyph(recipe.source) : undefined}
      />
      <span className="recipe-tile__name">{recipe.name}</span>
    </Link>
  );
}
