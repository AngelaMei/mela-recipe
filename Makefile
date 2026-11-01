# Build, push and deploy Mela to the `mela` namespace.
#
#   make images REGISTRY=registry.example.com/mela TAG=0.1.0
#   make deploy REGISTRY=registry.example.com/mela TAG=0.1.0
#
# `deploy` applies deploy/k8s/overlays/prod with your images swapped in, so the
# overlay's placeholder registry never needs editing. Needs docker + kubectl.

REGISTRY ?= registry.example.com/mela
TAG ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)
PLATFORM ?= linux/amd64
OVERLAY := deploy/k8s/overlays/prod

.PHONY: test images deploy render status logs psql backup-now dev

test:
	cd backend && python -m pytest -q
	cd web && npm run typecheck

images:
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/mela-api:$(TAG) --push backend
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/mela-web:$(TAG) --push web

.build/k8s/kustomization.yaml: FORCE
	@test -f $(OVERLAY)/secrets.env || (echo "Missing $(OVERLAY)/secrets.env — copy secrets.env.example and fill it in" && exit 1)
	@mkdir -p .build/k8s
	@printf '%s\n' \
	  'apiVersion: kustomize.config.k8s.io/v1beta1' \
	  'kind: Kustomization' \
	  'resources:' \
	  '  - ../../$(OVERLAY)' \
	  'images:' \
	  '  - name: registry.example.com/mela/mela-api' \
	  '    newName: $(REGISTRY)/mela-api' \
	  '    newTag: "$(TAG)"' \
	  '  - name: registry.example.com/mela/mela-web' \
	  '    newName: $(REGISTRY)/mela-web' \
	  '    newTag: "$(TAG)"' > $@
FORCE:

render: .build/k8s/kustomization.yaml
	kubectl kustomize .build/k8s

deploy: .build/k8s/kustomization.yaml
	kubectl apply -k .build/k8s
	kubectl -n mela rollout status statefulset/mela-postgres --timeout=180s
	kubectl -n mela rollout status deployment/mela-api --timeout=180s
	kubectl -n mela rollout status deployment/mela-web --timeout=180s

status:
	kubectl -n mela get pods,svc,ingress,pvc

logs:
	kubectl -n mela logs deploy/mela-api --all-containers --tail=100

psql:
	kubectl -n mela exec -it statefulset/mela-postgres -- sh -c 'psql -U "$$POSTGRES_USER" "$$POSTGRES_DB"'

backup-now:
	kubectl -n mela create job --from=cronjob/mela-backup mela-backup-manual-$$(date +%s)

dev:
	docker compose up --build
