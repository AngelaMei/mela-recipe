import type { Strings } from "./i18n";
import type { GroceryItem, Ingredient, Recipe } from "./types";

/** "2 cloves", "3瓣", "適量" */
export function ingredientQty(ing: Ingredient): string {
  if (ing.portion !== undefined) return ing.portion ?? "";
  const parts: string[] = [];
  if (ing.qty) parts.push(ing.qty);
  if (ing.unit) {
    const cjk = /[㐀-鿿]/.test(ing.unit);
    if (cjk && parts.length) parts[parts.length - 1] += ing.unit;
    else parts.push(ing.unit);
  }
  if (!parts.length && ing.note) return ing.note;
  return parts.join(" ");
}

export function groceryQty(item: GroceryItem, t: Strings): string {
  if (!item.qty) return "";
  if (!item.unit) return item.qty;
  const unit = t.unitNames[item.unit] ?? pluralUnit(item.unit, item.qty);
  return `${item.qty} ${unit}`;
}

const NO_PLURAL = new Set(["g", "kg", "ml", "l", "tsp", "tbsp", "oz", "lb"]);

/** clove -> cloves, bunch -> bunches, leaf -> leaves (English count units only). */
function pluralUnit(unit: string, qty: string): string {
  if (qty === "1" || NO_PLURAL.has(unit) || !/^[a-z]+$/i.test(unit)) return unit;
  if (unit === "leaf") return "leaves";
  if (/(ch|sh|s|x)$/.test(unit)) return `${unit}es`;
  return `${unit}s`;
}

/** "Shakshuka 2 + Curry Udon 1" (unitless) / "Shakshuka + Curry Udon" / "Added by Paul" */
export function grocerySources(item: GroceryItem, t: Strings, memberName: (n: string) => string): string {
  const srcs = item.sources;
  if (srcs.length === 1 && !srcs[0].from) return t.addedBy(memberName(srcs[0].by));
  const showAmounts = item.unitless && srcs.length > 1;
  // merge repeated sources (same recipe added twice)
  const merged: { label: string; amount: number | null }[] = [];
  for (const s of srcs) {
    const label = s.from ?? memberName(s.by);
    const prev = merged.find((m) => m.label === label);
    if (prev) prev.amount = prev.amount !== null || s.amount !== null ? (prev.amount ?? 0) + (s.amount ?? 0) : null;
    else merged.push({ label, amount: s.amount });
  }
  if (merged.length === 1 && !srcs.some((s) => !s.from)) return merged[0].label;
  return merged
    .map((m) => (showAmounts && m.amount !== null ? `${m.label} ${formatNumber(m.amount)}` : m.label))
    .join(" + ");
}

export function formatNumber(n: number): string {
  return Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100);
}

export function madeLabel(r: Recipe, t: Strings): string {
  return r.made_count > 0 ? t.madeTimes(r.made_count) : t.notMadeYet;
}

export function sourceGlyph(source: Recipe["source"]): string | undefined {
  if (source === "youtube") return "play_circle";
  if (source === "instagram") return "photo_camera";
  if (source === "link") return "open_in_new";
  return undefined;
}
