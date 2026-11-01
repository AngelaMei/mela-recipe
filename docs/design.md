# Mela — design system & build guide

Mela is a private recipe and grocery app for one household, Mei & Paul. It's a mobile web app built with Next.js. It is not a social or public product: there are two users, one shared kitchen, and no feeds.

**What it does**
- Saves recipes from a pasted **YouTube link**, **Instagram link**, or **any text**. Ingredients and steps are parsed with rules (no AI).
- Shows recently cooked dishes as **ceramic plates** on Home: 3 per row, up to 9.
- **Ingredient search**: type an ingredient and see every recipe that uses it.
- Keeps a **cook log** per recipe: date, rating, note, photo, and tweaks.
- Keeps a **shared grocery list**. You can add a recipe's missing ingredients in one tap, and duplicates are merged.
- **One language at a time**: English or 繁體中文, switched in Settings, per device.

**Sources**: the design canvas `Recipe App v2.dc.html` in this project. Round 2 set the visual direction, 3b the typography, 4a–4i the screens, 6a–6c the single "paste anything" entry, and 7b the navigation. There is no codebase or Figma file. There is no logo yet: the wordmark is "Mela" set in Figtree 700.

**Out of scope for this README**: the backend, auth and sync between the two phones. The engineer chooses these. Everything below assumes a data layer that gives you `recipes`, `logs` and `groceryItems`.

---

## Index

| Path | What |
|---|---|
| `styles.css` | Single entry point. Import it once in `app/layout.tsx` |
| `tokens/` | `colors.css` (light + dark), `typography.css`, `spacing.css` (space, radii, shadows, layout), `plates.css` (glaze fallbacks), `motion.css`, `fonts.css`, `base.css` |
| `components/core/` | Icon, Button, IconButton, Badge, Chip |
| `components/forms/` | TextField, Checkbox, SegmentedControl |
| `components/navigation/` | BottomNav (floating pill + add button), Tabs, TopBar |
| `components/recipe/` | Plate, RecipeTile, IngredientRow, StepRow, GroceryItem, LogEntry, SearchResult |
| `components/overlays/` | Sheet |
| `components/_load.js` | Dev-only loader for the preview cards and UI kit. **Not for production** |
| `ui_kits/mela-app/` | Clickable prototype. `parse.js` is the **reference implementation** of parsing, merging and search. `i18n.js` holds all UI copy in both languages |
| `assets/plates/` | Plate image spec + `plates.json` manifest (the designer delivers the images) |
| `guidelines/` | Specimen cards: colour, type, spacing, plates, icons |
| `SKILL.md` | Agent-skill wrapper |

Each component has a `.jsx` file (reference), a `.d.ts` file (props contract) and a `.prompt.md` file (usage). They use inline styles with CSS variables. Port them to `.tsx` with CSS Modules or plain CSS classes, whichever you prefer, but **keep the token names**.

---

## Decisions log

| Topic | Decision |
|---|---|
| Stack | Next.js (App Router), installable PWA, plain CSS with CSS variables (no Tailwind) |
| Language | English or Traditional Chinese, one at a time. Per device, set in Settings. User content (recipe names, notes) is shown **as entered**; a recipe may have an optional name in the other language |
| Parsing | Rule-based only (see Interaction specs) |
| YouTube | Read the video description server-side (YouTube Data API `videos.list?part=snippet`). Import **only ingredients and steps**, never the title or thumbnail |
| Instagram | Captions can't be fetched reliably. Show a "Paste the caption" field. If it's left empty, save the link only |
| Saved vs cooked | One recipe list. "Not made yet" is a filter, not a separate inbox |
| Plates | The designer supplies plate images or rim patterns. CSS glazes are placeholders. A plate is picked after the first cook |
| Navigation | Floating dark pill (4 tabs) at bottom-left and a terracotta + button at bottom-right (option 7b) |
| Dark mode | Tokens are defined (`[data-theme="dark"]`). Exposed in Settings › Appearance |

---

## CONTENT FUNDAMENTALS

