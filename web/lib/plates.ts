// The plate collection. Each plate is drawn as SVG (components/recipe/Plate.tsx)
// from the description below, and comes with its own tablecloth for the recipe
// hero and the plate picker, in the spirit of a top-down tabletop photo.
//
// When the designer delivers real plate images, list them in
// public/plates/plates.json as { "plates": [{ "id", "image", "foodInset" }] };
// an image takes precedence over the drawn plate (the tablecloth stays).

export type PlateShape = "round" | "scallop" | "petal" | "octagon";
export type PlateDecor = "none" | "flutes" | "garland" | "band" | "speckle";

export interface PlateDef {
  id: string;
  name: { en: string; zh: string };
  shape: PlateShape;
  /** Number of lobes for scallop / petal shapes. */
  lobes?: number;
  /** Rim glaze. */
  rim: string;
  /** Well (the flat centre) glaze. */
  well: string;
  /** Well radius as a fraction of the plate radius. */
  wellR: number;
  /** A glaze that fades from the centre outwards (ember). */
  centreGlaze?: string;
  /** Edge line colour, e.g. the ink rim or a stoneware edge. */
  edge?: string;
  edgeWidth?: number;
  decor: PlateDecor;
  /** Decor colour (band, garland flowers). */
  accent?: string;
  /** Tablecloth id (styles/tokens/plates.css: .cloth--<id>). */
  cloth: string;
  image?: string;
  foodInset?: number; // percent of the plate size
}

export const PLATES: PlateDef[] = [
  {
    id: "scallop",
    name: { en: "White scallop", zh: "白色波浪盤" },
    shape: "scallop",
    lobes: 18,
    rim: "#f7f5f0",
    well: "#f3f1eb",
    wellR: 0.68,
    decor: "none",
    cloth: "violet-stripe",
  },
  {
    id: "fluted",
    name: { en: "Fluted white", zh: "白色菊紋盤" },
    shape: "round",
    rim: "#f2f1ed",
    well: "#eeede8",
    wellR: 0.7,
    decor: "flutes",
    cloth: "chartreuse-weave",
  },
  {
    id: "garland",
    name: { en: "Rose garland", zh: "玫瑰花邊盤" },
    shape: "octagon",
    lobes: 24,
    rim: "#fbfaf6",
    well: "#f8f6f1",
    wellR: 0.66,
    decor: "garland",
    accent: "#d9707f",
    cloth: "blue-windowpane",
  },
  {
    id: "stoneware",
    name: { en: "Sage stoneware", zh: "灰綠陶盤" },
    shape: "round",
    rim: "#8d9284",
    well: "#7e8476",
    wellR: 0.8,
    edge: "#5f6457",
    edgeWidth: 3,
    decor: "speckle",
    cloth: "peach-linen",
  },
  {
    id: "petal",
    name: { en: "Grey petal", zh: "灰色花瓣盤" },
    shape: "petal",
    lobes: 12,
    rim: "#b4b8ba",
    well: "#c0c3c4",
    wellR: 0.62,
    decor: "none",
    cloth: "red-gingham",
  },
  {
    id: "ember",
    name: { en: "Ember glaze", zh: "橘紅漸層釉" },
    shape: "round",
    rim: "#f4ebe2",
    well: "#e9a07c",
    wellR: 0.86,
    centreGlaze: "#d4512e",
    decor: "none",
    cloth: "cream-linen",
  },
  {
    id: "greenband",
    name: { en: "Green band", zh: "綠邊餐盤" },
    shape: "round",
    rim: "#f6f5f1",
    well: "#f2f1ec",
    wellR: 0.66,
    decor: "band",
    accent: "#4f8a55",
    cloth: "navy-check",
  },
  {
    id: "inkrim",
    name: { en: "Ink rim", zh: "黑邊深盤" },
    shape: "round",
    rim: "#efeeea",
    well: "#e6e5e0",
    wellR: 0.8,
    edge: "#26231f",
    edgeWidth: 3.5,
    decor: "none",
    cloth: "ink-print",
  },
  {
    id: "plain",
    name: { en: "Everyday white", zh: "日常白盤" },
    shape: "round",
    rim: "#f6f5f1",
    well: "#f1f0eb",
    wellR: 0.7,
    decor: "none",
    cloth: "lemon-stripe",
  },
];

export const DEFAULT_PLATE = "plain";

/** Plates from the first, placeholder collection map to their nearest new plate. */
const LEGACY: Record<string, string> = {
  celadon: "stoneware",
  cobalt: "garland",
  ochre: "ember",
  speckle: "plain",
  tenmoku: "inkrim",
  slate: "petal",
  blush: "ember",
  ash: "fluted",
};

let manifest: Record<string, { image?: string; foodInset?: number }> | null = null;

export async function loadPlateManifest(): Promise<void> {
  if (manifest) return;
  try {
    const res = await fetch("/plates/plates.json", { cache: "force-cache" });
    const data = (await res.json()) as { plates?: { id: string; image?: string; foodInset?: number }[] };
    manifest = Object.fromEntries((data.plates ?? []).map((p) => [p.id, p]));
  } catch {
    manifest = {};
  }
}

export function plateDef(id: string | null | undefined): PlateDef {
  const key = id ? (LEGACY[id] ?? id) : DEFAULT_PLATE;
  const base = PLATES.find((p) => p.id === key) ?? PLATES.find((p) => p.id === DEFAULT_PLATE)!;
  return { ...base, ...(manifest?.[base.id] ?? {}) };
}
