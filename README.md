# Mela

A private recipe and grocery app for one household (Mei & Paul): save recipes from a YouTube link, an Instagram post or plain text, see what we've cooked as plates, search by ingredient, keep a cook log and share one grocery list.

The design spec is in [`docs/design.md`](docs/design.md).

```
web/       Next.js 15 (App Router) PWA, plain CSS with design tokens
backend/   FastAPI + SQLAlchemy + Alembic. Parsing, grocery merging and search live here
deploy/    Helm chart and deploy script for the `mela` namespace
```

## Architecture

```
                 Traefik Ingress (mela.meiyuchi.com)
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

Mela is deployed with the Helm chart in `deploy/helm/mela`, through `deploy/deploy.sh`.

```
                 Traefik Ingress  https://mela.meiyuchi.com   (cert-manager, ClusterIssuer "letsencrypt")
                 ├── /api/*  → mela-api  (FastAPI :8000, migrate init container) ──→ mela-postgres (StatefulSet, 5Gi PVC)
                 └── /*      → mela-web  (Next.js :3000)
namespace: mela  CronJob mela-backup: nightly pg_dump to its own PVC, 14 days kept
```

You need `git`, `docker` (with buildx), `kubectl` pointed at the cluster, `helm` 3, and a registry the cluster can pull from.

**One-time setup**

1. Registry: copy `deploy/deploy.env.example` to `deploy/deploy.env` and set `REGISTRY`, e.g. `ghcr.io/meiyuchi`. Run `docker login` for that registry.
   ```bash
   cp deploy/deploy.env.example deploy/deploy.env
   ```
2. Secrets: copy `deploy/secrets.env.example` to `deploy/secrets.env` and fill it in. The script writes it to the Kubernetes Secret `mela-secrets`; Helm never sees it.
   ```bash
   cp deploy/secrets.env.example deploy/secrets.env
   ```
   ```bash
   openssl rand -base64 32   # for POSTGRES_PASSWORD and SESSION_SECRET
   ```
3. Check the cert-manager issuer name matches `ingress.clusterIssuer` (default `letsencrypt`):
   ```bash
   kubectl get clusterissuer
   ```
   If yours is named differently, or you want other household names or a storage class, copy `deploy/values.local.yaml.example` to `deploy/values.local.yaml` and override them there.
4. Point DNS for `mela.meiyuchi.com` at Traefik's address.

**Deploy**

```bash
deploy/deploy.sh
```

This builds `mela-api` and `mela-web` with `docker buildx bake` (targets in `docker-bake.hcl`, both in parallel) from the current git `HEAD` (tagged with the short commit hash, plus `-dirty-<time>` if there are uncommitted changes), pushes them, updates the Secret, runs `helm upgrade --install`, then waits for Postgres, the API and the web app to finish rolling out (`kubectl rollout status`). It doesn't use `helm --wait`, because that also waits for the backup volume, which a `WaitForFirstConsumer` StorageClass (the GKE default) only creates when the nightly backup first runs. The API's `migrate` init container applies database migrations on every rollout.

Other options:

```bash
deploy/deploy.sh --skip-build   # images for this commit are already pushed
```
```bash
deploy/deploy.sh --tag 1a2b3c4d5e6f   # roll out (or roll back to) a specific build
```
```bash
deploy/deploy.sh --dry-run   # print the rendered manifests, change nothing
```

Rolling back also works with Helm's own history (`helm -n mela history mela`, then `helm -n mela rollback mela <revision>`).

If the cluster nodes are ARM, set `PLATFORM=linux/arm64` in `deploy/deploy.env`. If the registry is private, create a pull secret in `mela` and list it under `imagePullSecrets` in `values.local.yaml`.

*From the earlier kubectl/kustomize manifests:* the first `deploy.sh` run hands the existing resources over to Helm. Names and selectors are unchanged, so Postgres keeps its volume and data. The old hashed `mela-secrets-xxxxx` Secret can be deleted afterwards.

**Day to day**

```bash
kubectl -n mela get pods,svc,ingress,certificate,pvc     # status
```
```bash
kubectl -n mela logs deploy/mela-api --all-containers --tail=100     # API logs
```
```bash
kubectl -n mela exec -it statefulset/mela-postgres -- sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'     # database shell
```
```bash
kubectl -n mela create job --from=cronjob/mela-backup mela-backup-manual-$(date +%s)     # backup now
```

To restore a nightly backup:

```bash
kubectl -n mela exec -i statefulset/mela-postgres -- sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < <(gunzip -c mela-YYYYMMDD-HHMM.sql.gz)
```

The nightly backups sit on a PVC in the same cluster, so copy them off-cluster too if your volumes aren't backed up. Settings › Backup in the app also downloads everything (recipes, cook logs, photos) as a .zip.

**Importing recipes.** *Settings › Backup › Import recipes* takes a Mela backup `.zip`, recipes written as text (`.md` / `.txt`), or JSON, and shows a preview before anything is saved. The file format is in [`docs/import-format.md`](docs/import-format.md); there's an example at [`web/public/mela-import-example.md`](web/public/mela-import-example.md).

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