- **Voice**: "we/our" for the couple. The app speaks as their shared kitchen, not as a brand. Examples: "Our kitchen", "We made it!", "Tick what we already have", "We have everything".
- **Tone**: warm and plain. Short sentences with no exclamation marks, except the single celebratory "We made it!".
- **Casing**: sentence case everywhere ("Add 3 missing to grocery list", not Title Case). Overlines are uppercase in English only; Chinese is never uppercased.
- **Numbers**: always digits, with tabular figures for quantities. Use `×` for counts ("Made 7×" / "做過 7 次"). Dates are "Oct 24" / "10月24日".
- **No emoji. No exclamation stacks. No food puns.**
- **Errors and empty states** say what happened, then what to do: "Nothing found. It'll be saved with just the link." and "The post didn't include a recipe. Watch it, then paste what you need."
- **Buttons** start with a verb and name the result: "Add 3 missing to grocery list", "Use this plate", "Log today's cook".
- **Chinese copy** is Traditional (Taiwan usage: 採買, 食譜, 做好了). Don't translate word for word; see `ui_kits/mela-app/i18n.js` for every string.

| Key | English | 繁體中文 |
|---|---|---|
| Home title | Our kitchen | 我們的廚房 |
| Search placeholder | Search by ingredient | 用食材搜尋 |
| Section | Recently made | 最近做過 |
| Count | Made 7× | 做過 7 次 |
| Saved state | Not made yet | 還沒做過 |
| Tabs | Home · Search · Grocery · Recipes | 首頁 · 搜尋 · 採買 · 食譜 |
| CTA | Add 3 missing to grocery list | 把缺的 3 樣加入採買 |
| First cook | We made it! | 做好了！ |
| Search result | 4 recipes use eggplant | 4 道菜用到茄子 |
| Grocery subtitle | 6 to buy · shared with Paul | 還要買 6 樣 · 與保羅共用 |

---

## VISUAL FOUNDATIONS

**Mood.** A calm, warm kitchen table: cream paper, linen, real ceramics. It is *not* cute, gamified or bubbly. The plates are the only rich visuals, and everything else stays quiet so they stand out.

**Colour.** Warm cream neutrals (`--cream-*`) and warm ink text (`--ink-*`). There is **one action colour, terracotta** (`--accent`), used for the primary CTA, the add button, the active tab label, links, step numbers and search highlights. **Sage** (`--success`) means done (checked boxes, "Found 6 ingredients"). Never introduce a third accent. Write code against the semantic tokens (`--bg-app`, `--surface-card`, `--text-secondary`…), never against hex values.

**Type.** Figtree for everything English (400/500/600/700) and Noto Sans TC for Chinese. When the language is Chinese, set `font-family: var(--font-zh)` on the root.
- Display: 31/1.1/700 with −0.025em tracking (screen titles)
- Title: 27/1.15/700 (recipe name)
- Heading: 18/700 (section heads in English; Chinese uses 17)
- Body: 16 for list primary text, 15 for paragraphs
- Caption: 13 for meta
- Overline: 13/600/+0.06em uppercase
- Nav label: 11.5–14

The minimum text size is 11.5px and is only used for nav labels.

**Spacing.** 4px base. The screen gutter is **22px**. List rows are ≥44px tall with 13px vertical padding. Sections are separated by 24px plus an overline. Home grid: 3 columns, 16px side padding, `gap: 20px 10px`, plates 102px.

**Backgrounds.**
- `--bg-app` cream for screens.
- **Linen** (a fine crosshatch of two 1px repeating gradients over `--bg-linen`) behind the recipe hero plate and in the plate picker.
- No photos as full-bleed backgrounds, no gradients and no illustrations.

**Plates (signature element).** A plate has 4 layers: rim (glaze or designer image) → well (inset 13%, inner shadow) → dish photo (inset 22%, circle crop) → 145° light overlay. The drop shadow is CSS, never baked into the image. A dashed empty plate means "not made yet". Sizes:
- Home: 102
- Detail hero: 200
- Search and Recipes rows: 64
- Picker: 62–72

