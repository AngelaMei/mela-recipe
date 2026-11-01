import type { GroceryItem as Item } from "@/lib/types";

import { Checkbox } from "../forms/Checkbox";

export interface GroceryItemProps {
  item: Item;
  qty: string;
  sources: string;
  onToggle: () => void;
}

export function GroceryItem({ item, qty, sources, onToggle }: GroceryItemProps) {
  return (
    <li>
      <button
        type="button"
        role="checkbox"
        aria-checked={item.checked}
        className={`row grocery-item${item.checked ? " grocery-item--checked" : ""}`}
        onClick={onToggle}
      >
        <Checkbox checked={item.checked} />
        <span className="row__main">
          <span className="row__title" style={{ display: "block" }}>{item.name}</span>
          {sources && <span className="row__sub" style={{ display: "block" }}>{sources}</span>}
        </span>
        {qty && <span className="row__end">{qty}</span>}
      </button>
    </li>
  );
}
