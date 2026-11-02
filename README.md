# Mela

A private recipe and grocery app for one household (Mei & Paul): save recipes from a YouTube link, an Instagram post or plain text, see what we've cooked as plates, search by ingredient, keep a cook log and share one grocery list.

The design spec is in [`docs/design.md`](docs/design.md).

```
web/       Next.js 15 (App Router) PWA, plain CSS with design tokens
backend/   FastAPI + SQLAlchemy + Alembic. Parsing, grocery merging and search live here
deploy/    Kubernetes manifests (kustomize) for the `mela` namespace
```

## Architecture

```
                 Ingress (mela.example.com)
                 ├── /api/*  → mela-api  (FastAPI, :8000) ──→ mela-postgres (StatefulSet, PVC 5Gi)
                 └── /*      → mela-web  (Next.js standalone, :3000)
namespace: mela  CronJob mela-backup: nightly pg_dump to its own PVC, 14 days kept
```

- **Same origin.** The browser only talks to one host, so the session cookie needs no CORS setup. If you'd rather not split paths at the Ingress, the web container also proxies `/api` to `http://mela-api:8000`.
- **Adding a recipe is structured, not guessed.** Ingredients and steps each have two ways in, switchable at any time without losing anything:
  - *Type a list*: a big box, one ingredient (or step) per line. Each ingredient line is split into **name + amount** by `POST /api/parse/lines` (`backend/app/services/lines.py`) and previewed live, so you see the split before saving. Steps are one per line, never split on commas, and a leading `1.` is removed.
  - *One by one*: a row per item with a separate name and amount field and an "Add ingredient" / "Add step" button. Nothing is guessed.

  The amount is stored **exactly as typed** (`300g`, `1瓣（拍碎）`, `少許`) and shown that way. The server also reads a number and unit from it (`1大匙 + 1小匙` → 4 tsp) only so the grocery list can merge amounts. The same editor edits existing recipes (`/recipes/[id]/edit`).
- **Imports.** A YouTube link offers "Import from the video description", which fills the boxes for review using the older free-text heuristics in `parsing.py`. Grocery keys, aliases, units and search are in `normalize.py` / `search.py`, all unit-tested in Python.
- **Sync between the two phones.** Postgres is the source of truth. The grocery list polls every 4s while open; other screens revalidate on focus. Concurrent adds of the same ingredient are serialised with a Postgres advisory lock, so they merge instead of duplicating.
- **Auth.** Pick who you are, then enter a shared kitchen passcode. This sets a signed, HTTP-only cookie that lasts a year. Members are configured in `MELA_MEMBERS`, and the names drive "Added by Paul" and "shared with Paul".
- **Photos.** Resized on the phone to at most 1280px JPEG, then stored in Postgres (`photos` table). That keeps it to one stateful component to back up.
- **YouTube.** The server reads the description with YouTube Data API `videos.list?part=snippet` (set `YOUTUBE_API_KEY`). Only ingredients and steps are imported. Without a key, the Add screen falls back to "paste what you need".
- **Instagram.** Captions aren't fetched. The Add screen shows a Caption field, and if it's left empty the recipe is saved as link-only.

## Deploy to your cluster

Prerequisites: `kubectl` pointed at the cluster, a container registry the cluster can pull from, and an ingress controller. The manifests assume `ingressClassName: nginx` and cert-manager with a `letsencrypt` ClusterIssuer; change those in the overlay if yours differ.

1. **Secrets.** Copy `deploy/k8s/overlays/prod/secrets.env.example` to `secrets.env` (git-ignored) and fill it in:
   ```bash
   cp deploy/k8s/overlays/prod/secrets.env.example deploy/k8s/overlays/prod/secrets.env
   ```
   ```bash
   openssl rand -base64 32   # use for POSTGRES_PASSWORD and SESSION_SECRET
   ```
2. **Hostname.** In `deploy/k8s/overlays/prod/kustomization.yaml`, replace `mela.example.com` (twice) and the cert-manager issuer.
3. **Household.** Names live in `deploy/k8s/base/config.yaml` (`MELA_HOUSEHOLD`, `MELA_HOUSEHOLD_ZH`, `MELA_MEMBERS`).
4. **Build, push and deploy:**
   ```bash
   make images REGISTRY=<your-registry>/mela TAG=0.1.0
   ```
   ```bash
   make deploy REGISTRY=<your-registry>/mela TAG=0.1.0
   ```
   `make deploy` applies the prod overlay with your image names swapped in, then waits for Postgres, the API and the web app. The API pod's `migrate` init container waits for Postgres and runs `alembic upgrade head` on every rollout.

If your registry is private, add an `imagePullSecret` to the two Deployments, or attach it to the `default` ServiceAccount in `mela`.

Day-two commands: `make status`, `make logs`, `make psql`, `make backup-now`. To restore a backup:

```bash
kubectl -n mela exec -i statefulset/mela-postgres -- sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < <(gunzip -c mela-YYYYMMDD-HHMM.sql.gz)
```

The backups sit on a PVC in the same cluster. Copy them off-cluster too if your volumes aren't backed up.

## Local development

With Docker:

```bash
docker compose up --build
```

Then open http://localhost:3000. The passcode is `1234`.

Without Docker (Postgres running locally):

```bash
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
```
```bash
cp .env.example .env && alembic upgrade head && uvicorn app.main:app --reload --port 8000
```
```bash
cd web && npm install && API_INTERNAL_URL=http://localhost:8000 npm run dev
```

Tests:

```bash
cd backend && python -m pytest -q
```
```bash
cd backend && TEST_DATABASE_URL=postgresql+psycopg://mela:mela@localhost:5432/mela_test python -m pytest -q
```

The first command uses SQLite; the second runs against Postgres.

API docs are at `/api/docs`.

## Frontend notes

- Tokens: `web/styles/tokens/*.css`, imported once via `web/styles.css`. Components use the semantic tokens (`--bg-app`, `--surface-card`, `--text-secondary`, ...) and never raw hex values. Dark mode is `[data-theme="dark"]` on `<html>`.
- Components: `web/components/{core,forms,navigation,recipe,overlays}`, with the same names as the design (Icon, Button, IconButton, Badge, Chip, TextField, Checkbox, SegmentedControl, BottomNav, Tabs, TopBar, Plate, RecipeTile, IngredientRow, StepRow, GroceryItem, LogEntry, SearchResult, Sheet).
- Copy: every string, in English and 繁體中文, is in `web/lib/i18n.ts`. The language and theme are stored per device in localStorage.
- Plates: nine drawn plates (white scallop, fluted, rose garland, sage stoneware, grey petal, ember glaze, green band, ink rim, everyday white), each paired with its own tablecloth on the recipe page and in the plate picker. Defined in `web/lib/plates.ts`, drawn as SVG in `components/recipe/Plate.tsx`; see them all at `/plates`. Details and how to swap in photographed plates: `web/public/plates/README.md`.
- Things the design hadn't drawn, and how they're built here: the log form (date, rating, note, tweaks, photo; tap a log to edit or delete it), the login screen, the recipe editor (replaces the single "paste anything" field from the design), and "Edit recipe" / "Delete recipe" on the detail page. Extra icons used: `edit`, `close`.
