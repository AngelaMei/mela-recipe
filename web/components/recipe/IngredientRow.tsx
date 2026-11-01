import { ingredientQty } from "@/lib/format";
import type { Ingredient } from "@/lib/types";

import { Checkbox } from "../forms/Checkbox";

export interface IngredientRowProps {
  ingredient: Ingredient;
  /** When set, the row is a checkbox ("tick what we already have"). */
  have?: boolean;
  onToggle?: () => void;
}

export function IngredientRow({ ingredient, have, onToggle }: IngredientRowProps) {
  const qty = ingredientQty(ingredient);
  const note = ingredient.qty && ingredient.note ? ingredient.note : null;
  const content = (
    <>
      {onToggle && <Checkbox checked={!!have} />}
      <span className="row__main">
        <span className="row__title">{ingredient.name}</span>
        {note && <span className="row__sub" style={{ display: "block" }}>{note}</span>}
      </span>
      {qty && <span className="row__end">{qty}</span>}
    </>
  );
  if (!onToggle) return <li className="row">{content}</li>;
  return (
    <li>
      <button
        type="button"
        role="checkbox"
        aria-checked={!!have}
        className={`row ingredient-row${have ? " ingredient-row--have" : ""}`}
        onClick={onToggle}
      >
        {content}
      </button>
    </li>
  );
}