**Borders and cards.** Content sits on cream separated by **1px `--line` hairlines**, not boxed cards. Grouped previews (parsed ingredients, settings rows) use `--surface-card` with a 1px border and radius 12–14. No coloured left-border cards and no heavy cards.

**Corner radii.**
- 3: highlight
- 6: checkbox
- 9: chip
- 12: field and grouped list
- 14: button
- 24: sheet
- Pill: nav

The overall feel is soft but not bubbly.

**Shadows.** Only floating things cast shadows: the nav pill (`--shadow-float`), the add button (`--shadow-fab`), the selected segment (`--shadow-seg`) and plates. Everything else is flat.

**Transparency and blur.** Only the overlay back button (white at 92% opacity over linen) and the sheet scrim (`--scrim`) use transparency. There is no backdrop blur.

**Layout rules.**
- The status bar area is 46px.
- The floating nav sits 26px from the bottom, so scroll content needs `padding-bottom: var(--content-bottom-pad)` (112px).
- Sub-pages (recipe, add, settings) hide the nav and show a back control.
- Sticky bottom CTAs sit 18px from the sides and 26px from the bottom.
- Respect `env(safe-area-inset-bottom)` on real devices: add it to `--nav-offset`.

**Motion.** Quiet and quick.
- Press: scale 0.97 over 120ms.
- Tab or chip change: 200ms colour/padding with `--ease-out`.
- Sheet: slides up over 320ms.

There are no bounces, confetti or page transitions beyond a simple push. Respect `prefers-reduced-motion`; the tokens already zero out.

**States.** There's no hover styling on mobile beyond the link colour. Press = scale. Focus = 2px terracotta outline at 2px offset (`:focus-visible`). Disabled = 40% opacity. Field focus = 1.5px ink border.

**Imagery.** These are the couple's own phone photos: warm, natural light, top-down where possible, cropped into the plate well. No stock photography.

---

## ICONOGRAPHY

- **Material Symbols Rounded** (Google Fonts variable font), loaded in `tokens/fonts.css`. Use the `.mela-icon` class or the `<Icon>` component.
- Use the outline style by default, with weight 400. Only the **active nav tab** uses `FILL 1`.
- Sizes:
  - 24–26: nav
  - 22: buttons and fields
  - 16–18: inline (`open_in_new`, `check_circle`)
- Icons in use: `home search shopping_basket menu_book add settings chevron_left chevron_right check check_circle photo_camera play_circle open_in_new content_paste group straighten expand_more`.
- **Source glyphs**: `play_circle` = YouTube and `photo_camera` = Instagram, shown inside an empty plate. Don't use the YouTube or Instagram logos.
- No emoji. The only unicode used as a glyph is ★/☆ for ratings and × for counts.
- For production, either self-host the font subset or swap to `@material-symbols/svg-400` React icons. Keep the same names.

---

## Components

All the reusable primitives are listed in the Index. Notes:
- **BottomNav** must have exactly 4 items. Inactive tabs are icon-only with `aria-label`; the active tab expands to icon + label. The add button is separate, at the bottom-right.
- **Plate** prefers a `plate.image` from `assets/plates/plates.json` and falls back to the CSS `--glaze-<id>` tokens.
- **Button**: one `primary` (terracotta) per screen.

**Intentional additions**: `Icon` wraps the icon font, and `Badge` shows the grocery count. Both are needed by the designs; neither exists as a separate design artefact.

---

## Screen specs

All screens are 390pt wide (iPhone 13–15); the layout is fluid from 360 to 430.

**1. Home** (`HomeScreen`)
- Display title "Our kitchen", household subtitle, and a settings IconButton (42px) at the top right.
- A search field that is a button: tapping it switches to the Search tab.
- Overline "Recently made", with an "All recipes" link to the Recipes tab.
- Grid of the **9 most recently cooked** recipes (sorted by latest log date). 3 columns; each tile shows plate, name and "Made N×". Not-made recipes never appear here.

**2. Search** (`SearchScreen`)
- The field is auto-focused. Results update as you type (debounce 150ms).
- Empty query: "Try" chips with common ingredients.
- Overline "N recipes use {q}". Each `SearchResult` row has the plate (dashed if not made), name, "Made N×" or "Not made yet", the matched ingredient highlighted, then 2 other ingredients and "+N".

