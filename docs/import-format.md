# Importing recipes into Mela

**Settings › Backup › Import recipes** takes one file:

| File | What it is |
|---|---|
| `.md` or `.txt` | Recipes written as text (below). The easiest to write by hand. |
| `.zip` from **Export recipes** | A full Mela backup: recipes, cook logs and photos. |
| `.zip` of text files | Every `.md`, `.txt` and `.json` inside is imported. |
| `.json` | A list of recipes, for converting from another app with a script. |

You always see a preview first: every recipe found, how many ingredients, steps and cooks each has, and anything that couldn't be read. Nothing is saved until you tap **Import**. Recipes with the same name as one you already have are skipped, unless you choose to import them anyway.

Example to start from: [`web/public/mela-import-example.md`](../web/public/mela-import-example.md) (also downloadable from the import screen).

## Text format (`.md` / `.txt`)

Save the file as UTF-8. Big5 also works.

```markdown
## 三杯雞
*Three-cup chicken*
Link: https://www.youtube.com/watch?v=abc123
Note: 媽媽的做法，九層塔要最後放

### 食材
- 雞腿 — 600g
- 大蒜 — 10瓣
- 九層塔 — 一把

### 步驟
1. 雞腿切塊，用滾水汆燙後瀝乾
2. 麻油小火煸香薑片和大蒜

### 紀錄
- 2026-10-24 ★★★★★ (Mei): 收汁收得剛好
- 2026-09-12 ★★★★ (Paul): 太甜了 Tweaks: 冰糖減半
```

### Recipes
- Each recipe starts with a `## ` heading: `## Recipe name`.
- Text above the first `## ` heading is ignored, such as a `# File title`.
- If the file has no `## ` headings, each `# ` heading is a recipe. A file with no headings at all is one recipe, named after the file.

### Details (optional, between the name and the first section)

| Line | Becomes |
|---|---|
| `Link: https://…` or `連結：https://…` (or any line that's just a link) | The recipe's link. YouTube and Instagram are recognised. |
| `Note: …` / `備註：…`, a `> quoted` line, or any other plain line | The saved note |
| `*Three-cup chicken*` (in italics) or `Other name: …` | The name in the other language |
| `Plate: garland` | The plate (`scallop fluted garland stoneware petal ember greenband inkrim plain`) |

### Sections
A section starts with a `### ` heading. English or Chinese both work:

| Section | Heading |
|---|---|
| Ingredients | `### Ingredients`, `### 食材`, `### 材料` |
| Steps | `### Steps`, `### Method`, `### Directions`, `### Instructions`, `### 作法`, `### 做法`, `### 步驟` |
| Cook log | `### Cook log`, `### Log`, `### 紀錄` |

Other `### ` sections are skipped, and the preview lists them. Inside Ingredients, deeper headings like `#### Sauce` are just ignored, so you can group ingredients.

### Ingredients: one per line
- `- name — amount`. The ` — ` (em dash with spaces) separates the name from the amount exactly. ` – ` and ` | ` work too.
- Without a separator, the amount is read from the start or the end of the line, as in the recipe editor: `雞腿 300g`, `300g 雞腿`, `2 cloves garlic`, `鹽 少許`, `Salt to taste`.
- Use a separator when an ingredient's name ends in a number, or anything else unusual.
- The amount is kept exactly as written (`1瓣（拍碎）`, `1大匙 + 1小匙`).
- A line with no amount is fine, e.g. `- 香菜`.

### Steps: one per line
- A leading `1.`, `1)`, `1、`, `Step 1:` or `- ` is removed.
- Lines are never split on commas.
- A line indented with spaces continues the previous step.

### Cook log: one past cook per line

`- 2026-10-24 ★★★★ (Mei): note text Tweaks: what we changed`

- The date is required: `2026-10-24`, `2026/10/24` or `2026年10月24日`.
- Rating (optional): `★★★★`, `4/5` or `4 stars`.
- `(Mei)` (optional): who cooked it, if it matches a household member. Otherwise it's you.
- After `:` comes the note. Text after `Tweaks:` / `調整：` goes into tweaks.
- Imported recipes with a cook log count as made. Pick their plate afterwards with "Change plate".

## Mela backup (`.zip`)
Use the file from **Settings › Backup › Export recipes** as is. It restores recipes, every cook log with its photo and photo framing, plates and links. A recipe that's already in Mela (same recipe, or same name) is skipped. The grocery list isn't imported.

## JSON (`.json`)
For scripts. Either a list of recipes, or `{"recipes": [...]}`:

```json
[
  {
    "name": "三杯雞",
    "name_alt": "Three-cup chicken",
    "url": "https://www.youtube.com/watch?v=abc123",
    "note": "媽媽的做法",
    "ingredients": ["雞腿 600g", {"name": "大蒜", "portion": "10瓣"}],
    "steps": ["雞腿切塊", "麻油煸香薑片和大蒜"],
    "plate": "garland",
    "logs": [{"date": "2026-10-24", "rating": 5, "note": "收汁收得剛好", "by": "Mei"}]
  }
]
```

- Only `name` is required.
- An ingredient can be a line of text (read as in the text format) or `{"name", "portion"}`.
- `steps` can also be one string with a step per line.
- Also accepted: `title` for `name`; `link` / `source_url` for `url`; `instructions` for `steps`; `cook_log` for `logs`; `cooked_on` for `date`; `created_by` for `by`.
- The `mela-backup.json` inside an export uses this same shape, with more fields.
