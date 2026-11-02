# Plates

The collection is defined in `web/lib/plates.ts` and drawn as SVG by `web/components/recipe/Plate.tsx`. Each plate has a tablecloth (`web/styles/tokens/plates.css`) that shows behind it on the recipe page and in the plate picker. See all of them at `/plates`.

| id | Plate | Shape / detail | Tablecloth |
|---|---|---|---|
| `scallop` | White scallop · 白色波浪盤 | 18 soft waves | violet double stripes |
| `fluted` | Fluted white · 白色菊紋盤 | ribbed rim | chartreuse weave, natural stripe |
| `garland` | Rose garland · 玫瑰花邊盤 | soft octagon, roses and leaves | blue windowpane |
| `stoneware` | Sage stoneware · 灰綠陶盤 | speckled, dark edge | peach linen |
| `petal` | Grey petal · 灰色花瓣盤 | 12 petals | red gingham |
| `ember` | Ember glaze · 橘紅漸層釉 | coral centre fading to cream | cream linen |
| `greenband` | Green band · 綠邊餐盤 | green line on the rim | navy check |
| `inkrim` | Ink rim · 黑邊深盤 | deep well, black edge | black brush print |
| `plain` | Everyday white · 日常白盤 | plain | lemon stripes |

All plates are top-down, lit from the top-left; the shadow is a CSS `drop-shadow` so it follows scalloped and petal edges.

## Swapping in photographed plates

If you later shoot or commission real plates:

- 1024×1024 transparent WebP, top-down, light from the top-left, **no baked shadow**.
- Give each plate a `foodInset` (percent): where the dish photo sits inside the well.
- Drop the files here and list them in `plates.json`, e.g. `{ "id": "garland", "image": "/plates/garland.webp", "foodInset": 22 }`. An image replaces the drawn plate; its tablecloth stays.