**3. Grocery** (`GroceryScreen`)
- Title and "N to buy · shared with Paul".
- Add field + dark square add button. Typed text is parsed like an ingredient line ("2 onions" → qty 2).
- Open items show name, merged quantity, and their sources ("Shakshuka 2 + Curry Udon 1" / "Added by Paul").
- Checked items move to "In the basket (N)", struck through. "Clear" removes them.

**4. Recipes** (`RecipesScreen`)
- Title + "N total", search by name or ingredient.
- Filter chips: All · Not made yet · N · Made. A Source filter (YouTube/Instagram/manual) is optional.
- List rows are `SearchResult`s. Not-made recipes show a dashed plate with the source glyph and the saved note.

**5. Recipe detail** (`RecipeScreen`)
- Linen hero, 268px tall, with a 200px plate. Back button (overlay) at top-left; "Change plate" at top-right (only after the first cook).
- Title, a meta row (Made N× · ★ avg · Last: date · Source ↗) and Tabs: Ingredients / Steps (N) / Log (N).
- **Ingredients tab**: tick what we already have. The sticky CTA says "Add {missing} missing to grocery list", then "Added to grocery list" (disabled). If everything is ticked, it reads "We have everything".
- **Log tab**: `LogEntry` list, with a sticky dark CTA "Log today's cook" that opens the log form (rating, note, photo, tweaks; this form isn't drawn yet).
- **Not made yet**: dashed hero plate, and the CTA is "We made it!". That creates the first log, then opens the plate picker sheet.
- **Link-only** (nothing parsed): a box with "No ingredients or steps yet" plus [Paste text] [Open original].

**6. Add recipe** (`AddScreen`, opened by the + button)
- Header: Cancel · New recipe · Save.
- One field: **"Paste a link or recipe text"**. It detects the source as you type (see parsing).
  - YouTube: "Read from the video description · Found N ingredients and M steps".
  - Instagram: the helper explains captions can't be read, and a **Caption** field appears.
  - Other URL: link-only notice.
  - Plain text: parse directly.
- Name field (optional; falls back to "Untitled recipe").
- Split toggles (Line, Comma, 1. 2. 3., 。) for steps.
- Live preview of ingredients + steps. Very short steps (under 8 characters) offer "Merge ↑".
- Save creates a recipe in the **Not made yet** state and opens its detail page.

**7. Plate picker** (a Sheet from detail)
- Title "Choose a plate", a 160px preview, the plate name, a 4×2 grid of plates (selected = 2px ink ring), and "Use this plate".

**8. Settings** (opened from the Home gear)
- Back to Home, title.
- Language: segmented English | 繁體中文. Stored **per device** (localStorage is fine).
- Appearance: Light | Dark.
- Kitchen rows: Household, Units.

---

## Interaction specs

Reference code: `ui_kits/mela-app/parse.js`. Port it 1:1 and unit-test it with the examples below.

### Source detection
| Input | Result |
|---|---|
| single token containing `youtu.be` / `youtube.com` | `youtube`: server route fetches the description, then `parseRecipe` |
| single token containing `instagram.com` | `instagram`: show a Caption field, then `parseRecipe(caption)`. Empty = link-only |
| other single URL | `link`: link-only recipe |
| anything else | `text`: `parseRecipe(input)` |

### parseRecipe(text, opts)
1. Normalise line breaks. Detect section headers on their own line:
   - Ingredients: `ingredients|ingredient|食材|材料` (an optional `:`/`：` is allowed).
   - Steps: `steps|method|directions|instructions|作法|做法|步驟`.
2. **With headers**: lines go to the current section.
3. **Without headers**: a line is treated as an ingredient if it is ≤40 characters and either:
   - starts with a quantity (digits, fractions, ½, or 一–十/半/兩), optionally followed by a unit, or
   - ends with quantity + unit ("蒜頭 3瓣"), or
   - ends with 適量/少許/"to taste".

   Every other line is a step.
4. **Ingredient lines** are split on `, ，、` and parsed into `{name, qty, unit}`. The patterns are "qty unit name" and "name qty unit". Units are matched only on a word boundary, so "2 garlic" never reads as "2 g arlic".
5. **Steps**: `splitSteps(text, {line, comma, number, period})`. Defaults: line ✓, comma ✓, number ✓, period ✗.
   - number: "1. / 1) / 1、" starts a new step.
   - line: newlines split.
   - comma: `, ，、 ; ；` split.
   - period: `。` or ". " split.
   - Then trim bullets, drop empty pieces, and merge pieces shorter than 3 characters into the previous step. Steps under 8 characters are flagged `short`, which shows "Merge ↑".

Example input:
```
cut eggplant into strips, salt 10 min, pan fry till soft
fry garlic, ginger & doubanjiang, add pork
```
Result: 6 steps (comma + line). Turning off Comma gives 2 steps.

### Grocery merging (`addToGrocery`)
- **Key** = lower-cased name → alias map (scallion = green onion = 青蔥 = 蔥; eggplant = aubergine = 茄子; …) → simple de-pluralising (eggs→egg, tomatoes→tomato).
- **Units** convert to a base unit: g/kg/克 → g, ml/l/毫升 → ml, tsp/tbsp/小匙/大匙 → tsp. Plurals are folded (cloves→clove).
- If the key and base unit match an **unchecked** item, the amounts are summed and the source is appended. Otherwise a new row is added. Incompatible units (1 bunch + 2 stalks) stay as separate rows with the same name.
- Display: 1000 g → "1 kg"; tsp in multiples of 3 → tbsp. Sources are joined with " + "; unitless items show the amount per source ("Shakshuka 2 + Curry Udon 1").
- "Add N missing" adds only the **unticked** ingredients, with `from` = the recipe name.
- Checked items never merge (they are already bought).

### Search (`searchRecipes`)
- The query matches a recipe when an ingredient's key equals the query's key (aliases cross languages, so "蔥" finds "Scallion") **or** an ingredient's English or Chinese name contains the query.
- Results: **every** recipe that uses the ingredient, made and not-made alike. Sort by latest cook date; not-made recipes go last.
- The Recipes tab search also matches recipe names.

---

## Accessibility

- Contrast: body text uses `--text-body`/`--text-primary` on cream (≥ 9:1). Secondary `--ink-600` on cream is 5.9:1. `--ink-500` (4.0:1) is **only** for placeholders and disabled text. White on terracotta is 5.5:1.
- Touch targets are ≥44×44. Small visual controls (20px checkboxes, sm buttons) get their target from the full row.
- Icon-only buttons always have `aria-label`. The nav uses `aria-current="page"`.
- Checkboxes are `role="checkbox"` with `aria-checked`. The segmented control and tabs use `role="tablist"`/`tab` with `aria-selected`.
- The sheet is `role="dialog"` with `aria-modal`. Trap focus inside it, close on Esc or a scrim tap, and return focus to the trigger.
- Set `lang="zh-Hant"` on `<html>` when Chinese is chosen, so screen readers and line-breaking behave correctly.
- Ratings expose "4 of 5" as an `aria-label`, not just ★ characters.
- Respect `prefers-reduced-motion` and the system text size: use rem in production and let rows grow, never fixed heights.
- Plates are `role="img"` with the recipe name. The dish photo inside is decorative.

---

## Dark mode

Set `data-theme="dark"` on `<html>`, or map it from `prefers-color-scheme` when the setting is "System". All the semantic tokens remap.
- Terracotta lightens to `#e0866d`, with dark text on it.
- The nav pill becomes `#3a312a`, with a cream active pill.
- Plates keep their glazes; only the shadows read darker.

Test the linen hero and the dashed empty plate in both themes.

---

## Plate assets (for the designer)

See `assets/plates/README.md`:
- 1024² transparent WebP, top-down, light from the top-left, **no baked shadow**.
- A `foodInset` % per plate.
- Optional seamless rim pattern.

Fill `plates.json` and the components pick it up. The CSS glazes stay as a fallback.
