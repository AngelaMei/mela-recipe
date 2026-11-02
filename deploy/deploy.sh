#!/usr/bin/env bash
# Build Mela from the current git HEAD, push the images, and roll out with Helm.
#
#   deploy/deploy.sh                 build + push + helm upgrade --install
#   deploy/deploy.sh --skip-build    redeploy images already in the registry for this commit
#   deploy/deploy.sh --tag abc123    deploy a specific tag (implies --skip-build)
#   deploy/deploy.sh --dry-run       print the rendered manifests, change nothing
#
# Settings come from deploy/deploy.env (copy deploy.env.example). Secrets come
# from deploy/secrets.env (copy secrets.env.example); they are written to the
# Kubernetes Secret "mela-secrets" and never stored in Helm.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY="$ROOT/deploy"
CHART="$DEPLOY/helm/mela"

[[ -f "$DEPLOY/deploy.env" ]] && source "$DEPLOY/deploy.env"

PROJECT="${WALLET_PROJECT:-wallet-paul-eruh3h2k}"
REGION="${WALLET_REGION:-europe-west6}"
REGISTRY="$REGION-docker.pkg.dev/$PROJECT/mela"
NAMESPACE="${NAMESPACE:-mela}"
RELEASE="${RELEASE:-mela}"
PLATFORM="${PLATFORM:-linux/amd64}"
KUBE_CONTEXT="${KUBE_CONTEXT:-}"
VALUES_FILE="${VALUES_FILE:-$DEPLOY/values.local.yaml}"
SECRET_NAME="mela-secrets"

SKIP_BUILD=0
DRY_RUN=0
TAG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build) SKIP_BUILD=1 ;;
    --tag) TAG="$2"; SKIP_BUILD=1; shift ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\033[31mError:\033[0m %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null || die "$1 is not installed"; }

need git; need helm; need kubectl
[[ $SKIP_BUILD -eq 1 ]] || need docker
[[ -n "$REGISTRY" ]] || die "Set REGISTRY in deploy/deploy.env (e.g. REGISTRY=ghcr.io/you)"

KUBECTL=(kubectl); HELM=(helm)
if [[ -n "$KUBE_CONTEXT" ]]; then
  KUBECTL+=(--context "$KUBE_CONTEXT"); HELM+=(--kube-context "$KUBE_CONTEXT")
fi

# ---------------------------------------------------------------- version
if [[ -z "$TAG" ]]; then
  TAG="$(git -C "$ROOT" rev-parse --short=12 HEAD)"
  if [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
    # The images are built from the working tree; don't let a commit tag lie about it.
    TAG="$TAG-dirty-$(date +%Y%m%d%H%M%S)"
    echo "Note: uncommitted changes are included; tagging as $TAG"
  fi
fi
API_IMAGE="$REGISTRY/mela-api:$TAG"
WEB_IMAGE="$REGISTRY/mela-web:$TAG"

VALUES=(--set "image.registry=$REGISTRY" --set "image.tag=$TAG")
[[ -f "$VALUES_FILE" ]] && VALUES+=(-f "$VALUES_FILE")

if [[ $DRY_RUN -eq 1 ]]; then
  say "Rendering $RELEASE ($TAG), nothing will change"
  "${HELM[@]}" template "$RELEASE" "$CHART" --namespace "$NAMESPACE" "${VALUES[@]}"
  exit 0
fi

CTX="$("${KUBECTL[@]}" config current-context 2>/dev/null || echo '?')"
echo "Deploying $TAG to context '$CTX', namespace '$NAMESPACE'"

# ---------------------------------------------------------------- build + push
if [[ $SKIP_BUILD -eq 0 ]]; then
  say "Building and pushing $API_IMAGE and $WEB_IMAGE"
  # Both images in parallel, from docker-bake.hcl
  (cd "$ROOT" && REGISTRY="$REGISTRY" TAG="$TAG" PLATFORM="$PLATFORM" \
    docker buildx bake --file docker-bake.hcl --push)
fi

# ---------------------------------------------------------------- namespace + secret
"${KUBECTL[@]}" get namespace "$NAMESPACE" >/dev/null 2>&1 || "${KUBECTL[@]}" create namespace "$NAMESPACE"

if [[ -f "$DEPLOY/secrets.env" ]]; then
  say "Updating Secret $SECRET_NAME from deploy/secrets.env"
  for key in POSTGRES_PASSWORD MELA_PASSCODE SESSION_SECRET; do
    grep -qE "^$key=.+" "$DEPLOY/secrets.env" || die "deploy/secrets.env: $key is empty"
  done
  "${KUBECTL[@]}" -n "$NAMESPACE" create secret generic "$SECRET_NAME" \
    --from-env-file="$DEPLOY/secrets.env" --dry-run=client -o yaml | "${KUBECTL[@]}" apply -f - >/dev/null
elif ! "${KUBECTL[@]}" -n "$NAMESPACE" get secret "$SECRET_NAME" >/dev/null 2>&1; then
  die "No Secret '$SECRET_NAME' in '$NAMESPACE' yet. Copy deploy/secrets.env.example to deploy/secrets.env and fill it in."
fi

# ---------------------------------------------------------------- adopt an earlier kubectl/kustomize install
# Resources applied by hand aren't owned by Helm, and Helm refuses to touch them.
# Hand them over (same names and selectors, so Postgres keeps its volume and data).
if ! "${HELM[@]}" -n "$NAMESPACE" status "$RELEASE" >/dev/null 2>&1; then
  for res in configmap/mela-config service/mela-postgres statefulset/mela-postgres \
             service/mela-api deployment/mela-api service/mela-web deployment/mela-web \
             ingress/mela networkpolicy/mela-postgres pvc/mela-backups cronjob/mela-backup; do
    if "${KUBECTL[@]}" -n "$NAMESPACE" get "$res" >/dev/null 2>&1; then
      echo "Handing $res over to Helm"
      "${KUBECTL[@]}" -n "$NAMESPACE" label "$res" app.kubernetes.io/managed-by=Helm --overwrite >/dev/null
      "${KUBECTL[@]}" -n "$NAMESPACE" annotate "$res" meta.helm.sh/release-name="$RELEASE" \
        meta.helm.sh/release-namespace="$NAMESPACE" --overwrite >/dev/null
    fi
  done
fi

# ---------------------------------------------------------------- roll out
say "Rolling out $RELEASE ($TAG)"
"${HELM[@]}" upgrade --install "$RELEASE" "$CHART" --namespace "$NAMESPACE" "${VALUES[@]}" --wait --timeout 10m

say "Done"
"${KUBECTL[@]}" -n "$NAMESPACE" get pods -o wide
HOST="$("${KUBECTL[@]}" -n "$NAMESPACE" get ingress mela -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || true)"
[[ -n "$HOST" ]] && echo "Open https://$HOST"
