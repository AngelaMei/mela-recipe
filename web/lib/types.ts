export type Source = "youtube" | "instagram" | "link" | "manual";

export interface Ingredient {
  name: string;
  amount: number | null;
  qty: string | null;
  unit: string | null;
  note: string | null;
}

export interface CookLog {
  id: string;
  recipe_id: string;
  cooked_on: string; // YYYY-MM-DD
  rating: number | null;
  note: string | null;
  tweaks: string | null;
  photo_url: string | null;
  photo_id: string | null;
  created_by: string;
  created_at: string | null;
}

export interface Recipe {
  id: string;
  name: string;
  name_alt: string | null;
  source: Source;
  source_url: string | null;
  note: string | null;
  ingredients: Ingredient[];
  steps: string[];
  plate_id: string | null;
  created_by: string;
  created_at: string | null;
  made_count: number;
  last_cooked: string | null;
  avg_rating: number | null;
  photo_url: string | null;
  matched_index?: number | null;
  logs?: CookLog[];
}

export interface RecipeList {
  counts: { all: number; made: number; not_made: number };
  recipes: Recipe[];
}

export interface SearchResponse {
  query: string;
  count: number;
  results: Recipe[];
}

export interface GrocerySource {
  from: string | null;
  recipe_id: string | null;
  by: string;
  amount: number | null;
}

export interface GroceryItem {
  id: string;
  name: string;
  key: string;
  qty: string | null;
  unit: string | null;
  unitless: boolean;
  sources: GrocerySource[];
  checked: boolean;
  checked_at: string | null;
  created_at: string | null;
}

export interface GroceryList {
  open: GroceryItem[];
  basket: GroceryItem[];
  open_count: number;
}

export interface Member {
  name: string;
  name_zh: string;
}

export interface Household {
  name: string;
  name_zh: string;
  members: Member[];
}

export interface Me {
  member: string;
  household: Household;
}

export interface ParsedStep {
  text: string;
  short: boolean;
}

export type ParseStatus = "ok" | "empty" | "link_only" | "needs_caption" | "fetch_failed";

export interface ParseResult {
  source: "youtube" | "instagram" | "link" | "text";
  url: string | null;
  status: ParseStatus;
  ingredients: Ingredient[];
  steps: ParsedStep[];
}

export interface SplitOptions {
  line: boolean;
  comma: boolean;
  number: boolean;
  period: boolean;
}
