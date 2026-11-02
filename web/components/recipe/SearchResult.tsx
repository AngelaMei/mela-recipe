import Link from "next/link";

import { madeLabel, sourceGlyph } from "@/lib/format";
import type { Strings } from "@/lib/i18n";
import type { Recipe } from "@/lib/types";

import { Plate } from "./Plate";

export interface SearchResultProps {
  recipe: Recipe;
  t: Strings;
  /** Highlight this ingredient (index into recipe.ingredients). */
  matchedIndex?: number | null;
  showNote?: boolean;
}

/** Plate (dashed if not made), name, "Made N×" / "Not made yet", matched ingredient + 2 others + "+N". */
export function SearchResult({ recipe, t, matchedIndex, showNote }: SearchResultProps) {
  const made = recipe.made_count > 0;
  const ings = recipe.ingredients;
  const matched = matchedIndex != null ? ings[matchedIndex] : null;
  const others = ings.filter((_, i) => i !== matchedIndex);
  const shown = others.slice(0, matched ? 2 : 3);
  const rest = ings.length - shown.length - (matched ? 1 : 0);

  return (
    <li>
      <Link href={`/recipes/${recipe.id}`} className="search-result">
        <Plate
          size={64}
          plateId={recipe.plate_id}
          photoUrl={recipe.photo_url}
          photoCrop={recipe.photo_crop}
          empty={!made}
          glyph={!made ? sourceGlyph(recipe.source) : undefined}
          label={recipe.name}
        />
        <span className="search-result__body">
          <span className="search-result__name" style={{ display: "block" }}>{recipe.name}</span>
          <span className="search-result__meta" style={{ display: "block" }}>{madeLabel(recipe, t)}</span>
          {ings.length > 0 && (
            <span className="search-result__ings" style={{ display: "block" }}>
              {matched && <mark>{matched.name}</mark>}
              {matched && shown.length > 0 && " · "}
              {shown.map((i) => i.name).join(" · ")}
              {rest > 0 && ` ${t.moreCount(rest)}`}
            </span>
          )}
          {showNote && !made && recipe.note && (
            <span className="search-result__note" style={{ display: "block" }}>{recipe.note}</span>
          )}
        </span>
      </Link>
    </li>
  );
}
