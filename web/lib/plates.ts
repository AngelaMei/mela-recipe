// Plate manifest. When the designer delivers images, fill public/plates/plates.json
// with { "plates": [{ "id", "image", "foodInset" }] } — images take precedence over glazes.

export interface PlateDef {
  id: string;
  name: { en: string; zh: string };
  image?: string;
  foodInset?: number; // percent
}

export const PLATES: PlateDef[] = [
  { id: "celadon", name: { en: "Celadon", zh: "青瓷" } },
  { id: "cobalt", name: { en: "Cobalt line", zh: "藍邊白瓷" } },
  { id: "ochre", name: { en: "Ochre", zh: "赭黃釉" } },
  { id: "speckle", name: { en: "Speckled cream", zh: "米白斑點" } },
  { id: "tenmoku", name: { en: "Tenmoku", zh: "天目釉" } },
  { id: "slate", name: { en: "Slate", zh: "石板灰" } },
  { id: "blush", name: { en: "Blush", zh: "淡粉釉" } },
  { id: "ash", name: { en: "Ash glaze", zh: "灰釉" } },
];

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

export function plateDef(id: string | null | undefined): PlateDef | null {
  if (!id) return null;
  const base = PLATES.find((p) => p.id === id);
  if (!base) return null;
  return { ...base, ...(manifest?.[id] ?? {}) };
}
