import { ingredientQty } from "@/lib/format";
import type { Ingredient } from "@/lib/types";

import { Checkbox } from "../forms/Checkbox";

export interface IngredientRowProps {
  ingredient: Ingredient;
  /** When onToggle is set, the row is a checkbox ("tick what to buy"). */
  selected?: boolean;
  onToggle?: () => void;
}

export function IngredientRow({ ingredient, selected, onToggle }: IngredientRowProps) {
  const qty = ingredientQty(ingredient);
  // Older recipes have no portion; their prep note ("chopped") shows under the name.
  const note = ingredient.portion === undefined && ingredient.qty && ingredient.note ? ingredient.note : null;
  const content = (
    <>
      {onToggle && <Checkbox checked={!!selected} />}
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
        aria-checked={!!selected}
        className="row ingredient-row"
        onClick={onToggle}
      >
        {content}
      </button>
    </li>
  );
}
