# Plate assets

- 1024×1024 transparent WebP, top-down, light from the top-left, **no baked shadow** (the shadow is CSS).
- Give each plate a `foodInset` (percent) — where the dish photo sits inside the well.
- Optional seamless rim pattern.
- Plate ids: `celadon cobalt ochre speckle tenmoku slate blush ash` (names in `lib/plates.ts`).

Drop the files in this folder and list them in `plates.json`. Plates without an image fall back to the CSS glaze tokens.
